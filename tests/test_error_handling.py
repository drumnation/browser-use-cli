import pytest
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio
from src.utils.error_handling import ErrorHandler, MaxRetriesExceededError

class TestErrorHandler:
    @pytest.fixture
    def handler(self):
        return ErrorHandler()

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, handler):
        operation = "test_operation"
        error = ValueError("Test error")

        # Should handle first three attempts
        for _ in range(3):
            await handler.handle_error(error, operation)

        # Fourth attempt should raise MaxRetriesExceededError
        with pytest.raises(MaxRetriesExceededError) as exc_info:
            await handler.handle_error(error, operation)

        assert exc_info.value.operation == operation
        assert exc_info.value.original_error == error

    @pytest.mark.asyncio
    async def test_error_logging(self, handler):
        operation = "test_operation"
        error = ValueError("Test error")
        
        # First attempt
        await handler.handle_error(error, operation)
        
        # Get the last logged error
        last_error = handler.get_last_error()
        assert last_error["operation"] == operation
        assert last_error["attempt"] == 1
        assert "timestamp" in last_error
        assert last_error["error"]["name"] == "ValueError"
        assert last_error["error"]["message"] == "Test error"

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, handler):
        operation = "test_operation"
        error = ValueError("Test error")
        
        # Record start time
        start = datetime.now()
        
        # First attempt (should delay 1 second)
        await handler.handle_error(error, operation)
        
        # Second attempt (should delay 2 seconds)
        await handler.handle_error(error, operation)
        
        # Calculate duration
        duration = (datetime.now() - start).total_seconds()
        
        # Should have waited at least 3 seconds (1 + 2)
        assert duration >= 3

    @pytest.mark.asyncio
    async def test_error_code_extraction(self, handler):
        # Test with connection error
        error = ConnectionError("ERR_CONNECTION_REFUSED: Failed to connect")
        code = handler.extract_error_code(error)
        assert code == "ERR_CONNECTION_REFUSED"

        # Test with DNS error
        error = Exception("ERR_NAME_NOT_RESOLVED: Could not resolve hostname")
        code = handler.extract_error_code(error)
        assert code == "ERR_NAME_NOT_RESOLVED"

        # Test with unknown error
        error = ValueError("Some other error")
        code = handler.extract_error_code(error)
        assert code == "UNKNOWN_ERROR"

    @pytest.mark.asyncio
    async def test_concurrent_retries(self, handler):
        operation = "test_operation"
        error = ValueError("Test error")
        
        # Try to handle the same error concurrently
        tasks = [
            handler.handle_error(error, operation),
            handler.handle_error(error, operation),
            handler.handle_error(error, operation)
        ]
        
        # Should complete without raising an error
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Fourth attempt should still raise MaxRetriesExceededError
        with pytest.raises(MaxRetriesExceededError):
            await handler.handle_error(error, operation) 