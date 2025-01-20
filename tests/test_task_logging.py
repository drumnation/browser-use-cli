import pytest
from datetime import datetime, timedelta
import json
import asyncio
import os
from src.utils.task_logging import (
    TaskLogger,
    TaskContext,
    StepInfo,
    BrowserState,
    TaskStatus,
    PerformanceMetrics,
    ErrorInfo,
    ActionType,
    RetryConfig,
    RetryInfo,
    ColorScheme,
    LogFormatter,
    SeparatorStyle
)

def test_task_logger_initialization():
    logger = TaskLogger("test_task", "Test task goal")
    context = logger.get_context()
    
    assert context["task"]["id"] == "test_task"
    assert context["task"]["goal"] == "Test task goal"
    assert context["task"]["status"] == "pending"
    assert context["browser"]["url"] == ""
    assert context["browser"]["state"] == "loading"
    assert context["browser"]["visible_elements"] == 0
    assert context["browser"]["dynamic_content"] == "loading"

def test_step_update():
    logger = TaskLogger("test_task", "Test task goal")
    
    # Update to running state
    logger.update_step("Starting navigation", TaskStatus.RUNNING)
    context = logger.get_context()
    
    assert context["task"]["status"] == "running"
    assert context["task"]["progress"] == "2/unknown steps"  # Step number incremented
    
    # Update to complete state
    logger.update_step("Navigation complete", TaskStatus.COMPLETE)
    context = logger.get_context()
    
    assert context["task"]["status"] == "complete"
    assert context["task"]["progress"] == "3/unknown steps"

def test_browser_state_update():
    logger = TaskLogger("test_task", "Test task goal")
    
    # Update browser state
    logger.update_browser_state(
        url="https://example.com",
        page_ready=True,
        dynamic_content_loaded=True,
        visible_elements=10
    )
    
    context = logger.get_context()
    assert context["browser"]["url"] == "https://example.com"
    assert context["browser"]["state"] == "ready"
    assert context["browser"]["dynamic_content"] == "loaded"
    assert context["browser"]["visible_elements"] == 10

def test_partial_browser_state_update():
    logger = TaskLogger("test_task", "Test task goal")
    
    # Update only some fields
    logger.update_browser_state(url="https://example.com")
    context = logger.get_context()
    
    assert context["browser"]["url"] == "https://example.com"
    assert context["browser"]["state"] == "loading"  # Unchanged
    assert context["browser"]["dynamic_content"] == "loading"  # Unchanged
    assert context["browser"]["visible_elements"] == 0  # Unchanged

def test_elapsed_time_calculation():
    logger = TaskLogger("test_task", "Test task goal")
    
    # Set a specific start time
    start_time = datetime.utcnow() - timedelta(seconds=5)
    logger.context.started_at = start_time.isoformat()
    
    context = logger.get_context()
    elapsed_time = float(context["task"]["elapsed_time"].rstrip("s"))
    
    assert 4.5 <= elapsed_time <= 5.5  # Allow for small timing variations

def test_task_status_validation():
    logger = TaskLogger("test_task", "Test task goal")
    
    # Test all valid status values
    for status in TaskStatus:
        logger.update_step(f"Step with status {status}", status)
        context = logger.get_context()
        assert context["task"]["status"] == status.value

def test_json_serialization():
    logger = TaskLogger("test_task", "Test task goal")
    context = logger.get_context()
    
    # Verify that the context can be JSON serialized
    json_str = json.dumps(context)
    parsed = json.loads(json_str)
    
    assert parsed["task"]["id"] == "test_task"
    assert parsed["task"]["goal"] == "Test task goal"
    assert "timestamp" in parsed
    assert "elapsed_time" in parsed["task"]

def test_step_info_status_conversion():
    # Test that string status values are converted to TaskStatus enum
    step = StepInfo(
        number=1,
        description="Test step",
        started_at=datetime.utcnow().isoformat(),
        status="running"  # Pass as string
    )
    
    assert isinstance(step.status, TaskStatus)
    assert step.status == TaskStatus.RUNNING

