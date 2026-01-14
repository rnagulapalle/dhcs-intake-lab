"""
BHT Platform Error Taxonomy

Standardized error types for platform operations.
Provides structured error handling across all platform primitives.
"""
from typing import Optional, Dict, Any


class BHTPlatformError(Exception):
    """Base exception for all BHT platform errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "BHT_PLATFORM_ERROR"
        self.details = details or {}
        self.recoverable = recoverable

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
        }


# Model Gateway Errors

class ModelGatewayError(BHTPlatformError):
    """Base error for model gateway operations."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="BHT_MODEL_GATEWAY_ERROR",
            details=details,
            recoverable=True
        )


class ModelTimeoutError(ModelGatewayError):
    """Model invocation timed out."""

    def __init__(self, message: str, timeout_seconds: float, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["timeout_seconds"] = timeout_seconds
        super().__init__(message=message, details=details)
        self.error_code = "BHT_MODEL_TIMEOUT"


class ModelRateLimitError(ModelGatewayError):
    """Rate limit exceeded for model API."""

    def __init__(self, message: str, retry_after: Optional[float] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(message=message, details=details)
        self.error_code = "BHT_MODEL_RATE_LIMIT"


class ModelUnavailableError(ModelGatewayError):
    """Model service is unavailable."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.error_code = "BHT_MODEL_UNAVAILABLE"
        self.recoverable = False


class CircuitBreakerOpenError(ModelGatewayError):
    """Circuit breaker is open, requests are being rejected."""

    def __init__(self, message: str, recovery_time: Optional[float] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if recovery_time:
            details["recovery_time_seconds"] = recovery_time
        super().__init__(message=message, details=details)
        self.error_code = "BHT_CIRCUIT_BREAKER_OPEN"
        self.recoverable = True  # Will recover after timeout


class ModelRetryExhaustedError(ModelGatewayError):
    """All retry attempts exhausted."""

    def __init__(self, message: str, attempts: int, last_error: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["attempts"] = attempts
        if last_error:
            details["last_error"] = last_error
        super().__init__(message=message, details=details)
        self.error_code = "BHT_MODEL_RETRY_EXHAUSTED"


# Retrieval Service Errors

class RetrievalError(BHTPlatformError):
    """Base error for retrieval operations."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="BHT_RETRIEVAL_ERROR",
            details=details,
            recoverable=True
        )


class RetrievalTimeoutError(RetrievalError):
    """Retrieval operation timed out."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.error_code = "BHT_RETRIEVAL_TIMEOUT"


class KnowledgeBaseUnavailableError(RetrievalError):
    """Knowledge base is unavailable."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.error_code = "BHT_KB_UNAVAILABLE"
        self.recoverable = False


# Audit Context Errors

class AuditError(BHTPlatformError):
    """Error in audit/tracing operations."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="BHT_AUDIT_ERROR",
            details=details,
            recoverable=True  # Audit errors should not block operations
        )


# Degradation/Kill Switch Errors (for future use)

class ServiceDegradedError(BHTPlatformError):
    """Service is in degraded mode."""

    def __init__(self, message: str, degradation_level: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["degradation_level"] = degradation_level
        super().__init__(
            message=message,
            error_code="BHT_SERVICE_DEGRADED",
            details=details,
            recoverable=False
        )


class ServiceKilledError(BHTPlatformError):
    """Service has been killed via kill switch."""

    def __init__(self, message: str, workflow_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if workflow_id:
            details["workflow_id"] = workflow_id
        super().__init__(
            message=message,
            error_code="BHT_SERVICE_KILLED",
            details=details,
            recoverable=False
        )
