"""
BHT Platform Audit Context

Phase 3: Full audit context with mandatory fields and sink integration.
Provides request-scoped tracing and compliance logging using ContextVar.

Features:
- Unique request_id and trace_id per request
- Mandatory fields across all log types (trace_id, request_id, workflow_id, operation, latency_ms, success)
- Structured audit logging via AuditSink abstraction
- LLM call metadata logging (no prompts by default)
- Retrieval call metadata logging
- Workflow step logging hooks

Privacy:
- Prompts/responses NOT logged by default (BHT_AUDIT_LOG_PROMPTS/RESPONSES=false)
- Only operational metadata logged for compliance
"""
import json
import logging
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from platform.config import get_platform_config

if TYPE_CHECKING:
    from platform.audit_sink import AuditSink

logger = logging.getLogger(__name__)

# Context variable for request-scoped audit context
_current_audit_context: ContextVar[Optional["AuditContext"]] = ContextVar(
    "bht_audit_context", default=None
)


# =============================================================================
# Mandatory Fields Definition
# =============================================================================

# Fields that MUST be present in every audit entry
MANDATORY_AUDIT_FIELDS = frozenset({
    "trace_id",
    "request_id",
    "workflow_id",
    "operation",  # Type: llm_call, retrieval, workflow_step, api_request
    "latency_ms",
    "success",
})

# Standard operation names for consistency
class AuditOperation:
    """Standard operation names for audit logs."""
    LLM_CALL = "llm_call"
    RETRIEVAL = "retrieval"
    WORKFLOW_STEP = "workflow_step"
    API_REQUEST = "api_request"


# =============================================================================
# Audit Context
# =============================================================================

