# Docker Compose Verification Report

**Date:** 2026-01-14
**Status:** ✅ PASS
**Last Verified:** 2026-01-14T17:05:05Z

---

## 1. Inventory

| File | Path | Purpose |
|------|------|---------|
| docker-compose.yml | `./docker-compose.yml` | Main compose orchestration |
| api/Dockerfile | `./api/Dockerfile` | API service (multi-stage build, non-root) |
| .dockerignore | `./.dockerignore` | Build exclusions |
| Makefile | `./Makefile` | Build/run targets |

### Compose Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| (default) | agent-api | Development, API-only (stdout logging) |
| test | agent-api-test, smoke-test | Automated smoke testing (file-based audit) |
| infra | zookeeper, kafka, pinot-* | Full infrastructure |
| generator | generator | Data generation |
| dashboard | dashboard | UI |
| full | All services | Full stack |

---

## 2. Docker Verification Summary

| Check | Status | Evidence |
|-------|--------|----------|
| Image pinning | ✅ PASS | `confluentinc/cp-kafka:7.6.1`, `apachepinot/pinot:1.1.0`, `curlimages/curl:8.5.0` |
| Healthchecks | ✅ PASS | `healthcheck:` block in agent-api, kafka, zookeeper, pinot-* |
| Non-root | ✅ PASS | `USER bht` (uid/gid 1000) in api/Dockerfile |
| Secrets via env | ✅ PASS | `OPENAI_API_KEY: ${OPENAI_API_KEY:?OPENAI_API_KEY is required}` |
| Stdout logging | ✅ PASS | `BHT_AUDIT_SINK: stdout`, no log file mounts |

### Hygiene Evidence

```yaml
# From docker-compose.yml (secrets NOT expanded)
environment:
  OPENAI_API_KEY: ${OPENAI_API_KEY:?OPENAI_API_KEY is required}  # Via env only ✓
  BHT_AUDIT_SINK: stdout  # Stdout logging ✓
  BHT_SMOKE_ENDPOINT_ENABLED: "true"  # Smoke endpoint enabled
```

```dockerfile
# From api/Dockerfile
RUN groupadd --gid 1000 bht && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home bht
USER bht  # Non-root ✓
```

---

## 3. Test Cases Executed

| Test Case | Description | Result | Evidence |
|-----------|-------------|--------|----------|
| Health check | /health endpoint returns 200 | ✅ PASS | `{"status":"healthy",...}` |
| Single-request correlation | /smoke/correlate triggers retrieval + llm_call + api_request with SAME trace_id | ✅ PASS | trace_id `b02af316-80b2-48f4-a144-2b3c5a2ceecd` in all 3 operations |
| Smoke runner | Compose smoke-test exits 0 | ✅ PASS | `smoke-test exited with code 0` |

---

## 4. Single-Request Audit Correlation Evidence (CRITICAL)

### Request
```bash
POST /smoke/correlate
{"query":"What are the crisis response protocols?"}
```

### Response
```json
{
  "success": true,
  "trace_id": "351f09cb-1dd8-464a-991c-a6d52b599e0f",
  "retrieval_count": 3,
  "llm_summary": "Mobile crisis teams are mandated to provide immediate in-person cr..."
}
```

### Audit Logs (Same trace_id in ALL THREE operations)

**retrieval:**
```json
{"trace_id": "351f09cb-1dd8-464a-991c-a6d52b599e0f", "request_id": "f6a5ef11-5143-488a-8513-93638123c0a6", "workflow_id": "unknown", "operation": "retrieval", "latency_ms": 2013.36, "success": true, "timestamp": "2026-01-14T17:05:03.272825Z", "tenant_id": "default", "query_length": 39, "n_results": 3, "strategy": "semantic", "cache_hit": false}
```

**llm_call:**
```json
{"trace_id": "351f09cb-1dd8-464a-991c-a6d52b599e0f", "request_id": "f6a5ef11-5143-488a-8513-93638123c0a6", "workflow_id": "unknown", "operation": "llm_call", "latency_ms": 1960.79, "success": true, "timestamp": "2026-01-14T17:05:05.259224Z", "tenant_id": "default", "model": "gpt-4o-mini", "tokens_estimate": 199, "sub_operation": "chain", "retries": 0, "prompt_length": 749, "response_length": 360}
```

**api_request:**
```json
{"trace_id": "351f09cb-1dd8-464a-991c-a6d52b599e0f", "request_id": "f6a5ef11-5143-488a-8513-93638123c0a6", "workflow_id": "unknown", "operation": "api_request", "latency_ms": 4221.57, "success": true, "timestamp": "2026-01-14T17:05:05.260678Z", "tenant_id": "default", "endpoint": "/smoke/correlate", "method": "POST", "status_code": 200}
```

### Verification Command
```bash
# Automated verification (CI/CD)
docker compose --profile test up --build --abort-on-container-exit --exit-code-from smoke-test

# Manual verification
docker compose logs agent-api | grep "351f09cb-1dd8-464a-991c-a6d52b599e0f"
```

---

