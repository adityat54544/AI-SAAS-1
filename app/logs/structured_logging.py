"""
Structured Logging Helper.

Provides JSON logging with correlation IDs for request tracing.
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variables for request tracing
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
job_id_var: ContextVar[str] = ContextVar("job_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_var.get()


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set the request ID in context and return it."""
    rid = request_id or str(uuid.uuid4())[:16]
    request_id_var.set(rid)
    return rid


def get_job_id() -> str:
    """Get the current job ID from context."""
    return job_id_var.get()


def set_job_id(job_id: Optional[str] = None) -> str:
    """Set the job ID in context and return it."""
    jid = job_id or str(uuid.uuid4())[:16]
    job_id_var.set(jid)
    return jid


def get_user_id() -> str:
    """Get the current user ID from context."""
    return user_id_var.get()


def set_user_id(user_id: str) -> None:
    """Set the user ID in context."""
    user_id_var.set(user_id)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON logs with structured data.
    
    Includes:
    - Timestamp in ISO format
    - Log level
    - Message
    - Correlation IDs (request_id, job_id, user_id)
    - Extra fields
    """
    
    def __init__(self, include_extra: bool = True):
        """Initialize the formatter."""
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        # Base log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation IDs from context
        request_id = get_request_id()
        if request_id:
            log_entry["request_id"] = request_id
        
        job_id = get_job_id()
        if job_id:
            log_entry["job_id"] = job_id
        
        user_id = get_user_id()
        if user_id:
            log_entry["user_id"] = user_id
        
        # Add extra fields from the record
        if self.include_extra:
            extra_fields = {}
            # Get all attributes that are not standard LogRecord attributes
            standard_attrs = {
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                'message', 'asctime',
            }
            
            for key, value in record.__dict__.items():
                if key not in standard_attrs:
                    extra_fields[key] = value
            
            if extra_fields:
                log_entry["extra"] = extra_fields
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        if record.stack_info:
            log_entry["stack_trace"] = record.stack_info
        
        return json.dumps(log_entry, default=str)


class StructuredLogger:
    """
    Structured logger that provides convenient methods for logging with context.
    """
    
    def __init__(self, name: str):
        """Initialize the logger."""
        self.logger = logging.getLogger(name)
    
    def _log(self, level: int, message: str, **kwargs):
        """Log a message with extra fields."""
        extra = kwargs.pop("extra", {})
        extra.update(kwargs)
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception message with stack trace."""
        extra = kwargs.pop("extra", {})
        extra.update(kwargs)
        self.logger.exception(message, extra=extra)


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
) -> None:
    """
    Set up structured logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON format (True) or plain text (False)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
    
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


# Request context manager for correlation IDs
class RequestContext:
    """Context manager for request-scoped logging context."""
    
    def __init__(
        self,
        request_id: Optional[str] = None,
        job_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Initialize the context."""
        self.request_id = request_id
        self.job_id = job_id
        self.user_id = user_id
        self._old_request_id = None
        self._old_job_id = None
        self._old_user_id = None
    
    def __enter__(self):
        """Enter the context."""
        self._old_request_id = get_request_id()
        self._old_job_id = get_job_id()
        self._old_user_id = get_user_id()
        
        if self.request_id:
            set_request_id(self.request_id)
        if self.job_id:
            set_job_id(self.job_id)
        if self.user_id:
            set_user_id(self.user_id)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        # Restore old values
        if self._old_request_id:
            set_request_id(self._old_request_id)
        if self._old_job_id:
            set_job_id(self._old_job_id)
        if self._old_user_id:
            set_user_id(self._old_user_id)


# Convenience function for redacting sensitive data
def redact_sensitive(data: Dict[str, Any], sensitive_keys: set = None) -> Dict[str, Any]:
    """
    Redact sensitive values from a dictionary.
    
    Args:
        data: Dictionary to redact
        sensitive_keys: Set of keys to redact
        
    Returns:
        Dictionary with sensitive values redacted
    """
    if sensitive_keys is None:
        sensitive_keys = {
            'password', 'secret', 'token', 'api_key', 'apikey',
            'authorization', 'credential', 'private_key',
            'access_token', 'refresh_token', 'session_id',
        }
    
    redacted = {}
    for key, value in data.items():
        lower_key = key.lower()
        if any(sensitive in lower_key for sensitive in sensitive_keys):
            redacted[key] = "[REDACTED]"
        elif isinstance(value, dict):
            redacted[key] = redact_sensitive(value, sensitive_keys)
        else:
            redacted[key] = value
    
    return redacted