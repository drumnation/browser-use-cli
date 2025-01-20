import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import re

class MaxRetriesExceededError(Exception):
    def __init__(self, operation: str, original_error: Exception):
        self.operation = operation
        self.original_error = original_error
        super().__init__(f"Max retries exceeded for operation '{operation}': {str(original_error)}")

class ErrorHandler:
    MAX_RETRIES = 3

    def __init__(self):
        self._retry_counts: Dict[str, int] = {}
        self._last_error: Optional[Dict[str, Any]] = None

    async def handle_error(self, error: Exception, operation: str) -> None:
        retry_count = self._retry_counts.get(operation, 0)
        
        if retry_count >= self.MAX_RETRIES:
            raise MaxRetriesExceededError(operation, error)
        
        self._retry_counts[operation] = retry_count + 1
        await self._log_error(error, operation, retry_count)
        
        # Exponential backoff: 2^retry_count seconds
        await asyncio.sleep(2 ** retry_count)

    async def _log_error(self, error: Exception, operation: str, retry_count: int) -> None:
        error_context = {
            "operation": operation,
            "attempt": retry_count + 1,
            "timestamp": datetime.now().isoformat(),
            "error": {
                "name": error.__class__.__name__,
                "message": str(error),
                "code": self.extract_error_code(error)
            }
        }
        
        self._last_error = error_context
        # In a real implementation, we would log to a file or logging service
        print(f"Error: {error_context}")

    def extract_error_code(self, error: Exception) -> str:
        error_message = str(error)
        match = re.search(r'ERR_[A-Z_]+', error_message)
        return match.group(0) if match else "UNKNOWN_ERROR"

    def get_last_error(self) -> Optional[Dict[str, Any]]:
        return self._last_error 