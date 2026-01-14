"""
BHT Platform Audit Sink

Phase 3: Audit sink abstraction for flexible audit log destinations.
Provides a lightweight interface for routing audit entries to different backends.

Implementations:
- StdoutAuditSink: Default, writes JSON to stdout
- FileAuditSink: Writes JSON to a file (for local dev)

No external dependencies required.
"""
import json
import logging
import os
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Mandatory Audit Fields
# =============================================================================

# These fields MUST be present in every audit log entry
MANDATORY_FIELDS = {
    "trace_id",
    "request_id",
    "workflow_id",
    "operation",  # Type of operation (llm_call, retrieval, workflow_step, api_request)
    "latency_ms",
    "success",
}

# Optional but recommended fields
RECOMMENDED_FIELDS = {
    "tenant_id",
    "model",  # For LLM calls
    "error_type",  # When success=False
    "timestamp",
}


def validate_audit_entry(entry: Dict[str, Any]) -> List[str]:
    """
    Validate that an audit entry contains all mandatory fields.

    Args:
        entry: Audit log entry to validate

    Returns:
        List of missing mandatory fields (empty if valid)
    """
    missing = []
    for field in MANDATORY_FIELDS:
        if field not in entry:
            # 'operation' can be derived from 'type' for backward compat
            if field == "operation" and "type" in entry:
                continue
            missing.append(field)
    return missing


