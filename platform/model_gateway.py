"""
BHT Platform Model Gateway

Phase 1: Real implementation with reliability features.
Provides centralized LLM access with:
- Timeout enforcement (optional, disabled by default)
- Retry with exponential backoff (optional, disabled by default)
- Circuit breaker (optional, disabled by default)
- Audit logging for all operations

Default behavior is identical to Phase 0 (shim layer).
Reliability features are opt-in via feature flags.
"""
import logging
import random
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from platform.audit_context import AuditContext
from platform.config import PlatformConfig, get_platform_config
from platform.errors import (
    ModelGatewayError,
    ModelTimeoutError,
    ModelRateLimitError,
    CircuitBreakerOpenError,
    ModelRetryExhaustedError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class BudgetTags:
    """
    Budget tracking tags for cost attribution.

    Used for audit logging and future cost enforcement.
    """
    tenant_id: str = "default"
    workflow_id: str = "unknown"
    operation: str = "invoke"
    use_case: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        result = {
            "tenant_id": self.tenant_id,
            "workflow_id": self.workflow_id,
            "operation": self.operation,
        }
        if self.use_case:
            result["use_case"] = self.use_case
        return result


@dataclass
class ModelInvocationResult:
    """
    Result of a model invocation.

    Wraps the LLM response with metadata for audit and debugging.
    """
    content: str
    model_used: str
    latency_ms: float
    tokens_estimate: int
    trace_id: str
    success: bool = True
    error: Optional[str] = None
    retries: int = 0
    error_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "content": self.content,
            "model_used": self.model_used,
            "latency_ms": self.latency_ms,
            "tokens_estimate": self.tokens_estimate,
            "trace_id": self.trace_id,
            "success": self.success,
            "error": self.error,
            "retries": self.retries,
        }


