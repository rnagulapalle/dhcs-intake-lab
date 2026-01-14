"""
BHT Platform Configuration

Centralized configuration for platform primitives.
Designed to coexist with existing agents/core/config.py during migration.
"""
from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class PlatformConfig:
    """
    Platform-level configuration.

    During Phase 0 (shim layer), most values are read from environment
    or delegate to existing settings. In later phases, this becomes
    the authoritative configuration source.
    """

    # Model Gateway Configuration
    primary_model: str = field(default_factory=lambda: os.getenv("BHT_PRIMARY_MODEL", "gpt-4o-mini"))
    fallback_model: Optional[str] = field(default_factory=lambda: os.getenv("BHT_FALLBACK_MODEL"))
    default_temperature: float = field(default_factory=lambda: float(os.getenv("BHT_DEFAULT_TEMPERATURE", "0.7")))
    default_max_tokens: int = field(default_factory=lambda: int(os.getenv("BHT_DEFAULT_MAX_TOKENS", "4096")))

    # Retry Configuration
    max_retries: int = field(default_factory=lambda: int(os.getenv("BHT_MAX_RETRIES", "3")))
    retry_base_delay: float = field(default_factory=lambda: float(os.getenv("BHT_RETRY_BASE_DELAY", "1.0")))
    retry_max_delay: float = field(default_factory=lambda: float(os.getenv("BHT_RETRY_MAX_DELAY", "30.0")))
    retry_jitter: float = field(default_factory=lambda: float(os.getenv("BHT_RETRY_JITTER", "0.1")))

    # Timeout Configuration
    default_timeout_seconds: float = field(default_factory=lambda: float(os.getenv("BHT_DEFAULT_TIMEOUT", "60.0")))

    # Circuit Breaker Configuration
    circuit_breaker_threshold: int = field(default_factory=lambda: int(os.getenv("BHT_CB_THRESHOLD", "5")))
    circuit_breaker_recovery_seconds: float = field(default_factory=lambda: float(os.getenv("BHT_CB_RECOVERY", "60.0")))
    circuit_breaker_half_open_max: int = field(default_factory=lambda: int(os.getenv("BHT_CB_HALF_OPEN_MAX", "1")))

    # Retrieval Configuration
    retrieval_cache_ttl_seconds: int = field(default_factory=lambda: int(os.getenv("BHT_RETRIEVAL_CACHE_TTL", "300")))
    default_retrieval_top_k: int = field(default_factory=lambda: int(os.getenv("BHT_RETRIEVAL_TOP_K", "5")))

    # Audit Configuration
    audit_log_prompts: bool = field(default_factory=lambda: os.getenv("BHT_AUDIT_LOG_PROMPTS", "false").lower() == "true")
    audit_log_responses: bool = field(default_factory=lambda: os.getenv("BHT_AUDIT_LOG_RESPONSES", "false").lower() == "true")
    structured_logging: bool = field(default_factory=lambda: os.getenv("BHT_STRUCTURED_LOGGING", "true").lower() == "true")

    # Phase 3: Logging Configuration
    json_logs_enabled: bool = field(default_factory=lambda: os.getenv("BHT_JSON_LOGS_ENABLED", "true").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("BHT_LOG_LEVEL", "INFO").upper())

    # Phase 3: Audit Sink Configuration
    audit_sink_type: str = field(default_factory=lambda: os.getenv("BHT_AUDIT_SINK", "stdout").lower())
    audit_file_path: str = field(default_factory=lambda: os.getenv("BHT_AUDIT_FILE_PATH", "./logs/audit.jsonl"))
    audit_file_max_size_mb: float = field(default_factory=lambda: float(os.getenv("BHT_AUDIT_FILE_MAX_SIZE_MB", "10")))

    # Feature Flags - Core
    enable_gateway_shim: bool = field(default_factory=lambda: os.getenv("BHT_ENABLE_GATEWAY_SHIM", "true").lower() == "true")
    enable_audit_context: bool = field(default_factory=lambda: os.getenv("BHT_ENABLE_AUDIT_CONTEXT", "true").lower() == "true")

    # Feature Flags - Reliability (Phase 1: all disabled by default for zero behavior change)
    model_timeout_enabled: bool = field(default_factory=lambda: os.getenv("BHT_MODEL_TIMEOUT_ENABLED", "false").lower() == "true")
    model_retry_enabled: bool = field(default_factory=lambda: os.getenv("BHT_MODEL_RETRY_ENABLED", "false").lower() == "true")
    circuit_breaker_enabled: bool = field(default_factory=lambda: os.getenv("BHT_CIRCUIT_BREAKER_ENABLED", "false").lower() == "true")

    # Feature Flag - Use centralized gateway for all agents (Phase 1)
    # Default: TRUE - all agents use ModelGateway for centralized LLM access
    # Set BHT_USE_CENTRALIZED_GATEWAY=false only for rollback/debugging
    use_centralized_gateway: bool = field(default_factory=lambda: os.getenv("BHT_USE_CENTRALIZED_GATEWAY", "true").lower() == "true")

    # Response modification flags (for backward compatibility)
    # When False, _trace field is NOT added to API responses (production default)
    include_trace_in_response: bool = field(default_factory=lambda: os.getenv("BHT_INCLUDE_TRACE_IN_RESPONSE", "false").lower() == "true")

    # Master kill switch - when False, all platform features are disabled
    # Middleware becomes no-op, shims pass-through directly
    platform_enabled: bool = field(default_factory=lambda: os.getenv("BHT_PLATFORM_ENABLED", "true").lower() == "true")

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.default_timeout_seconds <= 0:
            raise ValueError("default_timeout_seconds must be positive")


# Global platform config instance (lazy initialization)
_platform_config: Optional[PlatformConfig] = None


def get_platform_config() -> PlatformConfig:
    """Get or create the global platform configuration."""
    global _platform_config
    if _platform_config is None:
        _platform_config = PlatformConfig()
    return _platform_config
