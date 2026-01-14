# BHT Platform Phase 0 - Rollback Guide

## Overview

Phase 0 (Shim Layer + Audit-lite) is designed for **zero-risk deployment** with instant rollback capability. All platform features can be disabled with a single environment variable, restoring the system to pre-Phase 0 behavior.

## Feature Flags

### Master Kill Switch

| Flag | Default | Description |
|------|---------|-------------|
| `BHT_PLATFORM_ENABLED` | `true` | Master switch for all platform features |

When set to `false`:
- Middleware becomes a no-op (passes requests through unchanged)
- No `_trace` field added to any response
- No `X-Trace-Id` or `X-Request-Id` headers added
- No audit logging performed
- Zero observable behavior change from pre-Phase 0

### Response Control

| Flag | Default | Description |
|------|---------|-------------|
| `BHT_INCLUDE_TRACE_IN_RESPONSE` | `false` | Add `_trace` metadata to response bodies |

When `false` (default - **production safe**):
- Response bodies are unchanged from pre-Phase 0
- `X-Trace-Id` headers are still added (for observability)
- Audit logging still occurs internally

When `true` (opt-in for debugging):
- `_trace` field added to supported endpoints
- Contains `trace_id`, `request_id`, `workflow_id`
- Useful for debugging and correlation

### All Configuration Flags

| Flag | Default | Description |
|------|---------|-------------|
| `BHT_PLATFORM_ENABLED` | `true` | Master switch |
| `BHT_INCLUDE_TRACE_IN_RESPONSE` | `false` | Add `_trace` to responses |
| `BHT_ENABLE_GATEWAY_SHIM` | `true` | Enable ModelGatewayShim |
| `BHT_ENABLE_AUDIT_CONTEXT` | `true` | Enable AuditContext |
| `BHT_AUDIT_LOG_PROMPTS` | `false` | Log full prompts (privacy) |
| `BHT_AUDIT_LOG_RESPONSES` | `false` | Log full responses (privacy) |
| `BHT_STRUCTURED_LOGGING` | `true` | Use structured JSON logging |

## Rollback Procedure

### Immediate Rollback (Recommended)

To instantly disable all Phase 0 features without redeployment:

```bash
# Set environment variable
export BHT_PLATFORM_ENABLED=false

# Restart the service
# (varies by deployment - examples below)

# Docker
docker-compose restart api

# Kubernetes
kubectl rollout restart deployment/api

# Direct process
kill -HUP $(pgrep -f "uvicorn api.main")
```

### Response-Only Rollback

If you only need to remove `_trace` from responses but keep observability:

```bash
export BHT_INCLUDE_TRACE_IN_RESPONSE=false
# Restart service
```

This keeps:
- `X-Trace-Id` headers (for log correlation)
- Internal audit logging
- All platform tracing

But removes:
- `_trace` field from response bodies

### Complete Code Rollback

If needed, the Phase 0 changes can be fully reverted:

1. Remove middleware from `api/main.py`:
   ```python
   # Remove these lines:
   from platform.middleware import AuditContextMiddleware
   from platform.audit_context import AuditContext
   app.add_middleware(AuditContextMiddleware)
   ```

2. Remove `_trace` additions from endpoints:
   ```python
   # Remove _maybe_add_trace() calls
   # Remove ctx.get_trace_metadata() references
   ```

3. Remove platform package (optional):
   ```bash
   rm -rf platform/
   ```

## Verification

### Test Platform Disabled

```bash
export BHT_PLATFORM_ENABLED=false
curl http://localhost:8000/health
```

Expected response (no `_trace`):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "service": "DHCS BHT Multi-Agent API"
}
```

Expected headers (no trace headers):
```
Content-Type: application/json
```

### Test Platform Enabled (Trace Disabled)

```bash
export BHT_PLATFORM_ENABLED=true
export BHT_INCLUDE_TRACE_IN_RESPONSE=false
curl -i http://localhost:8000/health
```

Expected response (no `_trace`):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "service": "DHCS BHT Multi-Agent API"
}
```

Expected headers (trace headers present):
```
X-Trace-Id: 12345678-1234-5678-1234-567812345678
X-Request-Id: 87654321-4321-8765-4321-876543218765
Content-Type: application/json
```

### Test Full Trace

```bash
export BHT_PLATFORM_ENABLED=true
export BHT_INCLUDE_TRACE_IN_RESPONSE=true
curl http://localhost:8000/health
```

Expected response (with `_trace`):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "service": "DHCS BHT Multi-Agent API",
  "_trace": {
    "trace_id": "12345678-1234-5678-1234-567812345678",
    "request_id": "87654321-4321-8765-4321-876543218765",
    "workflow_id": "health_check"
  }
}
```

## Endpoint Behavior Summary

| Endpoint | Supports `_trace` | Notes |
|----------|------------------|-------|
| `GET /health` | ✅ | Health check |
| `POST /chat` | ✅ | Main orchestrator |
| `POST /curation/process` | ✅ | Policy curation |
| `POST /query` | ❌ | Not yet migrated |
| `POST /analytics` | ❌ | Not yet migrated |
| `POST /triage` | ❌ | Not yet migrated |
| `POST /recommendations` | ❌ | Not yet migrated |
| `POST /knowledge/search` | ❌ | Not yet migrated |
| `GET /knowledge/stats` | ❌ | Not yet migrated |
| `POST /curation/batch` | ❌ | Not yet migrated |
| `GET /curation/stats` | ❌ | Not yet migrated |
| `POST /curation/diagnose` | ❌ | Not yet migrated |

> Note: All endpoints still receive trace headers (`X-Trace-Id`) when platform is enabled.

## Monitoring

When platform is enabled, you can correlate logs using:

```bash
# Find all logs for a specific trace
grep "trace_id=12345678-1234-5678-1234-567812345678" /var/log/api.log
```

When platform is disabled:
- No trace IDs are generated
- Log correlation is not available
- System behaves as pre-Phase 0

## Contact

For issues with Phase 0:
1. First try: `BHT_PLATFORM_ENABLED=false` (instant rollback)
2. If issues persist: Full code rollback
3. Report issues to platform team