# =============================================================================
# Circuit Breaker
# =============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Thread-safe circuit breaker implementation.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests rejected immediately
    - HALF_OPEN: Testing recovery, limited requests allowed

    Feature flag: BHT_CIRCUIT_BREAKER_ENABLED (default: false)
    When disabled, all methods are no-ops.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1,
        enabled: bool = False,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.enabled = enabled

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state (with automatic state transitions)."""
        if not self.enabled:
            return CircuitState.CLOSED

        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self._last_failure_time and \
                   (time.time() - self._last_failure_time) >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
            return self._state

    def can_execute(self) -> bool:
        """Check if request can proceed."""
        if not self.enabled:
            return True

        state = self.state  # This may trigger state transition

        with self._lock:
            if state == CircuitState.CLOSED:
                return True
            elif state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
            else:  # OPEN
                return False

    def record_success(self) -> None:
        """Record successful execution."""
        if not self.enabled:
            return

        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                # Success in half-open means service recovered
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._half_open_calls = 0
                logger.info("Circuit breaker CLOSED (service recovered)")
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    def record_failure(self) -> None:
        """Record failed execution."""
        if not self.enabled:
            return

        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Failure in half-open means service still failing
                self._state = CircuitState.OPEN
                logger.warning("Circuit breaker OPEN (half-open test failed)")
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(
                        f"Circuit breaker OPEN (threshold {self.failure_threshold} reached)"
                    )

    def get_recovery_time(self) -> Optional[float]:
        """Get time until circuit might close (for error messages)."""
        if not self.enabled or self._state != CircuitState.OPEN:
            return None
        if self._last_failure_time:
            return max(0, self.recovery_timeout - (time.time() - self._last_failure_time))
        return self.recovery_timeout

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0


# =============================================================================
# Model Gateway
# =============================================================================

class ModelGateway:
    """
    Centralized Model Gateway for all LLM operations.

    Features:
    - Unified interface for all model invocations
    - Audit logging with trace propagation
    - Timeout enforcement (optional, BHT_MODEL_TIMEOUT_ENABLED)
    - Retry with exponential backoff (optional, BHT_MODEL_RETRY_ENABLED)
    - Circuit breaker (optional, BHT_CIRCUIT_BREAKER_ENABLED)

    Default behavior is identical to direct ChatOpenAI usage.
    All reliability features are opt-in via feature flags.

    Usage:
        gateway = ModelGateway(model="gpt-4o-mini", temperature=0.7)
        result = gateway.invoke("Hello")
        print(result.content)
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        openai_api_key: Optional[str] = None,
        max_tokens: Optional[int] = None,
        config: Optional[PlatformConfig] = None,
        llm: Optional[ChatOpenAI] = None,
    ):
        """
        Initialize the model gateway.

        Args:
            model: Model name (defaults to platform config)
            temperature: Temperature setting (defaults to platform config)
            openai_api_key: OpenAI API key (required if llm not provided)
            max_tokens: Max tokens for response
            config: Platform configuration
            llm: Existing ChatOpenAI instance to wrap (for migration)
        """
        self.config = config or get_platform_config()

        if llm is not None:
            self._llm = llm
            self.model = getattr(llm, 'model_name', getattr(llm, 'model', 'unknown'))
            self.temperature = getattr(llm, 'temperature', 0.7)
        else:
            self.model = model or self.config.primary_model
            self.temperature = temperature if temperature is not None else self.config.default_temperature

            if openai_api_key is None:
                from agents.core.config import settings
                openai_api_key = settings.openai_api_key

            llm_kwargs = {
                "model": self.model,
                "temperature": self.temperature,
                "openai_api_key": openai_api_key,
            }
            if max_tokens is not None:
                llm_kwargs["max_tokens"] = max_tokens

            self._llm = ChatOpenAI(**llm_kwargs)

        # Initialize circuit breaker
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_threshold,
            recovery_timeout=self.config.circuit_breaker_recovery_seconds,
            half_open_max_calls=self.config.circuit_breaker_half_open_max,
            enabled=self.config.circuit_breaker_enabled,
        )

        # Thread pool for timeout enforcement
        self._executor: Optional[ThreadPoolExecutor] = None

        logger.debug(
            f"ModelGateway initialized: model={self.model}, "
            f"timeout_enabled={self.config.model_timeout_enabled}, "
            f"retry_enabled={self.config.model_retry_enabled}, "
            f"circuit_breaker_enabled={self.config.circuit_breaker_enabled}"
        )

    def invoke(
        self,
        messages: Union[List[BaseMessage], List[Dict[str, str]], str],
        budget_tags: Optional[BudgetTags] = None,
        audit_context: Optional[AuditContext] = None,
        timeout: Optional[float] = None,
    ) -> ModelInvocationResult:
        """
        Invoke the model with optional reliability features.

        Args:
            messages: Messages to send to model
            budget_tags: Cost attribution tags (optional)
            audit_context: Audit context for tracing (uses current if not provided)
            timeout: Override timeout (uses config default if not provided)

        Returns:
            ModelInvocationResult with response and metadata

        Raises:
            ModelGatewayError: On invocation failure
            ModelTimeoutError: If timeout enabled and exceeded
            CircuitBreakerOpenError: If circuit breaker is open
            ModelRetryExhaustedError: If retry enabled and all attempts fail
        """
        audit = audit_context or AuditContext.current()
        tags = budget_tags or BudgetTags(workflow_id=audit.workflow_id)

        normalized_messages = self._normalize_messages(messages)
        prompt_length = sum(len(str(m.content)) for m in normalized_messages)

        # Check circuit breaker
        if self.config.circuit_breaker_enabled and not self._circuit_breaker.can_execute():
            recovery_time = self._circuit_breaker.get_recovery_time()
            error = CircuitBreakerOpenError(
                "Circuit breaker is open, request rejected",
                recovery_time=recovery_time
            )
            # Log the rejection
            audit.log_llm_call(
                model=self.model,
                latency_ms=0,
                tokens=0,
                operation=tags.operation,
                success=False,
                error=str(error),
                error_type="circuit_breaker_open",
            )
            raise error

        # Determine effective timeout
        effective_timeout = None
        if self.config.model_timeout_enabled:
            effective_timeout = timeout or self.config.default_timeout_seconds

        start_time = time.time()
        retries = 0
        last_error: Optional[Exception] = None
        response_content = ""
        success = False
        error_type: Optional[str] = None

        # Determine max attempts
        max_attempts = 1
        if self.config.model_retry_enabled:
            max_attempts = self.config.max_retries + 1  # +1 for initial attempt

        for attempt in range(max_attempts):
            if attempt > 0:
                retries = attempt
                delay = self._calculate_retry_delay(attempt)
                logger.info(f"Retry attempt {attempt}/{self.config.max_retries} after {delay:.2f}s delay")
                time.sleep(delay)

            try:
                if effective_timeout:
                    response_content = self._invoke_with_timeout(
                        normalized_messages, effective_timeout
                    )
                else:
                    response = self._llm.invoke(normalized_messages)
                    response_content = response.content

                success = True
                self._circuit_breaker.record_success()
                break

            except FuturesTimeoutError:
                last_error = ModelTimeoutError(
                    f"Model invocation timed out after {effective_timeout}s",
                    timeout_seconds=effective_timeout
                )
                error_type = "timeout"
                self._circuit_breaker.record_failure()

            except Exception as e:
                last_error = e
                error_type = self._classify_error(e)
                self._circuit_breaker.record_failure()

                # Only retry on transient errors
                if not self._is_retryable(e):
                    break

        latency_ms = (time.time() - start_time) * 1000
        tokens_estimate = self._estimate_tokens(prompt_length, len(response_content))

        # Log to audit context
        audit.log_llm_call(
            model=self.model,
            latency_ms=latency_ms,
            tokens=tokens_estimate,
            operation=tags.operation,
            success=success,
            error=str(last_error) if last_error else None,
            error_type=error_type,
            prompt_length=prompt_length,
            response_length=len(response_content),
            retries=retries,
        )

        if not success:
            if retries > 0 and self.config.model_retry_enabled:
                raise ModelRetryExhaustedError(
                    f"All {max_attempts} attempts failed",
                    attempts=max_attempts,
                    last_error=str(last_error),
                )
            elif isinstance(last_error, ModelGatewayError):
                raise last_error
            else:
                raise ModelGatewayError(f"Model invocation failed: {last_error}")

        return ModelInvocationResult(
            content=response_content,
            model_used=self.model,
            latency_ms=latency_ms,
            tokens_estimate=tokens_estimate,
            trace_id=audit.trace_id,
            success=True,
            retries=retries,
        )

    def invoke_raw(
        self,
        messages: Union[List[BaseMessage], List[Dict[str, str]], str],
        budget_tags: Optional[BudgetTags] = None,
        audit_context: Optional[AuditContext] = None,
    ) -> Any:
        """
        Invoke the model and return raw LangChain response.

        This method provides pass-through behavior for compatibility.
        Note: Does NOT apply timeout/retry/circuit breaker (direct invocation).

        Args:
            messages: Messages to send to model
            budget_tags: Cost attribution tags (optional)
            audit_context: Audit context for tracing

        Returns:
            Raw LangChain response (AIMessage or similar)
        """
        audit = audit_context or AuditContext.current()
        tags = budget_tags or BudgetTags(workflow_id=audit.workflow_id)

        normalized_messages = self._normalize_messages(messages)
        prompt_length = sum(len(str(m.content)) for m in normalized_messages)

        start_time = time.time()
        error_msg = None
        response = None

        try:
            response = self._llm.invoke(normalized_messages)
            success = True
            response_length = len(response.content) if hasattr(response, 'content') else 0

        except Exception as e:
            error_msg = str(e)
            success = False
            response_length = 0
            raise

        finally:
            latency_ms = (time.time() - start_time) * 1000
            tokens_estimate = self._estimate_tokens(prompt_length, response_length)

            audit.log_llm_call(
                model=self.model,
                latency_ms=latency_ms,
                tokens=tokens_estimate,
                operation=tags.operation,
                success=success,
                error=error_msg,
                prompt_length=prompt_length,
                response_length=response_length,
            )

        return response

    def get_underlying_llm(self, with_audit_callback: bool = True) -> ChatOpenAI:
        """
        Get the underlying ChatOpenAI instance with audit callback attached.

        Use this for compatibility with LangChain chains. The returned LLM
        will automatically log llm_call operations to the AuditSink via
        AuditContext.current().

        Args:
            with_audit_callback: If True (default), attach audit callback for
                automatic llm_call logging. Set False to get raw LLM.

        Returns:
            ChatOpenAI instance, optionally with audit callback
        """
        if not with_audit_callback:
            return self._llm

        # Attach audit callback for automatic logging
        from platform.langchain_audit_callback import get_audit_callback
        callback = get_audit_callback()

        # Check if callback already attached
        existing_callbacks = getattr(self._llm, 'callbacks', None) or []
        if callback in existing_callbacks:
            return self._llm

        # Create a copy with the callback attached
        # We use with_config to avoid mutating the original LLM
        return self._llm.with_config(callbacks=[callback])

    def _invoke_with_timeout(self, messages: List[BaseMessage], timeout: float) -> str:
        """Execute LLM invocation with timeout enforcement."""
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=4)

        future = self._executor.submit(self._llm.invoke, messages)
        try:
            response = future.result(timeout=timeout)
            return response.content
        except FuturesTimeoutError:
            future.cancel()
            raise

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt using exponential backoff with jitter."""
        base_delay = self.config.retry_base_delay
        max_delay = self.config.retry_max_delay
        jitter = self.config.retry_jitter

        # Exponential backoff: base * 2^attempt
        delay = base_delay * (2 ** attempt)
        delay = min(delay, max_delay)

        # Add jitter (±jitter%)
        jitter_amount = delay * jitter * (2 * random.random() - 1)
        delay += jitter_amount

        return max(0, delay)

    def _is_retryable(self, error: Exception) -> bool:
        """Determine if an error is retryable."""
        error_str = str(error).lower()

        # Retryable conditions
        retryable_patterns = [
            "rate limit",
            "timeout",
            "connection",
            "temporary",
            "503",
            "502",
            "504",
            "overloaded",
            "capacity",
        ]

        # Non-retryable conditions
        non_retryable_patterns = [
            "invalid api key",
            "authentication",
            "authorization",
            "invalid request",
            "400",
            "401",
            "403",
            "404",
        ]

        for pattern in non_retryable_patterns:
            if pattern in error_str:
                return False

        for pattern in retryable_patterns:
            if pattern in error_str:
                return True

        # Default: retry on unknown errors (conservative)
        return True

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for audit logging."""
        error_str = str(error).lower()

        if "rate limit" in error_str:
            return "rate_limit"
        elif "timeout" in error_str:
            return "timeout"
        elif "connection" in error_str:
            return "connection_error"
        elif "authentication" in error_str or "api key" in error_str:
            return "auth_error"
        elif "invalid" in error_str:
            return "invalid_request"
        else:
            return "unknown"

    def _normalize_messages(
        self,
        messages: Union[List[BaseMessage], List[Dict[str, str]], str]
    ) -> List[BaseMessage]:
        """Normalize various message formats to LangChain BaseMessage list."""
        if isinstance(messages, str):
            return [HumanMessage(content=messages)]

        if not messages:
            return []

        if isinstance(messages[0], BaseMessage):
            return messages

        normalized = []
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "system":
                    normalized.append(SystemMessage(content=content))
                elif role == "assistant":
                    normalized.append(AIMessage(content=content))
                else:
                    normalized.append(HumanMessage(content=content))
            elif isinstance(msg, BaseMessage):
                normalized.append(msg)

        return normalized

    def _estimate_tokens(self, prompt_length: int, response_length: int) -> int:
        """Estimate token count from character lengths."""
        return (prompt_length + response_length) // 4

    # LangChain compatibility methods
    def __or__(self, other):
        """Support pipe operator for LangChain chains."""
        return self._llm | other

    def __ror__(self, other):
        """Support reverse pipe operator for LangChain chains."""
        return other | self._llm