def normalize_audit_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize an audit entry to ensure consistent field names.

    Maps legacy field names to Phase 3 standard:
    - 'type' -> 'operation' (if operation not present)

    Args:
        entry: Raw audit entry

    Returns:
        Normalized audit entry with consistent field names
    """
    normalized = entry.copy()

    # Map 'type' to 'operation' for backward compatibility
    if "operation" not in normalized and "type" in normalized:
        normalized["operation"] = normalized["type"]

    # Ensure timestamp is present
    if "timestamp" not in normalized:
        normalized["timestamp"] = datetime.utcnow().isoformat() + "Z"

    return normalized


# =============================================================================
# Audit Sink Interface
# =============================================================================

class AuditSink(ABC):
    """
    Abstract base class for audit log destinations.

    Implementations must handle:
    - Writing audit entries (synchronously or asynchronously)
    - Thread safety
    - Graceful failure (audit should not break the application)
    """

    @abstractmethod
    def write(self, entry: Dict[str, Any]) -> None:
        """
        Write an audit entry to the sink.

        Args:
            entry: Audit log entry (dict, will be serialized to JSON)

        Note:
            Implementations should be thread-safe and should NOT raise
            exceptions that would break the calling application.
        """
        pass

    @abstractmethod
    def flush(self) -> None:
        """
        Flush any buffered entries.

        Called when an audit context is closed.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the sink and release any resources.

        Called during application shutdown.
        """
        pass


# =============================================================================
# Stdout Audit Sink (Default)
# =============================================================================

class StdoutAuditSink(AuditSink):
    """
    Default audit sink that writes JSON to stdout.

    Suitable for:
    - Container/Kubernetes deployments (logs collected by orchestrator)
    - CloudWatch Logs, Datadog, or other log aggregators
    - Local development with JSON log viewing

    Thread-safe: Uses a lock to prevent interleaved output.
    """

    def __init__(self, pretty_print: bool = False):
        """
        Initialize stdout sink.

        Args:
            pretty_print: If True, format JSON with indentation (dev mode)
        """
        self._lock = threading.Lock()
        self._pretty_print = pretty_print

    def write(self, entry: Dict[str, Any]) -> None:
        """Write audit entry as JSON to stdout."""
        try:
            normalized = normalize_audit_entry(entry)

            if self._pretty_print:
                json_str = json.dumps(normalized, indent=2, default=str)
            else:
                json_str = json.dumps(normalized, default=str)

            with self._lock:
                print(json_str, flush=True)

        except Exception as e:
            # Never let audit failures break the application
            logger.warning(f"Failed to write audit entry to stdout: {e}")

    def flush(self) -> None:
        """Stdout is unbuffered when using print(), no-op."""
        pass

    def close(self) -> None:
        """No resources to release."""
        pass


# =============================================================================
# File Audit Sink (Local Development)
# =============================================================================

class FileAuditSink(AuditSink):
    """
    Audit sink that writes JSON lines to a file.

    Suitable for:
    - Local development and debugging
    - Audit log archival
    - Environments without log aggregation

    Features:
    - One JSON object per line (JSONL format)
    - Append mode (preserves existing logs)
    - Thread-safe writes
    - Automatic file rotation by size (optional)
    """

    def __init__(
        self,
        file_path: str,
        max_size_mb: Optional[float] = None,
        append: bool = True,
    ):
        """
        Initialize file sink.

        Args:
            file_path: Path to audit log file
            max_size_mb: Optional max file size in MB before rotation
            append: If True, append to existing file; if False, truncate
        """
        self._file_path = Path(file_path)
        self._max_size_bytes = int(max_size_mb * 1024 * 1024) if max_size_mb else None
        self._lock = threading.Lock()

        # Ensure parent directory exists
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        # Open file
        mode = "a" if append else "w"
        self._file = open(self._file_path, mode, encoding="utf-8")

        logger.debug(f"FileAuditSink initialized: {self._file_path}")

    def write(self, entry: Dict[str, Any]) -> None:
        """Write audit entry as JSON line to file."""
        try:
            normalized = normalize_audit_entry(entry)
            json_str = json.dumps(normalized, default=str)

            with self._lock:
                # Check for rotation
                if self._max_size_bytes and self._should_rotate():
                    self._rotate()

                self._file.write(json_str + "\n")
                self._file.flush()

        except Exception as e:
            logger.warning(f"Failed to write audit entry to file: {e}")

    def flush(self) -> None:
        """Flush file buffer."""
        with self._lock:
            try:
                self._file.flush()
            except Exception as e:
                logger.warning(f"Failed to flush audit file: {e}")

    def close(self) -> None:
        """Close the file handle."""
        with self._lock:
            try:
                self._file.close()
            except Exception as e:
                logger.warning(f"Failed to close audit file: {e}")

    def _should_rotate(self) -> bool:
        """Check if file should be rotated."""
        if not self._max_size_bytes:
            return False
        try:
            current_size = self._file_path.stat().st_size
            return current_size >= self._max_size_bytes
        except Exception:
            return False

    def _rotate(self) -> None:
        """Rotate the log file."""
        try:
            self._file.close()

            # Rename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            rotated_path = self._file_path.with_suffix(f".{timestamp}.jsonl")
            self._file_path.rename(rotated_path)

            # Open new file
            self._file = open(self._file_path, "w", encoding="utf-8")
            logger.info(f"Rotated audit log to: {rotated_path}")

        except Exception as e:
            logger.error(f"Failed to rotate audit log: {e}")
            # Try to reopen original
            self._file = open(self._file_path, "a", encoding="utf-8")


# =============================================================================
# Multi Audit Sink (Fan-out)
# =============================================================================

class MultiAuditSink(AuditSink):
    """
    Audit sink that writes to multiple destinations.

    Use for scenarios like:
    - Write to both stdout (for log aggregator) and file (for local backup)
    - Write to both development and production sinks during testing
    """

    def __init__(self, sinks: List[AuditSink]):
        """
        Initialize with list of sinks.

        Args:
            sinks: List of AuditSink instances to write to
        """
        self._sinks = sinks

    def write(self, entry: Dict[str, Any]) -> None:
        """Write to all sinks."""
        for sink in self._sinks:
            try:
                sink.write(entry)
            except Exception as e:
                logger.warning(f"Sink {type(sink).__name__} failed: {e}")

    def flush(self) -> None:
        """Flush all sinks."""
        for sink in self._sinks:
            try:
                sink.flush()
            except Exception as e:
                logger.warning(f"Failed to flush {type(sink).__name__}: {e}")

    def close(self) -> None:
        """Close all sinks."""
        for sink in self._sinks:
            try:
                sink.close()
            except Exception as e:
                logger.warning(f"Failed to close {type(sink).__name__}: {e}")


# =============================================================================
# Null Audit Sink (Testing/Disabled)
# =============================================================================

class NullAuditSink(AuditSink):
    """
    Audit sink that discards all entries.

    Use for:
    - Testing when audit output is not needed
    - Disabling audit without code changes
    """

    def write(self, entry: Dict[str, Any]) -> None:
        """Discard entry."""
        pass

    def flush(self) -> None:
        """No-op."""
        pass

    def close(self) -> None:
        """No-op."""
        pass


# =============================================================================
# Global Audit Sink Management
# =============================================================================

_default_audit_sink: Optional[AuditSink] = None
_sink_lock = threading.Lock()


def get_default_audit_sink() -> AuditSink:
    """
    Get or create the default audit sink.

    Configuration via environment:
    - BHT_AUDIT_SINK: "stdout" (default), "file", "null"
    - BHT_AUDIT_FILE_PATH: Path for file sink (default: ./logs/audit.jsonl)
    - BHT_AUDIT_PRETTY_PRINT: "true"/"false" for stdout (default: false)

    Returns:
        Default AuditSink instance
    """
    global _default_audit_sink

    if _default_audit_sink is None:
        with _sink_lock:
            if _default_audit_sink is None:
                _default_audit_sink = _create_sink_from_config()

    return _default_audit_sink


def set_default_audit_sink(sink: AuditSink) -> None:
    """
    Set the default audit sink.

    Use for:
    - Testing (inject mock sink)
    - Custom sink implementations

    Args:
        sink: AuditSink instance to use as default
    """
    global _default_audit_sink
    with _sink_lock:
        _default_audit_sink = sink


def reset_default_audit_sink() -> None:
    """Reset the default audit sink (for testing)."""
    global _default_audit_sink
    with _sink_lock:
        if _default_audit_sink is not None:
            try:
                _default_audit_sink.close()
            except Exception:
                pass
        _default_audit_sink = None


def _create_sink_from_config() -> AuditSink:
    """Create audit sink from environment configuration."""
    sink_type = os.getenv("BHT_AUDIT_SINK", "stdout").lower()

    if sink_type == "null" or sink_type == "none":
        return NullAuditSink()

    elif sink_type == "file":
        file_path = os.getenv("BHT_AUDIT_FILE_PATH", "./logs/audit.jsonl")
        max_size = float(os.getenv("BHT_AUDIT_FILE_MAX_SIZE_MB", "10"))
        return FileAuditSink(file_path, max_size_mb=max_size)

    else:  # Default: stdout
        pretty = os.getenv("BHT_AUDIT_PRETTY_PRINT", "false").lower() == "true"
        return StdoutAuditSink(pretty_print=pretty)
