from typing import Optional, Dict, Any, List
import logging
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from colorama import init, Fore, Style
import os

# Initialize colorama
init()

@dataclass
class ColorScheme:
    """Color scheme for different log elements."""
    ERROR: str = Fore.RED
    WARNING: str = Fore.YELLOW
    INFO: str = Fore.CYAN
    DEBUG: str = Style.DIM
    TIMESTAMP: str = Fore.WHITE
    SUCCESS: str = Fore.GREEN
    STEP: str = Fore.BLUE
    RESET: str = Style.RESET_ALL

class ColorizedFormatter(logging.Formatter):
    """Formatter that adds colors to log output."""
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and not os.getenv('NO_COLOR')
        self.colors = ColorScheme()
    
    def colorize(self, text: str, color: str) -> str:
        """Add color to text if colors are enabled."""
        if self.use_colors:
            return f"{color}{text}{self.colors.RESET}"
        return text
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        # Get the appropriate color for the log level
        level_color = getattr(self.colors, record.levelname, self.colors.INFO)
        
        # Format timestamp
        timestamp = self.colorize(
            datetime.utcnow().strftime("%H:%M:%S"),
            self.colors.TIMESTAMP
        )
        
        # Format level
        level = self.colorize(record.levelname, level_color)
        
        # Format message and handle special keywords
        msg = record.getMessage()
        if "✓" in msg:
            msg = msg.replace("✓", self.colorize("✓", self.colors.SUCCESS))
        if "×" in msg:
            msg = msg.replace("×", self.colorize("×", self.colors.ERROR))
        if "STEP" in msg:
            msg = msg.replace("STEP", self.colorize("STEP", self.colors.STEP))
        
        # Build the basic log message
        log_message = f"[{timestamp}] {level} {msg}"
        
        # Add structured data if available
        if hasattr(record, 'event_type'):
            event_type = self.colorize(record.event_type, self.colors.INFO)
            if hasattr(record, 'data'):
                # Format the data as JSON but don't colorize it
                data_str = json.dumps(record.data, indent=2)
                log_message = f"{log_message} | {event_type} | {data_str}"
        
        return log_message

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        output = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        
        # Add extra fields from record.__dict__ to handle custom attributes
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in output and key not in ('args', 'exc_info', 'exc_text', 'msg'):
                    output[key] = value
            
        return json.dumps(output)

def setup_structured_logging(level: int = logging.INFO, use_colors: bool = True, json_output: bool = False) -> None:
    """Set up structured logging with optional colorized output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with appropriate formatter
    handler = logging.StreamHandler()
    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(ColorizedFormatter(use_colors=use_colors))
    
    root_logger.addHandler(handler)

@dataclass
class ProgressEvent:
    """Represents a progress update in the browser automation process."""
    step: str
    status: str
    progress: float  # 0.0 to 1.0
    message: str
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

@dataclass
class BrowserEvent:
    """Represents a browser-related event."""
    event_type: str
    details: Dict[str, Any]
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

class StructuredLogger:
    """Handles structured logging with progress reporting and feedback."""
    
    def __init__(self, logger_name: str = "browser_automation"):
        self.logger = logging.getLogger(logger_name)
        self.progress_events: List[ProgressEvent] = []
        self.browser_events: List[BrowserEvent] = []
        self._current_progress: float = 0.0
        
    def log_progress(self, step: str, status: str, progress: float, message: str) -> None:
        """Log a progress update."""
        event = ProgressEvent(step=step, status=status, progress=progress, message=message)
        self.progress_events.append(event)
        self._current_progress = progress
        
        self.logger.info("Progress Update", extra={
            "event_type": "progress",
            "data": asdict(event)
        })
    
    def log_browser_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log a browser-related event."""
        event = BrowserEvent(event_type=event_type, details=details)
        self.browser_events.append(event)
        
        self.logger.info(f"Browser Event: {event_type}", extra={
            "event_type": "browser",
            "data": asdict(event)
        })
    
    def get_current_progress(self) -> float:
        """Get the current progress as a float between 0 and 1."""
        return self._current_progress
    
    def get_progress_history(self) -> List[Dict[str, Any]]:
        """Get the history of progress events."""
        return [asdict(event) for event in self.progress_events]
    
    def get_browser_events(self) -> List[Dict[str, Any]]:
        """Get all browser events."""
        return [asdict(event) for event in self.browser_events]
    
    def clear_history(self) -> None:
        """Clear all stored events."""
        self.progress_events.clear()
        self.browser_events.clear()
        self._current_progress = 0.0

class EventBatcher:
    def __init__(self, batch_size: int = 5):
        self.events: List[BrowserEvent] = []
        self.batch_size = max(1, batch_size)  # Ensure minimum batch size of 1

    def add_event(self, event: BrowserEvent) -> Optional[Dict[str, Any]]:
        self.events.append(event)
        if len(self.events) >= self.batch_size:
            return self.flush_events()
        return None

    def flush_events(self) -> Dict[str, Any]:
        if not self.events:
            return {
                "timestamp": datetime.now().isoformat(),
                "total_events": 0,
                "success_count": 0,
                "error_count": 0,
                "duration_ms": 0
            }

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_events": len(self.events),
            "success_count": sum(1 for e in self.events if e.get_status() == "success"),
            "error_count": sum(1 for e in self.events if e.get_status() == "failed"),
            "duration_ms": self._calculate_total_duration()
        }
        self.events = []
        return summary

    def get_event_count(self) -> int:
        return len(self.events)

    def _calculate_total_duration(self) -> int:
        total_duration = 0
        for event in self.events:
            if event.metrics and "duration_ms" in event.metrics:
                total_duration += event.metrics["duration_ms"]
        return total_duration 