## 5. Automated Smoke Test Output

```
==============================================
BHT AUTOMATED AUDIT CORRELATION SMOKE TEST
==============================================

[1/6] Verifying API health...
{"status":"healthy","timestamp":"2026-01-14T17:05:01.032385","service":"DHCS BHT Multi-Agent API"}
  ✓ Health check passed

[2/6] Calling /smoke/correlate (triggers retrieval + llm_call)...
  Response received (truncated): {"success":true,"trace_id":"351f09cb-1dd8-464a-991c-a6d52b599e0f","retrieval_count":3,"llm_summary":"Mobile crisis teams are mandated to provide immediate in-person cr...

[3/6] Extracting trace_id from response...
  ✓ trace_id: 351f09cb-1dd8-464a-991c-a6d52b599e0f

[4/6] Verifying audit file...
  ✓ Audit file exists with 5 entries

[5/6] Verifying SINGLE-REQUEST CORRELATION...
  Looking for trace_id 351f09cb-1dd8-464a-991c-a6d52b599e0f in all three operations:

  Debug - Lines with trace_id:
{"trace_id": "351f09cb-1dd8-464a-991c-a6d52b599e0f", "request_id": "f6a5ef11-5143-488a-8513-93638123c0a6", ... "operation": "retrieval", ...}
{"trace_id": "351f09cb-1dd8-464a-991c-a6d52b599e0f", "request_id": "f6a5ef11-5143-488a-8513-93638123c0a6", ... "operation": "llm_call", ...}
{"trace_id": "351f09cb-1dd8-464a-991c-a6d52b599e0f", "request_id": "f6a5ef11-5143-488a-8513-93638123c0a6", ... "operation": "api_request", ... "endpoint": "/smoke/correlate", ...}

  ✓ api_request: FOUND
  ✓ retrieval: FOUND
  ✓ llm_call: FOUND

[6/6] Running security checks...
  ✓ No API key patterns found
  ✓ No prompt content logged
  ✓ No response content logged

==============================================
SMOKE TEST RESULTS
==============================================

trace_id: 351f09cb-1dd8-464a-991c-a6d52b599e0f

Operations verified (same trace_id):
  - api_request:  FOUND
  - retrieval:    FOUND
  - llm_call:     FOUND

Security checks:
  - No secrets in logs: PASS
  - Prompts disabled:   PASS
  - Responses disabled: PASS

==============================================
ALL ASSERTIONS PASSED
==============================================
smoke-test exited with code 0
```

---

## 6. Commands Reference

### Build and Run
```bash
# Build images
docker compose build

# Start API only (development)
docker compose up -d agent-api

# Start with infrastructure
docker compose --profile infra up -d

# Start everything
docker compose --profile full up -d
```

### Automated Smoke Test (CI/CD)
```bash
# Run fully automated smoke test with assertions
# Exits 0 ONLY if ALL assertions pass:
#   - api_request + retrieval + llm_call with SAME trace_id
#   - No secrets (sk-) in audit logs
#   - No prompt/response content logged
docker compose --profile test up --build --abort-on-container-exit --exit-code-from smoke-test
```

### View Audit Logs
```bash
# All audit entries
docker compose logs agent-api | grep '"operation"'

# By operation type
docker compose logs agent-api | grep '"operation":"api_request"'
docker compose logs agent-api | grep '"operation":"llm_call"'
docker compose logs agent-api | grep '"operation":"retrieval"'

# By specific trace_id
docker compose logs agent-api | grep "<trace_id>"
```

### Cleanup
```bash
docker compose --profile full down -v
```

---

## 7. Re-run Verification From Scratch

```bash
# Clean slate verification
docker compose down -v && \
docker compose --profile test up --build --abort-on-container-exit --exit-code-from smoke-test
```

---

## 8. Remaining Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| PyPI timeouts during build | Low | Retry build; consider requirements lock file |
| ChromaDB first-startup delay | Low | Embedding model download cached after first run |
| Pinot not running | Info | Expected - graceful degradation; /chat returns error but audits correctly |

---

## 9. Final Status

| Category | Status |
|----------|--------|
| Build | ✅ PASS |
| Runtime | ✅ PASS |
| Healthchecks | ✅ PASS |
| Audit: api_request | ✅ PASS |
| Audit: llm_call | ✅ PASS |
| Audit: retrieval | ✅ PASS |
| **Single-request correlation** | ✅ PASS |
| Automated Smoke Test | ✅ PASS |
| Security: No secrets in logs | ✅ PASS |
| Security: Prompts disabled | ✅ PASS |
| Security: Responses disabled | ✅ PASS |
| Compose Hygiene | ✅ PASS |

## OVERALL STATUS: ✅ PASS

**Critical requirement met:** Single-request audit correlation verified. The same trace_id (`351f09cb-1dd8-464a-991c-a6d52b599e0f`) appears in api_request, llm_call, AND retrieval operations from ONE request to `/smoke/correlate`.

**Automated verification:** The smoke test automatically exits with code 1 unless ALL assertions pass. No manual verification required for CI/CD integration.