def test_error_handling():
    logger = TaskLogger("error_task", "Test error handling")
    
    # Simulate an error
    error = ValueError("Test error")
    logger.log_error(error, step_number=1, action="test action")
    
    context = logger.get_context()
    assert context["task"]["status"] == "failed"
    assert context["error"]["message"] == "Test error"
    assert context["error"]["type"] == "ValueError"
    assert context["error"]["step"] == 1
    assert context["error"]["action"] == "test action"

def test_performance_metrics():
    logger = TaskLogger("perf_task", "Test performance tracking")
    
    # Start tracking performance
    logger.start_performance_tracking()
    
    # Simulate some steps with timing
    logger.update_step("Navigation", TaskStatus.RUNNING)
    logger.track_step_duration("navigation", 0.5)
    
    logger.update_step("Interaction", TaskStatus.RUNNING)
    logger.track_step_duration("interaction", 0.3)
    
    # Get performance metrics
    metrics = logger.get_performance_metrics()
    assert metrics["step_breakdown"]["navigation"] == pytest.approx(0.5)
    assert metrics["step_breakdown"]["interaction"] == pytest.approx(0.3)
    assert metrics["total_duration"] > 0

def test_detailed_browser_state():
    logger = TaskLogger("browser_task", "Test browser state")
    
    # Update with detailed browser state
    logger.update_browser_state(
        url="https://example.com",
        page_ready=True,
        dynamic_content_loaded=True,
        visible_elements=10,
        current_frame="main",
        active_element="search_input",
        page_title="Example Page"
    )
    
    context = logger.get_context()
    browser_state = context["browser"]
    assert browser_state["url"] == "https://example.com"
    assert browser_state["state"] == "ready"
    assert browser_state["current_frame"] == "main"
    assert browser_state["active_element"] == "search_input"
    assert browser_state["page_title"] == "Example Page"

def test_task_progress_tracking():
    logger = TaskLogger("progress_task", "Test progress tracking")
    
    # Add steps with progress information
    logger.update_step("Step 1", TaskStatus.COMPLETE, progress=0.25)
    context = logger.get_context()
    assert context["task"]["progress"] == "25%"
    
    logger.update_step("Step 2", TaskStatus.COMPLETE, progress=0.5)
    context = logger.get_context()
    assert context["task"]["progress"] == "50%"
    
    logger.update_step("Final Step", TaskStatus.COMPLETE, progress=1.0)
    context = logger.get_context()
    assert context["task"]["progress"] == "100%"

def test_log_formatting():
    logger = TaskLogger("format_task", "Test log formatting")
    
    # Capture log output
    logger.update_step("Navigation", TaskStatus.RUNNING)
    log_output = logger.format_log_entry()
    
    # Verify log format matches the specified structure
    assert "[" in log_output  # Has timestamp
    assert "STEP 2/" in log_output  # Has step number (2 because update_step increments)
    assert "Navigation" in log_output  # Has action
    assert "→" in log_output  # Has status symbol for running
    
    # Add another step to test duration
    logger.update_step("Click button", TaskStatus.COMPLETE)
    log_output = logger.format_log_entry()
    assert "(" in log_output and "s)" in log_output  # Now we should have duration

def test_semantic_step_descriptions():
    logger = TaskLogger("semantic_task", "Test semantic descriptions")
    
    # Test navigation step
    logger.update_step(
        "Navigate to example.com",
        TaskStatus.RUNNING,
        action_type=ActionType.NAVIGATION
    )
    context = logger.get_context()
    assert context["task"]["current_action"] == "navigation"
    assert "🌐" in logger.format_log_entry()  # Navigation emoji
    
    # Test interaction step
    logger.update_step(
        "Click search button",
        TaskStatus.RUNNING,
        action_type=ActionType.INTERACTION
    )
    context = logger.get_context()
    assert context["task"]["current_action"] == "interaction"
    assert "🖱️" in logger.format_log_entry()  # Interaction emoji
    
    # Test extraction step
    logger.update_step(
        "Extract search results",
        TaskStatus.RUNNING,
        action_type=ActionType.EXTRACTION
    )
    context = logger.get_context()
    assert context["task"]["current_action"] == "extraction"
    assert "📑" in logger.format_log_entry()  # Extraction emoji

