import json
import logging
import datetime
import pytest
from io import StringIO
from typing import Dict, Any
from src.utils.logging import (
    LogFormatter,
    BatchedEventLogger,
    setup_logging,
    PRODUCTION_EXCLUDE_PATTERNS,
    LogLevel
)
import sys

class TestLogFormatter:
    @pytest.fixture
    def json_formatter(self):
        return LogFormatter(use_json=True)
    
    @pytest.fixture
    def compact_formatter(self):
        return LogFormatter(use_json=False)
    
    def test_json_format_basic_log(self, json_formatter):
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = json_formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
    
    def test_json_format_with_extra_fields(self, json_formatter):
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.event_type = "test_event"
        record.event_data = {"key": "value"}
        
        formatted = json_formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["event_type"] == "test_event"
        assert parsed["data"] == {"key": "value"}
    
    def test_json_format_with_error(self, json_formatter):
        try:
            raise ValueError("Test error")
        except ValueError as e:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info()
            )
            
            formatted = json_formatter.format(record)
            parsed = json.loads(formatted)
            
            assert parsed["error"]["type"] == "ValueError"
            assert parsed["error"]["message"] == "Test error"
            assert "stack_trace" in parsed["error"]
    
    def test_compact_format_basic_log(self, compact_formatter):
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = compact_formatter.format(record)
        assert "] I: Test message" in formatted
    
    def test_compact_format_with_error(self, compact_formatter):
        try:
            raise ValueError("Test error")
        except ValueError as e:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info()
            )
            
            formatted = compact_formatter.format(record)
            assert "] E: Error occurred" in formatted
            assert "ValueError: Test error" in formatted

class TestBatchedEventLogger:
    @pytest.fixture
    def string_io(self):
        return StringIO()
    
    @pytest.fixture
    def logger(self, string_io):
        handler = logging.StreamHandler(string_io)
        handler.setFormatter(LogFormatter(use_json=True))
        logger = logging.getLogger("test_batched")
        logger.handlers = [handler]
        logger.setLevel(logging.INFO)
        return logger
    
    @pytest.fixture
    def batched_logger(self, logger):
        return BatchedEventLogger(logger)
    
    def test_batch_single_event(self, batched_logger, string_io):
        event_data = {"action": "click", "element": "button"}
        batched_logger.add_event("ui_action", event_data)
        batched_logger.flush()
        
        output = string_io.getvalue()
        parsed = json.loads(output)
        
        assert parsed["event_type"] == "batched_ui_action"
        assert parsed["data"]["count"] == 1
        assert parsed["data"]["events"][0] == event_data
    
    def test_batch_multiple_events(self, batched_logger, string_io):
        events = [
            {"action": "click", "element": "button1"},
            {"action": "type", "element": "input1"},
            {"action": "click", "element": "button2"}
        ]
        
        for event in events:
            batched_logger.add_event("ui_action", event)
        
        batched_logger.flush()
        
        output = string_io.getvalue()
        parsed = json.loads(output)
        
        assert parsed["event_type"] == "batched_ui_action"
        assert parsed["data"]["count"] == 3
        assert parsed["data"]["events"] == events

class TestLoggingSetup:
    @pytest.fixture
    def temp_logger(self):
        # Store original handlers
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers[:]
        
        yield root_logger
        
        # Restore original handlers
        root_logger.handlers = original_handlers
    
    def test_setup_basic_logging(self, temp_logger):
        setup_logging(level="INFO", use_json=True)
        assert len(temp_logger.handlers) == 1
        assert isinstance(temp_logger.handlers[0].formatter, LogFormatter)
        assert temp_logger.level == logging.INFO
    
    def test_setup_with_exclude_patterns(self, temp_logger):
        test_patterns = ["debug", "deprecated"]
        setup_logging(level="INFO", exclude_patterns=test_patterns)
        
        # Create a test record that should be filtered
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="This is a debug message",
            args=(),
            exc_info=None
        )
        
        # The record should be filtered out
        assert not temp_logger.handlers[0].filter(record)
    
    def test_production_exclude_patterns(self):
        # Verify that all production patterns are strings
        assert all(isinstance(pattern, str) for pattern in PRODUCTION_EXCLUDE_PATTERNS)
        
        # Verify that common patterns are included
        common_patterns = ["deprecated", "virtual environment"]
        assert all(pattern in PRODUCTION_EXCLUDE_PATTERNS for pattern in common_patterns)

def test_log_levels():
    # Test that all expected log levels are defined
    expected_levels = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "TRACE"]
    assert all(level in LogLevel.__members__ for level in expected_levels)
    
    # Test that the values match the names
    for level in LogLevel:
        assert level.value == level.name 