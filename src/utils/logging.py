import json
import logging
import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import traceback
import types

class LogLevel(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"

class LogJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Exception):
            return {
                'type': obj.__class__.__name__,
                'message': str(obj),
                'traceback': traceback.format_exception(type(obj), obj, obj.__traceback__)
            }
        if isinstance(obj, type):
            return obj.__name__
        if isinstance(obj, types.TracebackType):
            return traceback.format_tb(obj)
        return super().default(obj)

class LogFormatter(logging.Formatter):
    def __init__(self, use_json: bool = True):
        super().__init__()
        self.use_json = use_json
        self._event_counter: Dict[str, int] = {}

    def _serialize_error(self, exc_info) -> Dict[str, str]:
        """Serialize error information into a dictionary."""
        exc_type, exc_value, exc_tb = exc_info
        return {
            "type": exc_type.__name__ if exc_type else "Unknown",
            "message": str(exc_value) if exc_value else "",
            "stack_trace": self.formatException(exc_info) if exc_tb else ""
        }

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.datetime.fromtimestamp(record.created).strftime("%Y-%m-%dT%H:%M:%S")
        
        # Extract additional fields if they exist
        extra_fields = {}
        for key, value in vars(record).items():
            if key not in logging.LogRecord.__dict__ and not key.startswith('_'):
                extra_fields[key] = value

        if self.use_json:
            log_entry = {
                "timestamp": timestamp,
                "level": record.levelname,
                "logger": record.name or "root",
                "message": record.getMessage(),
                **extra_fields
            }
            
            if hasattr(record, 'event_type'):
                log_entry["event_type"] = getattr(record, 'event_type')
                
            if hasattr(record, 'event_data'):
                log_entry["data"] = getattr(record, 'event_data')

            if record.exc_info and record.levelno >= logging.ERROR:
                log_entry["error"] = self._serialize_error(record.exc_info)
            
            return json.dumps(log_entry, cls=LogJSONEncoder)
        else:
            # Compact format for non-JSON logs
            basic_msg = f"[{timestamp}] {record.levelname[0]}: {record.getMessage()}"
            
            if record.exc_info and record.levelno >= logging.ERROR:
                return f"{basic_msg}\n{self.formatException(record.exc_info)}"
            
            return basic_msg

class BatchedEventLogger:
    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._batched_events: Dict[str, List[Dict[str, Any]]] = {}
        
    def add_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        if event_type not in self._batched_events:
            self._batched_events[event_type] = []
        self._batched_events[event_type].append(event_data)
        
    def flush(self) -> None:
        for event_type, events in self._batched_events.items():
            if events:
                self._logger.info(
                    f"Batch: {len(events)} {event_type} events",
                    extra={
                        "event_type": f"batched_{event_type}",
                        "event_data": {
                            "count": len(events),
                            "events": events
                        }
                    }
                )
        self._batched_events.clear()

def setup_logging(
    level: str = "INFO",
    use_json: bool = True,
    log_file: Optional[str] = None,
    exclude_patterns: Optional[List[str]] = None
) -> None:
    """
    Setup logging configuration with the improved formatter
    
    Args:
        level: The logging level to use
        use_json: Whether to use JSON formatting
        log_file: Optional file to write logs to
        exclude_patterns: Optional list of patterns to exclude from logging
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(LogFormatter(use_json=use_json))
    
    if exclude_patterns:
        class ExcludeFilter(logging.Filter):
            def filter(self, record: logging.LogRecord) -> bool:
                return not any(pattern in record.getMessage() for pattern in exclude_patterns)
        
        console_handler.addFilter(ExcludeFilter())
    
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(LogFormatter(use_json=True))  # Always use JSON for file logging
        if exclude_patterns:
            file_handler.addFilter(ExcludeFilter())
        root_logger.addHandler(file_handler)

# Production filter patterns
PRODUCTION_EXCLUDE_PATTERNS = [
    "deprecated",
    "virtual environment",
    "Activating virtual environment",
    "✅ Eval: Success",
    "🤔 Thought:",
    "VIRTUAL_ENV:"
] 