@dataclass
class AuditContext:
    """
    Request-scoped audit context for tracing and compliance.

    Phase 3 Features:
    - Mandatory fields in all audit entries
    - AuditSink integration for flexible output destinations
    - Consistent operation naming across all log types
    - Workflow step hooks for orchestrator logging

    Usage:
        # Create context at request boundary (e.g., FastAPI middleware)
        with AuditContext.create(workflow_id="curation", tenant_id="county_la") as ctx:
            # All operations within this context inherit trace_id
            result = gateway.invoke(messages, audit_context=ctx)

        # Or get current context anywhere in the call stack
        ctx = AuditContext.current()
        ctx.log_llm_call(model="gpt-4o-mini", latency_ms=150, tokens=500)
    """

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default"
    workflow_id: str = "unknown"
    use_case: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)

    # Internal: accumulated audit entries (for get_audit_trail())
    _entries: List[Dict[str, Any]] = field(default_factory=list)
    _config: Any = field(default=None, repr=False)
    _sink: Optional["AuditSink"] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize configuration and sink references."""
        if self._config is None:
            self._config = get_platform_config()
        if self._sink is None:
            self._sink = _get_default_sink()

    @classmethod
    def create(
        cls,
        workflow_id: str = "unknown",
        tenant_id: str = "default",
        use_case: str = "",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        parent_trace_id: Optional[str] = None,
        sink: Optional["AuditSink"] = None,
    ) -> "AuditContext":
        """
        Create new audit context and set as current.

        Args:
            workflow_id: Workflow identifier (e.g., "curation", "crisis_intake")
            tenant_id: Tenant identifier (e.g., county code)
            use_case: Specific use case within workflow
            user_id: Optional user identifier
            session_id: Optional session identifier
            parent_trace_id: Optional parent trace for distributed tracing
            sink: Optional custom AuditSink (uses default if not provided)

        Returns:
            New AuditContext instance (also set as current)
        """
        ctx = cls(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            use_case=use_case,
            user_id=user_id,
            session_id=session_id,
            trace_id=parent_trace_id or str(uuid.uuid4()),
            _sink=sink,
        )
        _current_audit_context.set(ctx)
        return ctx

    @classmethod
    def current(cls) -> "AuditContext":
        """
        Get current audit context or create a default one.

        Returns:
            Current AuditContext from ContextVar, or new default instance
        """
        ctx = _current_audit_context.get()
        if ctx is None:
            # Create minimal context if none exists
            ctx = cls()
            _current_audit_context.set(ctx)
        return ctx

    @classmethod
    def get_current_trace_id(cls) -> str:
        """Get trace_id from current context, or generate a new one."""
        ctx = _current_audit_context.get()
        if ctx is not None:
            return ctx.trace_id
        return str(uuid.uuid4())

    def __enter__(self) -> "AuditContext":
        """Context manager entry - set as current context."""
        _current_audit_context.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - flush and clear context."""
        self.flush()
        _current_audit_context.set(None)

    # =========================================================================
    # Core Logging Methods
    # =========================================================================

    def _create_base_entry(self, operation: str, latency_ms: float, success: bool) -> Dict[str, Any]:
        """
        Create base audit entry with mandatory fields.

        Args:
            operation: Operation type (llm_call, retrieval, workflow_step, api_request)
            latency_ms: Operation latency in milliseconds
            success: Whether operation succeeded

        Returns:
            Dict with all mandatory fields populated
        """
        return {
            # Mandatory fields
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "workflow_id": self.workflow_id,
            "operation": operation,
            "latency_ms": round(latency_ms, 2),
            "success": success,
            # Standard metadata
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tenant_id": self.tenant_id,
        }

    def _emit_entry(self, entry: Dict[str, Any]) -> None:
        """
        Emit an audit entry through the sink.

        Args:
            entry: Complete audit entry
        """
        self._entries.append(entry)

        if self._sink:
            try:
                self._sink.write(entry)
            except Exception as e:
                # Never let audit failures break the application
                logger.warning(f"Failed to write audit entry: {e}")
        else:
            # Fallback to logger if no sink
            self._emit_log_fallback(entry)

    def _emit_log_fallback(self, entry: Dict[str, Any]) -> None:
        """
        Fallback log emission when no sink is available.

        Uses standard logging with JSON or human-readable format.
        """
        if self._config and self._config.structured_logging:
            logger.info(json.dumps(entry))
        else:
            log_msg = (
                f"[{entry['operation']}] trace_id={entry['trace_id']} "
                f"workflow={entry['workflow_id']} latency_ms={entry['latency_ms']}"
            )
            logger.info(log_msg)

    # Backward compatibility: _emit_log delegates to _emit_entry
    def _emit_log(self, entry: Dict[str, Any]) -> None:
        """Backward compatibility: emit log entry via sink or fallback."""
        self._emit_entry(entry)

    # =========================================================================
    # LLM Call Logging
    # =========================================================================

    def log_llm_call(
        self,
        model: str,
        latency_ms: float,
        tokens: int,
        operation: str = "invoke",
        success: bool = True,
        error: Optional[str] = None,
        error_type: Optional[str] = None,
        retries: int = 0,
        prompt_length: Optional[int] = None,
        response_length: Optional[int] = None,
        prompt: Optional[str] = None,
        response: Optional[str] = None,
    ) -> None:
        """
        Log LLM invocation metadata for audit trail.

        Args:
            model: Model identifier (e.g., "gpt-4o-mini")
            latency_ms: Invocation latency in milliseconds
            tokens: Estimated token usage
            operation: Sub-operation type (e.g., "invoke", "classify")
            success: Whether invocation succeeded
            error: Error message if failed
            error_type: Error classification (e.g., "timeout", "rate_limit")
            retries: Number of retry attempts
            prompt_length: Length of prompt in characters
            response_length: Length of response in characters
            prompt: Full prompt text (only logged if BHT_AUDIT_LOG_PROMPTS=true)
            response: Full response text (only logged if BHT_AUDIT_LOG_RESPONSES=true)
        """
        entry = self._create_base_entry(AuditOperation.LLM_CALL, latency_ms, success)

        # LLM-specific fields
        entry["model"] = model
        entry["tokens_estimate"] = tokens
        entry["sub_operation"] = operation  # Keep original operation as sub_operation
        entry["retries"] = retries

        if prompt_length is not None:
            entry["prompt_length"] = prompt_length
        if response_length is not None:
            entry["response_length"] = response_length
        if error:
            entry["error"] = error
        if error_type:
            entry["error_type"] = error_type

        # Only log full content if explicitly enabled (privacy protection)
        if self._config and self._config.audit_log_prompts and prompt:
            entry["prompt"] = prompt
        if self._config and self._config.audit_log_responses and response:
            entry["response"] = response

        self._emit_entry(entry)

    # =========================================================================
    # Retrieval Logging
    # =========================================================================

    def log_retrieval(
        self,
        query_length: int,
        n_results: int,
        latency_ms: float,
        strategy: str = "semantic",
        cache_hit: bool = False,
        success: bool = True,
        error: Optional[str] = None,
        error_type: Optional[str] = None,
    ) -> None:
        """
        Log retrieval operation metadata for audit trail.

        Args:
            query_length: Length of search query in characters
            n_results: Number of results returned
            latency_ms: Operation latency in milliseconds
            strategy: Search strategy used (semantic, keyword, hybrid)
            cache_hit: Whether result was from cache
            success: Whether retrieval succeeded
            error: Error message if failed
            error_type: Error classification
        """
        entry = self._create_base_entry(AuditOperation.RETRIEVAL, latency_ms, success)

        # Retrieval-specific fields
        entry["query_length"] = query_length
        entry["n_results"] = n_results
        entry["strategy"] = strategy
        entry["cache_hit"] = cache_hit

        if error:
            entry["error"] = error
        if error_type:
            entry["error_type"] = error_type

        self._emit_entry(entry)

    # =========================================================================
    # Workflow Step Logging
    # =========================================================================

    def log_workflow_step(
        self,
        step_name: str,
        latency_ms: float,
        success: bool = True,
        input_summary: Optional[str] = None,
        output_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        error_type: Optional[str] = None,
    ) -> None:
        """
        Log workflow step execution for audit trail.

        Use this for orchestrator-level logging of discrete workflow steps.

        Args:
            step_name: Name of workflow step (e.g., "evidence_extraction", "grounding")
            latency_ms: Step execution time in milliseconds
            success: Whether step succeeded
            input_summary: Brief summary of step input (no sensitive data)
            output_summary: Brief summary of step output (no sensitive data)
            metadata: Additional step metadata
            error: Error message if failed
            error_type: Error classification
        """
        entry = self._create_base_entry(AuditOperation.WORKFLOW_STEP, latency_ms, success)

        # Workflow step-specific fields
        entry["step_name"] = step_name

        if input_summary:
            entry["input_summary"] = input_summary
        if output_summary:
            entry["output_summary"] = output_summary
        if metadata:
            entry["step_metadata"] = metadata
        if error:
            entry["error"] = error
        if error_type:
            entry["error_type"] = error_type

        self._emit_entry(entry)

    # =========================================================================
    # API Request Logging
    # =========================================================================

    def log_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        error: Optional[str] = None,
        error_type: Optional[str] = None,
    ) -> None:
        """
        Log API request metadata for audit trail.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: Response status code
            latency_ms: Request processing time
            error: Error message if failed
            error_type: Error classification
        """
        success = 200 <= status_code < 400
        entry = self._create_base_entry(AuditOperation.API_REQUEST, latency_ms, success)

        # API request-specific fields
        entry["endpoint"] = endpoint
        entry["method"] = method
        entry["status_code"] = status_code

        if error:
            entry["error"] = error
        if error_type:
            entry["error_type"] = error_type

        self._emit_entry(entry)

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get all audit entries for this context."""
        return self._entries.copy()

    def get_trace_metadata(self) -> Dict[str, Any]:
        """
        Get trace metadata for inclusion in API responses.

        Returns minimal, safe metadata that can be returned to clients.
        """
        return {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "workflow_id": self.workflow_id,
        }

    def flush(self) -> None:
        """
        Flush any buffered audit entries.

        Called when the context manager exits.
        """
        total_latency_ms = (time.time() - self.start_time) * 1000

        if self._sink:
            try:
                self._sink.flush()
            except Exception as e:
                logger.warning(f"Failed to flush audit sink: {e}")

        logger.debug(
            f"Audit context complete: trace_id={self.trace_id}, "
            f"entries={len(self._entries)}, total_latency_ms={total_latency_ms:.2f}"
        )


# =============================================================================
# Workflow Step Timer (Convenience)
# =============================================================================

class WorkflowStepTimer:
    """
    Context manager for timing and logging workflow steps.

    Usage:
        with WorkflowStepTimer("evidence_extraction", audit_context=ctx) as step:
            # Do work
            step.set_metadata({"documents_processed": 5})

        # Automatically logs step with latency when exiting
    """

    def __init__(
        self,
        step_name: str,
        audit_context: Optional[AuditContext] = None,
        input_summary: Optional[str] = None,
    ):
        self.step_name = step_name
        self.ctx = audit_context or AuditContext.current()
        self.input_summary = input_summary
        self.output_summary: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self._start_time: float = 0
        self._success: bool = True
        self._error: Optional[str] = None
        self._error_type: Optional[str] = None

    def __enter__(self) -> "WorkflowStepTimer":
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        latency_ms = (time.time() - self._start_time) * 1000

        if exc_type is not None:
            self._success = False
            self._error = str(exc_val) if exc_val else str(exc_type.__name__)
            self._error_type = exc_type.__name__

        self.ctx.log_workflow_step(
            step_name=self.step_name,
            latency_ms=latency_ms,
            success=self._success,
            input_summary=self.input_summary,
            output_summary=self.output_summary,
            metadata=self.metadata if self.metadata else None,
            error=self._error,
            error_type=self._error_type,
        )

    def set_output_summary(self, summary: str) -> None:
        """Set output summary for the step."""
        self.output_summary = summary

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set additional metadata for the step."""
        self.metadata.update(metadata)

    def mark_failed(self, error: str, error_type: Optional[str] = None) -> None:
        """Mark the step as failed (without raising exception)."""
        self._success = False
        self._error = error
        self._error_type = error_type


# =============================================================================
# Sink Lazy Loading
# =============================================================================

def _get_default_sink() -> Optional["AuditSink"]:
    """Lazy load default audit sink to avoid circular imports."""
    try:
        from platform.audit_sink import get_default_audit_sink
        return get_default_audit_sink()
    except ImportError:
        return None