def test_redundant_message_filtering():
    logger = TaskLogger("filter_task", "Test message filtering")
    
    # Add multiple steps of the same type
    logger.update_step(
        "Navigate to example.com",
        TaskStatus.RUNNING,
        action_type=ActionType.NAVIGATION
    )
    logger.update_step(
        "Page loaded successfully",
        TaskStatus.COMPLETE,
        action_type=ActionType.NAVIGATION,
        suppress_similar=True  # Should be filtered as it's a completion of the same action
    )
    
    # Get all log entries
    log_entries = logger.get_log_history()
    
    # Verify that redundant messages are consolidated
    navigation_entries = [entry for entry in log_entries if "Navigate" in entry]
    assert len(navigation_entries) == 1  # Only the main action should be logged
    
    # Verify that the current step shows the completion status
    current_log = logger.format_log_entry()
    assert "✓" in current_log  # Success symbol should be in current state

def test_action_context_tracking():
    logger = TaskLogger("context_task", "Test action context")
    
    # Start a navigation action
    logger.update_step(
        "Navigate to example.com",
        TaskStatus.RUNNING,
        action_type=ActionType.NAVIGATION,
        context={
            "url": "https://example.com",
            "method": "GET",
            "headers": {"User-Agent": "browser-use"}
        }
    )
    
    context = logger.get_context()
    assert "action_context" in context["task"]
    assert context["task"]["action_context"]["url"] == "https://example.com"
    
    # Complete the action with results
    logger.update_step(
        "Navigation complete",
        TaskStatus.COMPLETE,
        action_type=ActionType.NAVIGATION,
        results={
            "status_code": 200,
            "page_title": "Example Domain",
            "load_time": 0.5
        }
    )
    
    context = logger.get_context()
    assert "action_results" in context["task"]
    assert context["task"]["action_results"]["status_code"] == 200

def test_retry_configuration():
    config = RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=10.0,
        jitter=0.1
    )
    
    # Test that delays follow exponential backoff pattern
    delays = [config.get_delay(attempt) for attempt in range(5)]
    assert delays[0] == 0  # First attempt has no delay
    assert 0.9 <= delays[1] <= 1.1  # First retry ~1.0s with jitter
    assert 1.8 <= delays[2] <= 2.2  # Second retry ~2.0s with jitter
    assert 3.6 <= delays[3] <= 4.4  # Third retry ~4.0s with jitter
    assert delays[4] == -1  # Beyond max retries
    
    # Test max delay capping
    config = RetryConfig(
        max_retries=5,
        base_delay=1.0,
        max_delay=5.0,
        jitter=0.0  # Disable jitter for predictable testing
    )
    assert config.get_delay(3) == 4.0  # Within max
    assert config.get_delay(4) == 5.0  # Capped at max

@pytest.mark.asyncio
async def test_retry_execution():
    logger = TaskLogger("retry_task", "Test retry logic")
    
    # Mock function that fails twice then succeeds
    attempt_count = 0
    async def mock_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count <= 2:
            raise ValueError("Temporary error")
        return "success"
    
    # Configure retry behavior
    retry_config = RetryConfig(max_retries=3, base_delay=0.1)
    
    # Execute with retry
    result = await logger.execute_with_retry(
        mock_operation,
        "test_operation",
        retry_config=retry_config
    )
    
    assert result == "success"
    assert attempt_count == 3  # Two failures + one success
    
    # Verify retry information in logs
    context = logger.get_context()
    assert "retries" in context["task"]
    retry_info = context["task"]["retries"]
    assert retry_info["attempts"] == 3
    assert retry_info["success"] is True
    assert len(retry_info["history"]) == 2  # Two retry attempts

@pytest.mark.asyncio
async def test_retry_max_attempts_exceeded():
    logger = TaskLogger("retry_task", "Test retry logic")
    
    # Mock function that always fails
    async def mock_operation():
        raise ValueError("Persistent error")
    
    # Configure retry behavior
    retry_config = RetryConfig(max_retries=2, base_delay=0.1)
    
    # Execute with retry and expect failure
    with pytest.raises(ValueError) as exc_info:
        await logger.execute_with_retry(
            mock_operation,
            "test_operation",
            retry_config=retry_config
        )
    
    assert str(exc_info.value) == "Persistent error"
    
    # Verify retry information in logs
    context = logger.get_context()
    assert "retries" in context["task"]
    retry_info = context["task"]["retries"]
    assert retry_info["attempts"] == 3  # Initial + 2 retries
    assert retry_info["success"] is False
    assert len(retry_info["history"]) == 3  # Initial attempt + two retries
    assert all(entry["error"] == "ValueError: Persistent error" for entry in retry_info["history"])
    
    # Verify the delays follow the expected pattern
    delays = [entry["delay"] for entry in retry_info["history"]]
    assert delays[0] > 0  # First retry has positive delay
    assert delays[1] > delays[0]  # Second retry has longer delay
    assert delays[2] == -1  # Final attempt indicates max retries exceeded

