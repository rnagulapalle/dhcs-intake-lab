"""
BHT Platform Logging

Phase 3: Structured logging infrastructure for consistent log schemas.
Provides a PlatformLogger and JSON formatter for uniform log output.

Features:
- JSON structured logging (configurable)
- Consistent field schemas across all platform components
- Log level configuration via environment
- Automatic trace_id injection from AuditContext
"""
import json
import logging
import os
import sys
import threading
from datetime import datetime
from typing import Any, Dict, Optional

# Avoid circular import - we'll get trace_id lazily
_get_current_trace_id = None


def _lazy_get_trace_id() -> Optional[str]:
    """Lazily import and get current trace_id to avoid circular imports."""
    global _get_current_trace_id
    if _get_current_trace_id is None:
        try:
            from platform.audit_context import AuditContext
            _get_current_trace_id = lambda: getattr(AuditContext.current(), 'trace_id', None)
        except ImportError:
            _get_current_trace_id = lambda: None
    return _get_current_trace_id()


# =============================================================================
# Log Level Configuration
# =============================================================================

def get_log_level() -> int:
    """
    Get log level from environment.

    Environment: BHT_LOG_LEVEL (default: INFO)
    Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    level_name = os.getenv("BHT_LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


def is_json_logging_enabled() -> bool:
    """
    Check if JSON logging is enabled.

    Environment: BHT_JSON_LOGS_ENABLED (default: true)
    """
    return os.getenv("BHT_JSON_LOGS_ENABLED", "true").lower() == "true"


# =============================================================================
# JSON Log Formatter
# =============================================================================

class JSONLogFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Produces log entries in the format:
    {
        "timestamp": "2024-01-15T10:30:00.123Z",
        "level": "INFO",
        "logger": "platform.model_gateway",
        "message": "LLM invocation completed",
        "trace_id": "abc-123",  # Injected from AuditContext if available
        "extra": { ... }  # Any extra fields passed to the log call
    }
    """

    def __init__(self, include_trace_id: bool = True):
        """
        Initialize JSON formatter.

        Args:
            include_trace_id: If True, inject trace_id from current AuditContext
        """
        super().__init__()
        self._include_trace_id = include_trace_id

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add trace_id from current context if available
        if self._include_trace_id:
            trace_id = _lazy_get_trace_id()
            if trace_id:
                log_entry["trace_id"] = trace_id

        # Add any extra fields
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_entry["extra"] = record.extra

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add standard fields that might be useful
        if hasattr(record, "funcName"):
            log_entry["function"] = record.funcName
        if hasattr(record, "lineno"):
            log_entry["line"] = record.lineno

        return json.dumps(log_entry, default=str)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for development.

    Produces log entries in the format:
    2024-01-15 10:30:00 [INFO] platform.model_gateway: LLM invocation completed (trace_id=abc-123)
    """

    def __init__(self, include_trace_id: bool = True):
        super().__init__()
        self._include_trace_id = include_trace_id

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        base = f"{timestamp} [{record.levelname}] {record.name}: {record.getMessage()}"

        if self._include_trace_id:
            trace_id = _lazy_get_trace_id()
            if trace_id:
                base += f" (trace_id={trace_id[:8]}...)"

        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)

        return base


# =============================================================================
# Platform Logger
# =============================================================================

class PlatformLogger:
    """
    Platform-aware logger with structured logging support.

    Features:
    - Automatic trace_id injection
    - Structured extra fields
    - Consistent log schema
    - JSON or human-readable output

    Usage:
        logger = PlatformLogger("platform.model_gateway")
        logger.info("LLM invocation completed", latency_ms=150.5, model="gpt-4o-mini")
        logger.error("Invocation failed", error_type="timeout", retries=3)
    """

    def __init__(self, name: str):
        """
        Initialize platform logger.

        Args:
            name: Logger name (typically __name__)
        """
        self._logger = logging.getLogger(name)
        self._name = name

    def _log(self, level: int, message: str, **kwargs) -> None:
        """
        Internal log method with extra field support.

        Args:
            level: Logging level
            message: Log message
            **kwargs: Extra fields to include in structured log
        """
        extra = {"extra": kwargs} if kwargs else {}
        self._logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs) -> None:
        """Log at DEBUG level."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log at INFO level."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log at WARNING level."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log at ERROR level."""
        extra = {"extra": kwargs} if kwargs else {}
        self._logger.error(message, exc_info=exc_info, extra=extra)

    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log at CRITICAL level."""
        extra = {"extra": kwargs} if kwargs else {}
        self._logger.critical(message, exc_info=exc_info, extra=extra)

    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        extra = {"extra": kwargs} if kwargs else {}
        self._logger.exception(message, extra=extra)


# =============================================================================
# Logging Configuration
# =============================================================================

_logging_configured = False
_config_lock = threading.Lock()


def configure_platform_logging(
    json_logs: Optional[bool] = None,
    log_level: Optional[int] = None,
    include_trace_id: bool = True,
) -> None:
    """
    Configure platform logging infrastructure.

    Should be called once at application startup.
    Safe to call multiple times (only first call takes effect).

    Args:
        json_logs: Enable JSON logging (default: from BHT_JSON_LOGS_ENABLED)
        log_level: Log level (default: from BHT_LOG_LEVEL)
        include_trace_id: Include trace_id in logs (default: True)
    """
    global _logging_configured

    with _config_lock:
        if _logging_configured:
            return

        # Determine settings
        use_json = json_logs if json_logs is not None else is_json_logging_enabled()
        level = log_level if log_level is not None else get_log_level()

        # Create handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Set formatter based on config
        if use_json:
            handler.setFormatter(JSONLogFormatter(include_trace_id=include_trace_id))
        else:
            handler.setFormatter(HumanReadableFormatter(include_trace_id=include_trace_id))

        # Configure root logger for platform
        platform_logger = logging.getLogger("platform")
        platform_logger.setLevel(level)
        platform_logger.addHandler(handler)

        # Also configure agents logger
        agents_logger = logging.getLogger("agents")
        agents_logger.setLevel(level)
        agents_logger.addHandler(handler)

        _logging_configured = True


def get_platform_logger(name: str) -> PlatformLogger:
    """
    Get a platform logger instance.

    Convenience function for creating loggers.

    Args:
        name: Logger name (typically __name__)

    Returns:
        PlatformLogger instance
    """
    # Ensure logging is configured
    configure_platform_logging()
    return PlatformLogger(name)


# =============================================================================
# Logging Context Manager
# =============================================================================

class LogContext:
    """
    Context manager for adding extra fields to all logs within a scope.

    Usage:
        with LogContext(workflow_id="curation", tenant_id="county_la"):
            logger.info("Processing request")  # Includes workflow_id and tenant_id
    """

    _context: Dict[str, Any] = {}
    _lock = threading.Lock()

    def __init__(self, **kwargs):
        """
        Initialize log context with extra fields.

        Args:
            **kwargs: Fields to add to all logs in this context
        """
        self._fields = kwargs
        self._previous: Dict[str, Any] = {}

    def __enter__(self) -> "LogContext":
        with self._lock:
            # Save previous values
            for key in self._fields:
                if key in LogContext._context:
                    self._previous[key] = LogContext._context[key]
            # Set new values
            LogContext._context.update(self._fields)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        with self._lock:
            # Restore previous values
            for key in self._fields:
                if key in self._previous:
                    LogContext._context[key] = self._previous[key]
                else:
                    LogContext._context.pop(key, None)

    @classmethod
    def get_context(cls) -> Dict[str, Any]:
        """Get current log context fields."""
        with cls._lock:
            return cls._context.copy()