# =============================================================================
# Backward Compatibility Alias
# =============================================================================

# Alias for backward compatibility with Phase 0 code
ModelGatewayShim = ModelGateway


# =============================================================================
# Singleton Gateway
# =============================================================================

_default_gateway: Optional[ModelGateway] = None
_gateway_lock = threading.Lock()


def get_default_gateway() -> ModelGateway:
    """
    Get or create the default singleton ModelGateway.

    Used when agents don't have a gateway injected.
    Thread-safe initialization.
    """
    global _default_gateway

    if _default_gateway is None:
        with _gateway_lock:
            if _default_gateway is None:
                _default_gateway = create_gateway_from_settings()

    return _default_gateway


def reset_default_gateway() -> None:
    """Reset the default gateway (for testing)."""
    global _default_gateway
    with _gateway_lock:
        _default_gateway = None


# =============================================================================
# Factory Functions
# =============================================================================

def create_gateway_from_settings(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> ModelGateway:
    """
    Factory function to create a ModelGateway using existing settings.

    Args:
        model: Override model (uses settings.agent_model if not provided)
        temperature: Override temperature (uses settings.agent_temperature if not provided)

    Returns:
        Configured ModelGateway instance
    """
    from agents.core.config import settings

    return ModelGateway(
        model=model or settings.agent_model,
        temperature=temperature if temperature is not None else settings.agent_temperature,
        openai_api_key=settings.openai_api_key,
    )


def wrap_existing_llm(llm: ChatOpenAI) -> ModelGateway:
    """
    Wrap an existing ChatOpenAI instance with ModelGateway.

    Use this for gradual migration of existing code.

    Args:
        llm: Existing ChatOpenAI instance

    Returns:
        ModelGateway wrapping the existing instance
    """
    return ModelGateway(llm=llm)