def test_retry_backoff_calculation():
    config = RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=10.0,
        jitter=0.0  # Disable jitter for predictable testing
    )
    
    # Test exponential backoff sequence
    assert config.get_delay(0) == 0  # First attempt
    assert config.get_delay(1) == 1.0  # First retry
    assert config.get_delay(2) == 2.0  # Second retry
    assert config.get_delay(3) == 4.0  # Third retry
    assert config.get_delay(4) == -1  # Beyond max retries
    
    # Test max delay capping
    config = RetryConfig(
        max_retries=5,
        base_delay=1.0,
        max_delay=5.0,
        jitter=0.0
    )
    assert config.get_delay(3) == 4.0  # Within max
    assert config.get_delay(4) == 5.0  # Capped at max

def test_color_scheme():
    """Test that color scheme is properly defined and accessible."""
    scheme = ColorScheme()
    
    # Test error colors
    assert scheme.error.startswith("\033[31m")  # Red
    assert scheme.warning.startswith("\033[33m")  # Yellow
    assert scheme.info.startswith("\033[36m")  # Cyan
    assert scheme.success.startswith("\033[32m")  # Green
    assert scheme.reset == "\033[0m"  # Reset

def test_log_formatting_with_colors():
    """Test that log messages are properly formatted with colors."""
    logger = TaskLogger("color_task", "Test color formatting")
    
    # Test error formatting
    logger.update_step("Failed operation", TaskStatus.FAILED)
    log_output = logger.format_log_entry()
    assert "\033[31m" in log_output  # Contains red color code
    assert "×" in log_output  # Contains error symbol
    
    # Test success formatting
    logger.update_step("Successful operation", TaskStatus.COMPLETE)
    log_output = logger.format_log_entry()
    assert "\033[32m" in log_output  # Contains green color code
    assert "✓" in log_output  # Contains success symbol
    
    # Test running state formatting
    logger.update_step("Running operation", TaskStatus.RUNNING)
    log_output = logger.format_log_entry()
    assert "\033[36m" in log_output  # Contains cyan color code
    assert "→" in log_output  # Contains running symbol

def test_color_disabled():
    """Test that colors can be disabled via environment variable."""
    os.environ["NO_COLOR"] = "1"
    logger = TaskLogger("no_color_task", "Test without colors")
    
    logger.update_step("Test operation", TaskStatus.COMPLETE)
    log_output = logger.format_log_entry()
    
    # Verify no color codes are present
    assert "\033[" not in log_output
    assert "✓" in log_output  # Symbols still present
    
    # Clean up
    del os.environ["NO_COLOR"]

def test_color_scheme_customization():
    """Test that color scheme can be customized."""
    custom_scheme = ColorScheme(
        error="\033[35m",  # Magenta for errors
        warning="\033[34m",  # Blue for warnings
        info="\033[37m",  # White for info
        success="\033[32m"  # Keep green for success
    )
    
    logger = TaskLogger("custom_color_task", "Test custom colors", color_scheme=custom_scheme)
    
    # Test custom error color
    logger.update_step("Failed operation", TaskStatus.FAILED)
    log_output = logger.format_log_entry()
    assert "\033[35m" in log_output  # Contains magenta color code
    
    # Test custom info color
    logger.update_step("Info message", TaskStatus.RUNNING)
    log_output = logger.format_log_entry()
    assert "\033[37m" in log_output  # Contains white color code

