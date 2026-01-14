"""
BHT Governed AI Platform - Core Primitives

This package provides platform-level abstractions for:
- Model Gateway: Centralized LLM access with routing, retry, and audit
- Retrieval Service: Unified document retrieval with citation tracking
- Audit Context: Request-scoped tracing and compliance logging
- Degradation Policy: Kill switches and fallback behaviors (future)

Phase 0: Shim layer wrapping existing implementations
Phase 1+: Full platform primitives with enhanced capabilities
"""

# Use lazy imports to avoid import errors when optional dependencies are missing
# This allows the platform package to be imported even in minimal environments

__all__ = [
    "AuditContext",
    "ModelGatewayShim",
    "BudgetTags",
    "RetrievalServiceShim",
    "PlatformConfig",
]

__version__ = "0.1.0"


def __getattr__(name):
    """Lazy import for platform components, with fallback to stdlib platform."""
    if name == "AuditContext":
        from platform.audit_context import AuditContext
        return AuditContext
    elif name == "ModelGatewayShim":
        from platform.model_gateway import ModelGatewayShim
        return ModelGatewayShim
    elif name == "BudgetTags":
        from platform.model_gateway import BudgetTags
        return BudgetTags
    elif name == "RetrievalServiceShim":
        from platform.retrieval_service import RetrievalServiceShim
        return RetrievalServiceShim
    elif name == "PlatformConfig":
        from platform.config import PlatformConfig
        return PlatformConfig

    # Fallback: delegate to stdlib platform module to avoid shadowing issues
    # Load stdlib platform module directly from its known location
    import importlib.util
    import sysconfig
    import os

    stdlib_path = sysconfig.get_paths()["stdlib"]
    platform_file = os.path.join(stdlib_path, "platform.py")

    if os.path.exists(platform_file):
        spec = importlib.util.spec_from_file_location("_stdlib_platform", platform_file)
        if spec and spec.loader:
            stdlib_platform = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(stdlib_platform)
            if hasattr(stdlib_platform, name):
                return getattr(stdlib_platform, name)

    raise AttributeError(f"module 'platform' has no attribute '{name}'")
