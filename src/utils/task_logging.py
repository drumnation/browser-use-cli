from typing import Dict, Any, List, Literal, Optional, Union, Callable, TypeVar, Awaitable
from dataclasses import dataclass, asdict, field
from datetime import datetime
import json
from enum import Enum
import traceback
import asyncio
import random
import os
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init()

# Define generic type parameter at module level
T = TypeVar('T')

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"

class ActionType(str, Enum):
    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    RECOVERY = "recovery"

    @property
    def emoji(self) -> str:
        """Get the emoji representation of the action type."""
        return {
            ActionType.NAVIGATION: "🌐",
            ActionType.INTERACTION: "🖱️",
            ActionType.EXTRACTION: "📑",
            ActionType.VALIDATION: "✅",
            ActionType.RECOVERY: "🔄"
        }[self]

@dataclass
class PerformanceMetrics:
    """Performance metrics for task execution."""
    total_duration: float = 0.0
    step_breakdown: Dict[str, float] = field(default_factory=dict)
    
    def add_step_duration(self, step_type: str, duration: float) -> None:
        """Add duration for a step type."""
        if step_type not in self.step_breakdown:
            self.step_breakdown[step_type] = 0
        self.step_breakdown[step_type] += duration
        self.total_duration += duration

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a dictionary."""
        return {
            "total_duration": self.total_duration,
            "step_breakdown": self.step_breakdown
        }

@dataclass
class ErrorInfo:
    """Information about an error that occurred."""
    type: str
    message: str
    step: int
    action: str
    traceback: Optional[str] = None

@dataclass
class StepInfo:
    """Information about the current step in a task."""
    number: int
    description: str
    started_at: str
    status: Union[TaskStatus, str]
    duration: Optional[float] = None
    progress: Optional[float] = None
    action_type: Optional[ActionType] = None
    context: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    suppress_similar: bool = False

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)
        if isinstance(self.action_type, str):
            self.action_type = ActionType(self.action_type)
    
    @property
    def status_value(self) -> str:
        """Get the string value of the status."""
        return self.status.value if isinstance(self.status, TaskStatus) else str(self.status)

@dataclass
class BrowserState:
    """Current state of the browser."""
    url: str
    page_ready: bool
    dynamic_content_loaded: bool
    visible_elements: int
    current_frame: Optional[str] = None
    active_element: Optional[str] = None
    page_title: Optional[str] = None

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 10.0
    jitter: float = 0.1
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt using exponential backoff."""
        if attempt == 0:
            return 0
        if attempt > self.max_retries:
            return -1
            
        # Calculate exponential delay
        delay = self.base_delay * (2 ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        # Add jitter if configured
        if self.jitter > 0:
            jitter_range = delay * self.jitter
            delay += random.uniform(-jitter_range/2, jitter_range/2)
            
        return max(0, delay)

@dataclass
class RetryInfo:
    """Information about retry attempts."""
    attempts: int = 0
    success: bool = False
    history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class TaskContext:
    """Context information for a task."""
    id: str
    goal: str
    current_step: StepInfo
    browser_state: BrowserState
    started_at: Optional[str] = None
    error: Optional[ErrorInfo] = None
    performance: Optional[PerformanceMetrics] = None
    log_history: List[StepInfo] = field(default_factory=list)
    retries: Optional[RetryInfo] = None
    
    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.utcnow().isoformat()
        if self.performance is None:
            self.performance = PerformanceMetrics()
        if self.retries is None:
            self.retries = RetryInfo()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the context to a dictionary for logging."""
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "task": {
                "id": self.id,
                "goal": self.goal,
                "progress": self._format_progress(),
                "elapsed_time": self._calculate_elapsed_time(),
                "status": self.current_step.status_value
            }
        }
        
        # Add retry information if available
        if self.retries and self.retries.attempts > 0:
            result["task"]["retries"] = {
                "attempts": self.retries.attempts,
                "success": self.retries.success,
                "history": self.retries.history
            }
        
        # Add current action information
        if self.current_step.action_type:
            result["task"]["current_action"] = self.current_step.action_type.value
        if self.current_step.context:
            result["task"]["action_context"] = self.current_step.context
        if self.current_step.results:
            result["task"]["action_results"] = self.current_step.results
            
        # Add browser state
        result["browser"] = {
            "url": self.browser_state.url,
            "state": "ready" if self.browser_state.page_ready else "loading",
            "visible_elements": self.browser_state.visible_elements,
            "dynamic_content": "loaded" if self.browser_state.dynamic_content_loaded else "loading"
        }
        
        if self.browser_state.current_frame:
            result["browser"]["current_frame"] = self.browser_state.current_frame
        if self.browser_state.active_element:
            result["browser"]["active_element"] = self.browser_state.active_element
        if self.browser_state.page_title:
            result["browser"]["page_title"] = self.browser_state.page_title
            
        if self.error:
            result["error"] = {
                "type": self.error.type,
                "message": self.error.message,
                "step": self.error.step,
                "action": self.error.action
            }
            if self.error.traceback:
                result["error"]["traceback"] = self.error.traceback
                
        if self.performance and self.performance.step_breakdown:
            result["performance"] = self.performance.to_dict()
            
        return result
    
    def _format_progress(self) -> str:
        """Format the progress information."""
        if self.current_step.progress is not None:
            return f"{int(self.current_step.progress * 100)}%"
        return f"{self.current_step.number}/unknown steps"
    
    def _calculate_elapsed_time(self) -> str:
        """Calculate the elapsed time since task start."""
        if self.started_at is None:
            return "0.0s"
        start = datetime.fromisoformat(self.started_at)
        elapsed = datetime.utcnow() - start
        return f"{elapsed.total_seconds():.1f}s"

@dataclass
class ColorScheme:
    """Color scheme for log messages."""
    error: str = Fore.RED
    warning: str = Fore.YELLOW
    info: str = Fore.CYAN
    success: str = Fore.GREEN
    reset: str = Style.RESET_ALL
    
    @property
    def enabled(self) -> bool:
        """Check if colors should be enabled."""
        return not bool(os.getenv("NO_COLOR"))
    
    def apply(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if not self.enabled:
            return text
        return f"{color}{text}{self.reset}"

class LogFormatter:
    """Formatter for log messages with color support."""
    
    def __init__(self, color_scheme: Optional[ColorScheme] = None):
        self.colors = color_scheme or ColorScheme()
    
    def format(self, record: Any) -> str:
        """Format a log record with appropriate colors."""
        level_colors = {
            "ERROR": self.colors.error,
            "WARNING": self.colors.warning,
            "INFO": self.colors.info
        }
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        
        # Color the level name
        level_color = level_colors.get(record.levelname, self.colors.info)
        colored_level = self.colors.apply(record.levelname, level_color)
        
        return f"[{timestamp}] {colored_level}: {record.msg}"

@dataclass
class SeparatorStyle:
    """Style configuration for visual separators."""
    task: str = "=" * 50  # Task separator (longer)
    phase: str = "-" * 30  # Phase separator (medium)
    error: str = "*" * 40  # Error separator (distinct)

class TaskLogger:
    """Advanced logger for task context and state tracking."""
    
    def __init__(
        self,
        task_id: str,
        goal: str,
        color_scheme: Optional[ColorScheme] = None,
        separator_style: Optional[SeparatorStyle] = None,
        use_separators: bool = True
    ):
        self.context = TaskContext(
            id=task_id,
            goal=goal,
            current_step=StepInfo(
                number=1,
                description="Task initialized",
                started_at=datetime.utcnow().isoformat(),
                status=TaskStatus.PENDING
            ),
            browser_state=BrowserState(
                url="",
                page_ready=False,
                dynamic_content_loaded=False,
                visible_elements=0
            ),
            retries=RetryInfo()
        )
        self._step_start_time: Optional[datetime] = None
        self.colors = color_scheme or ColorScheme()
        self.separators = separator_style or SeparatorStyle()
        self.use_separators = use_separators
        
        # Add initial task separator and goal
        if self.use_separators:
            self._add_separator("task")
            self._add_log_entry(f"TASK GOAL: {goal}")
    
    def start_phase(self, phase_name: str) -> None:
        """Start a new phase in the task."""
        if self.use_separators:
            self._add_separator("phase")
            self._add_log_entry(f"PHASE: {phase_name}")
    
    def _add_separator(self, separator_type: Literal["task", "phase", "error"]) -> None:
        """Add a visual separator to the log history."""
        if not self.use_separators:
            return
            
        separator = getattr(self.separators, separator_type)
        colored_separator = self.colors.apply(
            separator,
            self.colors.info if separator_type != "error" else self.colors.error
        )
        self._add_log_entry(colored_separator)
    
    def _add_log_entry(self, entry: str) -> None:
        """Add a raw log entry to the history."""
        step = StepInfo(
            number=self.context.current_step.number,
            description=entry,
            started_at=datetime.utcnow().isoformat(),
            status=TaskStatus.RUNNING
        )
        self.context.log_history.append(step)
    
    def update_step(self, 
                   description: str, 
                   status: TaskStatus, 
                   progress: Optional[float] = None,
                   action_type: Optional[ActionType] = None,
                   context: Optional[Dict[str, Any]] = None,
                   results: Optional[Dict[str, Any]] = None,
                   suppress_similar: bool = False) -> None:
        """Update the current step information."""
        step_duration = None
        if self._step_start_time:
            step_duration = (datetime.utcnow() - self._step_start_time).total_seconds()
            
        new_step = StepInfo(
            number=self.context.current_step.number + 1,
            description=description,
            started_at=datetime.utcnow().isoformat(),
            status=status,
            duration=step_duration,
            progress=progress,
            action_type=action_type,
            context=context,
            results=results,
            suppress_similar=suppress_similar
        )
        
        # Check if we should suppress this step
        if not suppress_similar or not self._is_similar_to_previous(new_step):
            self.context.log_history.append(new_step)
            self.context.current_step = new_step
            self._step_start_time = datetime.utcnow()
        else:
            # Update the previous step with new status/results
            prev_step = self.context.log_history[-1]
            prev_step.status = status
            if results:
                prev_step.results = results
            # Update current step to reflect changes
            self.context.current_step = prev_step
    
    def _is_similar_to_previous(self, step: StepInfo) -> bool:
        """Check if a step is similar to the previous one."""
        if not self.context.log_history:
            return False
        prev_step = self.context.log_history[-1]
        return (
            prev_step.action_type == step.action_type and
            prev_step.description.split()[0] == step.description.split()[0]  # Compare first word
        )
    
    def get_log_history(self) -> List[str]:
        """Get the formatted history of log entries."""
        return [self._format_step(step) for step in self.context.log_history]
    
    def _format_step(self, step: StepInfo) -> str:
        """Format a step as a log entry with colors."""
        timestamp = datetime.fromisoformat(step.started_at).strftime("%Y-%m-%d %H:%M:%S")
        duration = f"({step.duration:.1f}s)" if step.duration is not None else ""
        
        # Color-coded status symbols
        if isinstance(step.status, TaskStatus):
            status_symbol = {
                TaskStatus.COMPLETE: self.colors.apply("✓", self.colors.success),
                TaskStatus.FAILED: self.colors.apply("×", self.colors.error),
                TaskStatus.RUNNING: self.colors.apply("→", self.colors.info),
                TaskStatus.PENDING: self.colors.apply("→", self.colors.info)
            }.get(step.status, self.colors.apply("→", self.colors.info))
        else:
            status_symbol = self.colors.apply("→", self.colors.info)
        
        # Color-coded action emoji
        action_emoji = step.action_type.emoji if step.action_type else ""
        if action_emoji:
            action_emoji = self.colors.apply(action_emoji, self.colors.info)
        
        # Format step number with info color
        step_number = self.colors.apply(f"STEP {step.number}/?", self.colors.info)
        
        return f"[{timestamp}] {action_emoji} {step_number} {step.description} {status_symbol} {duration}"
    
    def format_log_entry(self) -> str:
        """Format the current state as a log entry."""
        return self._format_step(self.context.current_step)
    
    def update_browser_state(self, 
                           url: Optional[str] = None,
                           page_ready: Optional[bool] = None,
                           dynamic_content_loaded: Optional[bool] = None,
                           visible_elements: Optional[int] = None,
                           current_frame: Optional[str] = None,
                           active_element: Optional[str] = None,
                           page_title: Optional[str] = None) -> None:
        """Update the browser state information."""
        if url is not None:
            self.context.browser_state.url = url
        if page_ready is not None:
            self.context.browser_state.page_ready = page_ready
        if dynamic_content_loaded is not None:
            self.context.browser_state.dynamic_content_loaded = dynamic_content_loaded
        if visible_elements is not None:
            self.context.browser_state.visible_elements = visible_elements
        if current_frame is not None:
            self.context.browser_state.current_frame = current_frame
        if active_element is not None:
            self.context.browser_state.active_element = active_element
        if page_title is not None:
            self.context.browser_state.page_title = page_title
    
    def log_error(self, error: Exception, step_number: int, action: str) -> None:
        """Log an error with context."""
        if self.use_separators:
            self._add_separator("error")
            
        self.context.error = ErrorInfo(
            type=error.__class__.__name__,
            message=str(error),
            step=step_number,
            action=action,
            traceback=traceback.format_exc()
        )
        self.context.current_step.status = TaskStatus.FAILED
        
        if self.use_separators:
            self._add_separator("error")
    
    def start_performance_tracking(self) -> None:
        """Start tracking performance metrics."""
        self._step_start_time = datetime.utcnow()
    
    def track_step_duration(self, step_type: str, duration: float) -> None:
        """Track the duration of a specific step type."""
        if self.context.performance is not None:
            self.context.performance.add_step_duration(step_type, duration)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get the current performance metrics."""
        if self.context.performance is not None:
            return self.context.performance.to_dict()
        return {"total_duration": 0.0, "step_breakdown": {}}
    
    def get_context(self) -> Dict[str, Any]:
        """Get the current context as a dictionary."""
        return self.context.to_dict()
    
    def log_state(self) -> None:
        """Log the current state."""
        state = self.get_context()
        print(json.dumps(state, indent=2))
    
    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_name: str,
        retry_config: Optional[RetryConfig] = None
    ) -> T:
        """Execute an operation with retry logic."""
        if retry_config is None:
            retry_config = RetryConfig()
            
        attempt = 0
        last_error = None
        
        while True:
            try:
                # Calculate and apply delay if this is a retry
                delay = retry_config.get_delay(attempt)
                if delay == -1:  # Max retries exceeded
                    if last_error:
                        raise last_error
                    raise Exception("Max retries exceeded")
                    
                if delay > 0:
                    await asyncio.sleep(delay)
                
                # Attempt the operation
                result = await operation()
                
                # Update retry info on success
                if self.context.retries is not None:
                    self.context.retries.attempts = attempt + 1
                    self.context.retries.success = True
                
                return result
                
            except Exception as e:
                last_error = e
                attempt += 1
                
                # Log the retry attempt
                if self.context.retries is not None:
                    self.context.retries.history.append({
                        "attempt": attempt,
                        "timestamp": datetime.utcnow().isoformat(),
                        "error": f"{e.__class__.__name__}: {str(e)}",
                        "delay": retry_config.get_delay(attempt)
                    })
                
                # Update the error context
                self.log_error(e, self.context.current_step.number, operation_name)
                
                # Continue if we haven't exceeded max retries
                if attempt <= retry_config.max_retries:
                    self.update_step(
                        f"Retrying {operation_name} (attempt {attempt + 1}/{retry_config.max_retries + 1})",
                        TaskStatus.RUNNING
                    )
                    continue
                    
                # Max retries exceeded
                if self.context.retries is not None:
                    self.context.retries.attempts = attempt
                    self.context.retries.success = False
                raise 