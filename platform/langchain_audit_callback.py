"""
BHT Platform LangChain Audit Callback

Provides a LangChain callback handler that automatically logs LLM calls
to the AuditSink via AuditContext. This enables audit correlation for
existing LangChain chains without requiring refactoring.

Usage:
    # Automatically included when using ModelGateway.get_underlying_llm()
    llm = gateway.get_underlying_llm()  # Callback already attached

    # Or manually attach to any LLM:
    from platform.langchain_audit_callback import get_audit_callback
    llm = ChatOpenAI(callbacks=[get_audit_callback()])
"""
import logging
import time
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


class AuditCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler for audit logging.

    Logs llm_call operations to AuditSink with mandatory fields:
    - trace_id, request_id, workflow_id (from current AuditContext)
    - operation: "llm_call"
    - latency_ms: measured from on_llm_start to on_llm_end
    - success: True/False based on completion vs error

    Privacy:
    - Prompts/responses NOT logged unless BHT_AUDIT_LOG_PROMPTS/RESPONSES=true
    """

    def __init__(self):
        super().__init__()
        # Track start times by run_id
        self._start_times: Dict[UUID, float] = {}
        self._prompts: Dict[UUID, str] = {}
        self._serialized: Dict[UUID, Dict[str, Any]] = {}

    @property
    def _config(self):
        """Lazy load config to avoid circular imports."""
        from platform.config import get_platform_config
        return get_platform_config()

    def _get_audit_context(self):
        """Get current audit context, or None if not available."""
        try:
            from platform.audit_context import AuditContext
            return AuditContext.current()
        except Exception:
            return None

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Record start time and prompt info when LLM call begins."""
        self._start_times[run_id] = time.time()
        self._prompts[run_id] = "\n".join(prompts) if prompts else ""
        self._serialized[run_id] = serialized or {}

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Log successful LLM call to audit."""
        start_time = self._start_times.pop(run_id, None)
        prompt = self._prompts.pop(run_id, "")
        serialized = self._serialized.pop(run_id, {})

        if start_time is None:
            return

        latency_ms = (time.time() - start_time) * 1000

        # Extract model name from serialized data
        model = "unknown"
        if "kwargs" in serialized:
            model = serialized["kwargs"].get("model", serialized["kwargs"].get("model_name", "unknown"))
        elif "name" in serialized:
            model = serialized.get("name", "unknown")

        # Extract response text
        response_text = ""
        tokens = 0
        if response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    response_text += gen.text if hasattr(gen, 'text') else str(gen)

        # Estimate tokens from llm_output if available
        if response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            tokens = token_usage.get("total_tokens", 0)

        # If no token info, estimate
        if tokens == 0:
            tokens = self._estimate_tokens(len(prompt), len(response_text))

        # Log to audit context
        ctx = self._get_audit_context()
        if ctx:
            log_kwargs = {
                "model": model,
                "latency_ms": latency_ms,
                "tokens": tokens,
                "operation": "chain",
                "success": True,
                "prompt_length": len(prompt),
                "response_length": len(response_text),
            }

            # Only include prompt/response if explicitly enabled
            if self._config.audit_log_prompts:
                log_kwargs["prompt"] = prompt
            if self._config.audit_log_responses:
                log_kwargs["response"] = response_text

            ctx.log_llm_call(**log_kwargs)

    def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Log failed LLM call to audit."""
        start_time = self._start_times.pop(run_id, None)
        prompt = self._prompts.pop(run_id, "")
        serialized = self._serialized.pop(run_id, {})

        if start_time is None:
            return

        latency_ms = (time.time() - start_time) * 1000

        # Extract model name
        model = "unknown"
        if "kwargs" in serialized:
            model = serialized["kwargs"].get("model", serialized["kwargs"].get("model_name", "unknown"))

        # Classify error
        error_type = self._classify_error(error)

        # Log to audit context
        ctx = self._get_audit_context()
        if ctx:
            ctx.log_llm_call(
                model=model,
                latency_ms=latency_ms,
                tokens=0,
                operation="chain",
                success=False,
                error=str(error),
                error_type=error_type,
                prompt_length=len(prompt),
            )

    def _estimate_tokens(self, prompt_length: int, response_length: int) -> int:
        """Estimate token count from character lengths."""
        # Rough estimate: ~4 chars per token for English
        return (prompt_length + response_length) // 4

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for audit logging."""
        error_str = str(type(error).__name__).lower()
        error_msg = str(error).lower()

        if "timeout" in error_str or "timeout" in error_msg:
            return "timeout"
        elif "rate" in error_msg or "429" in error_msg:
            return "rate_limit"
        elif "auth" in error_msg or "401" in error_msg or "403" in error_msg:
            return "auth_error"
        elif "connection" in error_str or "connection" in error_msg:
            return "connection_error"
        else:
            return "unknown"


# Singleton instance for reuse
_audit_callback: Optional[AuditCallbackHandler] = None


def get_audit_callback() -> AuditCallbackHandler:
    """
    Get the singleton audit callback handler.

    Returns:
        AuditCallbackHandler instance for use with LangChain LLMs
    """
    global _audit_callback
    if _audit_callback is None:
        _audit_callback = AuditCallbackHandler()
    return _audit_callback


def reset_audit_callback() -> None:
    """Reset the singleton callback (for testing)."""
    global _audit_callback
    _audit_callback = None