def test_log_formatter_with_colors():
    """Test that the log formatter properly applies colors to different components."""
    formatter = LogFormatter()
    
    # Create a mock log record
    class MockRecord:
        def __init__(self, levelname, msg):
            self.levelname = levelname
            self.msg = msg
            self.created = datetime.utcnow().timestamp()
    
    # Test error formatting
    error_record = MockRecord("ERROR", "Test error message")
    formatted = formatter.format(error_record)
    assert "\033[31m" in formatted  # Red for error
    assert "ERROR" in formatted
    
    # Test info formatting
    info_record = MockRecord("INFO", "Test info message")
    formatted = formatter.format(info_record)
    assert "\033[36m" in formatted  # Cyan for info
    assert "INFO" in formatted
    
    # Test warning formatting
    warn_record = MockRecord("WARNING", "Test warning message")
    formatted = formatter.format(warn_record)
    assert "\033[33m" in formatted  # Yellow for warning
    assert "WARNING" in formatted

def test_task_separator_style():
    """Test that separator styles are properly defined and formatted."""
    style = SeparatorStyle()
    
    # Test default separator styles
    assert len(style.task) >= 50  # Task separator should be substantial
    assert len(style.phase) >= 30  # Phase separator should be visible but less prominent
    assert len(style.error) >= 40  # Error separator should be distinct
    
    # Test that styles are different
    assert style.task != style.phase
    assert style.task != style.error
    assert style.phase != style.error

def test_task_start_separator():
    """Test that separators are added at task start."""
    logger = TaskLogger("separator_task", "Test separators")
    
    # Get initial log output
    log_entries = logger.get_log_history()
    
    # Should have task separator and initial step
    assert len(log_entries) == 2
    assert "=" * 50 in log_entries[0]  # Task separator
    assert "TASK GOAL: Test separators" in log_entries[1]  # Initial step message

def test_phase_separators():
    """Test that separators are added between different phases."""
    logger = TaskLogger("separator_task", "Test separators")
    
    # Navigation phase
    logger.start_phase("Navigation")
    logger.update_step("Navigate to example.com", TaskStatus.COMPLETE, action_type=ActionType.NAVIGATION)
    
    # Interaction phase
    logger.start_phase("Interaction")
    logger.update_step("Click button", TaskStatus.COMPLETE, action_type=ActionType.INTERACTION)
    
    # Get log entries
    log_entries = logger.get_log_history()
    
    # Count phase separators
    phase_separators = [entry for entry in log_entries if "-" * 30 in entry]
    assert len(phase_separators) == 2  # One before each phase

def test_error_separators():
    """Test that separators are added around error messages."""
    logger = TaskLogger("separator_task", "Test separators")
    
    # Simulate an error
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.log_error(e, step_number=1, action="test_action")
    
    # Get log entries
    log_entries = logger.get_log_history()
    
    # Should have error separators
    error_separators = [entry for entry in log_entries if "*" * 40 in entry]
    assert len(error_separators) == 2  # One before and one after error

def test_custom_separator_style():
    """Test that separator styles can be customized."""
    custom_style = SeparatorStyle(
        task="◈" * 30,
        phase="•" * 20,
        error="!" * 25
    )
    
    logger = TaskLogger("custom_separator_task", "Test custom separators", separator_style=custom_style)
    
    # Start a phase
    logger.start_phase("Test Phase")
    
    # Get log entries
    log_entries = logger.get_log_history()
    
    # Verify custom separators are used
    assert "◈" * 30 in log_entries[0]  # Task separator
    assert "•" * 20 in log_entries[2]  # Phase separator
    assert "→" in log_entries[2]  # Arrow indicator for phase start

def test_separator_with_colors():
    """Test that separators can be colored."""
    logger = TaskLogger("colored_separator_task", "Test colored separators")
    
    # Start a phase
    logger.start_phase("Test Phase")
    
    # Get log entries
    log_entries = logger.get_log_history()
    
    # Verify separators have color codes
    task_separator = log_entries[0]
    phase_separator = log_entries[1]
    
    assert "\033[" in task_separator  # Contains color code
    assert "\033[" in phase_separator  # Contains color code

def test_separator_disabled():
    """Test that separators can be disabled."""
    logger = TaskLogger("no_separator_task", "Test without separators", use_separators=False)
    
    # Start a phase
    logger.start_phase("Test Phase")
    
    # Get log entries
    log_entries = logger.get_log_history()
    
    # Verify no separators are present
    separators = [entry for entry in log_entries if any(c * 20 in entry for c in "=-*")]
    assert len(separators) == 0  # No separators should be present 