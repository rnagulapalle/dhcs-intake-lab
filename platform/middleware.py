"""
BHT Platform Middleware

FastAPI middleware for request-scoped audit context and tracing.

Feature Flags:
- BHT_PLATFORM_ENABLED: Master switch (default: true). When false, middleware is no-op.
- BHT_INCLUDE_TRACE_IN_RESPONSE: When true, adds X-Trace-Id headers (default: true when platform enabled)
"""
import time
import logging
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from platform.audit_context import AuditContext
from platform.config import get_platform_config

logger = logging.getLogger(__name__)


class AuditContextMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that creates AuditContext for each request.

    Features:
    - Creates unique trace_id and request_id per request
    - Propagates trace_id from X-Trace-Id header if present
    - Extracts workflow_id from request path
    - Adds trace metadata to response headers
    - Logs request completion with latency

    Usage:
        from fastapi import FastAPI
        from platform.middleware import AuditContextMiddleware

        app = FastAPI()
        app.add_middleware(AuditContextMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with audit context.

        When BHT_PLATFORM_ENABLED=false, this middleware is a no-op pass-through.
        """
        config = get_platform_config()

        # Master kill switch - if platform disabled, pass through directly
        if not config.platform_enabled:
            return await call_next(request)

        start_time = time.time()

        # Extract trace_id from header if provided (for distributed tracing)
        parent_trace_id = request.headers.get("X-Trace-Id")

        # Extract workflow from path
        workflow_id = self._extract_workflow_id(request.url.path)

        # Extract tenant from header or default
        tenant_id = request.headers.get("X-Tenant-Id", "default")

        # Create audit context for this request
        with AuditContext.create(
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            parent_trace_id=parent_trace_id,
        ) as audit_ctx:
            # Process request
            try:
                response = await call_next(request)
                status_code = response.status_code

            except Exception as e:
                logger.error(f"Request failed: {e}", exc_info=True)
                status_code = 500
                raise

            finally:
                latency_ms = (time.time() - start_time) * 1000

                # Log API request
                audit_ctx.log_api_request(
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=status_code,
                    latency_ms=latency_ms,
                )

            # Add trace metadata to response headers (always, for observability)
            response.headers["X-Trace-Id"] = audit_ctx.trace_id
            response.headers["X-Request-Id"] = audit_ctx.request_id

            return response

    def _extract_workflow_id(self, path: str) -> str:
        """
        Extract workflow identifier from request path.

        Maps API paths to workflow identifiers for audit grouping.
        """
        path_lower = path.lower()

        if "/curation" in path_lower:
            return "curation"
        elif "/chat" in path_lower:
            return "crisis_intake"
        elif "/query" in path_lower:
            return "crisis_query"
        elif "/analytics" in path_lower:
            return "crisis_analytics"
        elif "/triage" in path_lower:
            return "crisis_triage"
        elif "/recommendations" in path_lower:
            return "crisis_recommendations"
        elif "/knowledge" in path_lower:
            return "knowledge_search"
        elif "/health" in path_lower:
            return "health_check"
        else:
            return "unknown"


def get_audit_context_from_request(request: Request) -> Optional[AuditContext]:
    """
    Get current audit context (for use in route handlers).

    Usage:
        @app.post("/my-endpoint")
        async def my_endpoint(request: Request):
            ctx = get_audit_context_from_request(request)
            # ctx is now available with trace_id, etc.
    """
    return AuditContext.current()
