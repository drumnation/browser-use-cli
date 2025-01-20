import pytest
import json
import logging
import os
from datetime import datetime
from src.utils.structured_logging import (
    StructuredLogger,
    ProgressEvent,
    BrowserEvent,
    JSONFormatter,
    ColorizedFormatter,
    ColorScheme,
    setup_structured_logging
)
from colorama import Fore, Style

@pytest.fixture
def structured_logger():
    logger = StructuredLogger("test_logger")
    return logger

def test_progress_event_creation():
    event = ProgressEvent(
        step="test_step",
        status="in_progress",
        progress=0.5,
        message="Testing progress"
    )
    assert event.step == "test_step"
    assert event.status == "in_progress"
    assert event.progress == 0.5
    assert event.message == "Testing progress"
    assert event.timestamp is not None

def test_browser_event_creation():
    details = {"action": "click", "selector": "#button"}
    event = BrowserEvent(
        event_type="interaction",
        details=details
    )
    assert event.event_type == "interaction"
    assert event.details == details
    assert event.timestamp is not None

def test_progress_logging(structured_logger):
    structured_logger.log_progress(
        step="test_step",
        status="started",
        progress=0.0,
        message="Starting test"
    )
    
    history = structured_logger.get_progress_history()
    assert len(history) == 1
    assert history[0]["step"] == "test_step"
    assert history[0]["status"] == "started"
    assert history[0]["progress"] == 0.0
    assert history[0]["message"] == "Starting test"

def test_browser_event_logging(structured_logger):
    details = {"page": "test.html", "action": "navigate"}
    structured_logger.log_browser_event(
        event_type="navigation",
        details=details
    )
    
    events = structured_logger.get_browser_events()
    assert len(events) == 1
    assert events[0]["event_type"] == "navigation"
    assert events[0]["details"] == details

def test_progress_tracking(structured_logger):
    # Test multiple progress updates
    steps = [
        ("step1", "started", 0.0, "Starting"),
        ("step1", "in_progress", 0.5, "Halfway"),
        ("step1", "completed", 1.0, "Done")
    ]
    
    for step, status, progress, message in steps:
        structured_logger.log_progress(step, status, progress, message)
    
    assert structured_logger.get_current_progress() == 1.0
    history = structured_logger.get_progress_history()
    assert len(history) == 3
    
    for i, (step, status, progress, message) in enumerate(steps):
        assert history[i]["step"] == step
        assert history[i]["status"] == status
        assert history[i]["progress"] == progress
        assert history[i]["message"] == message

def test_clear_history(structured_logger):
    # Add some events
    structured_logger.log_progress("test", "started", 0.5, "Test progress")
    structured_logger.log_browser_event("test", {"action": "test"})
    
    # Clear history
    structured_logger.clear_history()
    
    assert len(structured_logger.get_progress_history()) == 0
    assert len(structured_logger.get_browser_events()) == 0
    assert structured_logger.get_current_progress() == 0.0

def test_json_formatter():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    # Add custom fields
    setattr(record, 'event_type', 'test_event')
    setattr(record, 'data', {'test_key': 'test_value'})
    
    formatted = formatter.format(record)
    parsed = json.loads(formatted)
    
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message"
    assert parsed["logger"] == "test_logger"
    assert parsed["event_type"] == "test_event"
    assert parsed["data"] == {"test_key": "test_value"}
    assert "timestamp" in parsed

def test_colorized_formatter_with_colors():
    formatter = ColorizedFormatter(use_colors=True)
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="Test error message",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    assert Fore.RED in formatted  # Error level should be red
    assert Style.RESET_ALL in formatted  # Should have reset codes
    assert "[" in formatted and "]" in formatted  # Should have timestamp brackets
    assert "ERROR" in formatted  # Should include level name

def test_colorized_formatter_without_colors():
    formatter = ColorizedFormatter(use_colors=False)
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    assert Fore.CYAN not in formatted  # Should not have color codes
    assert Style.RESET_ALL not in formatted
    assert "[" in formatted and "]" in formatted
    assert "INFO" in formatted

def test_colorized_formatter_special_keywords():
    formatter = ColorizedFormatter(use_colors=True)
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="✓ STEP(1) completed × failed",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    assert Fore.GREEN in formatted  # Success checkmark
    assert Fore.BLUE in formatted   # STEP keyword
    assert Fore.RED in formatted    # Error cross

def test_colorized_formatter_with_structured_data():
    formatter = ColorizedFormatter(use_colors=True)
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Progress Update",
        args=(),
        exc_info=None
    )
    
    # Add structured data
    setattr(record, 'event_type', 'progress')
    setattr(record, 'data', {'step': 'test', 'progress': 0.5})
    
    formatted = formatter.format(record)
    assert 'progress' in formatted
    assert '"step": "test"' in formatted
    assert '"progress": 0.5' in formatted

def test_color_scheme():
    scheme = ColorScheme()
    assert scheme.ERROR == Fore.RED
    assert scheme.WARNING == Fore.YELLOW
    assert scheme.INFO == Fore.CYAN
    assert scheme.DEBUG == Style.DIM
    assert scheme.SUCCESS == Fore.GREEN
    assert scheme.RESET == Style.RESET_ALL

def test_no_color_environment_variable():
    os.environ['NO_COLOR'] = '1'
    formatter = ColorizedFormatter(use_colors=True)  # Even with colors enabled
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    assert Fore.RED not in formatted  # Should not have color codes
    assert Style.RESET_ALL not in formatted
    
    # Clean up
    del os.environ['NO_COLOR']

def test_setup_structured_logging_with_colors():
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set up logging with colors
    setup_structured_logging(level=logging.DEBUG, use_colors=True, json_output=False)
    
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0].formatter, ColorizedFormatter)
    assert root_logger.handlers[0].formatter.use_colors is True

def test_setup_structured_logging_json():
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set up logging with JSON output
    setup_structured_logging(level=logging.DEBUG, json_output=True)
    
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0].formatter, JSONFormatter)

def test_setup_structured_logging():
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set up logging with default settings
    setup_structured_logging(level=logging.DEBUG)
    
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0].formatter, ColorizedFormatter)  # Default to ColorizedFormatter 