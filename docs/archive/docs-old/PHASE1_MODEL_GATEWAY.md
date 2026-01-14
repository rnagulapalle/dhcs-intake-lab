# BHT Platform Phase 1 - Model Gateway

## Overview

Phase 1 upgrades the Phase 0 shim layer to a real ModelGateway with centralized LLM access and reliability features.

**Key Changes in Phase 1 (Hardened):**
- **Centralized Gateway**: ON by default (`BHT_USE_CENTRALIZED_GATEWAY=true`)
- **Reliability Features**: OFF by default (timeout, retry, circuit breaker)
- **No Provider Imports Outside platform/**: ChatOpenAI imports ONLY in `platform/model_gateway.py`
- **Rollback Changes Gateway Behavior**: Agents never import providers directly

## Feature Flags

### Gateway Centralization (ENABLED by default)

| Flag | Default | Description |
|------|---------|-------------|
| `BHT_USE_CENTRALIZED_GATEWAY` | `true` | **All agents use singleton gateway** |

### Reliability Features (ALL disabled by default)

| Flag | Default | Description |
|------|---------|-------------|
| `BHT_MODEL_TIMEOUT_ENABLED` | `false` | Enforce timeout on LLM calls |
| `BHT_MODEL_RETRY_ENABLED` | `false` | Retry transient failures with exponential backoff |
| `BHT_CIRCUIT_BREAKER_ENABLED` | `false` | Open circuit after consecutive failures |

### Timeout Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `BHT_DEFAULT_TIMEOUT` | `60.0` | Default timeout in seconds |

### Retry Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `BHT_MAX_RETRIES` | `3` | Maximum retry attempts |
| `BHT_RETRY_BASE_DELAY` | `1.0` | Base delay in seconds |
| `BHT_RETRY_MAX_DELAY` | `30.0` | Maximum delay in seconds |
| `BHT_RETRY_JITTER` | `0.1` | Jitter factor (±10%) |

### Circuit Breaker Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `BHT_CB_THRESHOLD` | `5` | Failures before opening circuit |
| `BHT_CB_RECOVERY` | `60.0` | Recovery timeout in seconds |
| `BHT_CB_HALF_OPEN_MAX` | `1` | Max calls in half-open state |

## Behavior by Configuration

### Default (All Features Disabled)

```
BHT_MODEL_TIMEOUT_ENABLED=false
BHT_MODEL_RETRY_ENABLED=false
BHT_CIRCUIT_BREAKER_ENABLED=false
```

- Identical behavior to Phase 0
- Single attempt per LLM call
- No timeout enforcement
- No circuit breaker
- Audit logging still active

### Timeout Enabled

```
BHT_MODEL_TIMEOUT_ENABLED=true
BHT_DEFAULT_TIMEOUT=30
```

- LLM calls timeout after 30 seconds
- Raises `ModelTimeoutError` on timeout
- Logged as `error_type: "timeout"`

### Retry Enabled

```
BHT_MODEL_RETRY_ENABLED=true
BHT_MAX_RETRIES=3
```

- Retries on transient errors (rate limit, connection, 5xx)
- Does NOT retry on: auth errors, 4xx errors
- Exponential backoff: 1s, 2s, 4s (capped at 30s)
- Raises `ModelRetryExhaustedError` after all attempts fail
- Audit log includes `retries` count

### Circuit Breaker Enabled

```
BHT_CIRCUIT_BREAKER_ENABLED=true
BHT_CB_THRESHOLD=5
BHT_CB_RECOVERY=60
```

States:
- **CLOSED**: Normal operation, failures counted
- **OPEN**: After 5 failures, rejects immediately with `CircuitBreakerOpenError`
- **HALF_OPEN**: After 60s, allows 1 test request

### Centralized Gateway (DEFAULT)

```
BHT_USE_CENTRALIZED_GATEWAY=true  # This is the default
```

- **All agents** use singleton ModelGateway (no direct ChatOpenAI)
- Guarantees all LLM calls go through gateway
- Enables centralized monitoring, audit logging, and control
- Set to `false` only for debugging/rollback

## Audit Log Fields

Phase 1 adds new fields to audit logs:

```json
{
  "type": "llm_call",
  "trace_id": "...",
  "model": "gpt-4o-mini",
  "operation": "invoke",
  "latency_ms": 1500.5,
  "tokens_estimate": 500,
  "success": false,
  "retries": 2,
  "error": "Rate limit exceeded",
  "error_type": "rate_limit"
}
```

New fields:
- `retries`: Number of retry attempts (0 if disabled)
- `error_type`: Classification of error (timeout, rate_limit, connection_error, auth_error, unknown)

## Files Changed

### Modified

| File | Changes |
|------|---------|
| [platform/config.py](../platform/config.py) | Added reliability feature flags, centralized gateway default=true |
| [platform/model_gateway.py](../platform/model_gateway.py) | Full gateway implementation |
| [platform/errors.py](../platform/errors.py) | Added `CircuitBreakerOpenError`, `ModelRetryExhaustedError` |
| [platform/audit_context.py](../platform/audit_context.py) | Added `error_type` field |
| [agents/core/base_agent.py](../agents/core/base_agent.py) | Uses centralized gateway by default |
| [agents/core/orchestrator.py](../agents/core/orchestrator.py) | Uses centralized gateway |
| [agents/core/curation_orchestrator.py](../agents/core/curation_orchestrator.py) | Uses centralized gateway |
| [agents/core/evidence_extraction_agent.py](../agents/core/evidence_extraction_agent.py) | Uses centralized gateway |
| [agents/core/grounding_verification_agent.py](../agents/core/grounding_verification_agent.py) | Uses centralized gateway |
| [agents/core/evidence_composition_agent.py](../agents/core/evidence_composition_agent.py) | Uses centralized gateway |

### New Test Files

| File | Purpose |
|------|---------|
| [tests/platform/test_model_gateway_reliability.py](../tests/platform/test_model_gateway_reliability.py) | Unit tests for retry, timeout, circuit breaker |
| [tests/platform/test_centralized_gateway.py](../tests/platform/test_centralized_gateway.py) | Integration tests for centralized usage |
| [tests/platform/test_no_direct_chatgpt.py](../tests/platform/test_no_direct_chatgpt.py) | Enforcement test: no direct ChatOpenAI imports |
| [tests/platform/test_audit_integration.py](../tests/platform/test_audit_integration.py) | Integration tests for audit logging |

## Validation

### Verify No Behavior Change (Default)

```bash
# All flags disabled (default)
export BHT_PLATFORM_ENABLED=true
export BHT_MODEL_TIMEOUT_ENABLED=false
export BHT_MODEL_RETRY_ENABLED=false
export BHT_CIRCUIT_BREAKER_ENABLED=false

# Run existing tests - should all pass
pytest tests/
```

### Verify Centralized Gateway

```bash
# Enable centralized gateway
export BHT_USE_CENTRALIZED_GATEWAY=true

# All agents should log LLM calls through gateway
# Check logs for "llm_call" entries with trace_id
```

### Verify Retry Works

```bash
export BHT_MODEL_RETRY_ENABLED=true
export BHT_MAX_RETRIES=3

# Simulate rate limit (will retry 3 times)
# Audit logs show retries=2 for exhausted retries
```

## Rollback

### Disable Reliability Features Only

Reliability features are already OFF by default. If you enabled them and need to rollback:

```bash
# Disable retry only
export BHT_MODEL_RETRY_ENABLED=false

# Disable timeout only
export BHT_MODEL_TIMEOUT_ENABLED=false

# Disable circuit breaker only
export BHT_CIRCUIT_BREAKER_ENABLED=false
```

### Disable Centralized Gateway (Full Rollback to Phase 0)

⚠️ **Use only if issues are detected with centralized gateway:**

```bash
# Disable centralized gateway - agents will use direct ChatOpenAI
export BHT_USE_CENTRALIZED_GATEWAY=false
```

This will:
- Agents with gateway support fall back to direct ChatOpenAI
- Audit logging still works at API level
- No behavior change in LLM responses

### Disable All Phase 1 Features

```bash
# Complete Phase 1 rollback (Phase 0 behavior)
export BHT_MODEL_TIMEOUT_ENABLED=false
export BHT_MODEL_RETRY_ENABLED=false
export BHT_CIRCUIT_BREAKER_ENABLED=false
export BHT_USE_CENTRALIZED_GATEWAY=false
```

### Complete Platform Disable

```bash
# Master kill switch (Phase 0 + Phase 1 disabled)
export BHT_PLATFORM_ENABLED=false
```

## Verification: No Behavior Change

### Before/After Check

With centralized gateway enabled (default), verify:

1. **Prompts unchanged**: Same prompts sent to LLM
2. **Model unchanged**: Same model used (gpt-4o-mini by default)
3. **Temperature unchanged**: Same temperature per agent
4. **Responses unchanged**: Same response format and content

### Verification Commands

```bash
# Run enforcement tests (Phase 1 Hardened)
pytest tests/platform/test_no_direct_chatgpt.py -v

# Run audit integration tests
pytest tests/platform/test_audit_integration.py -v

# Run all platform tests
pytest tests/platform/ -v

# Verify NO ChatOpenAI imports outside platform/
grep -rn "from langchain_openai import ChatOpenAI" --include="*.py" agents/ api/
# Should return NO matches

# Verify platform/ is the only location
grep -rn "from langchain_openai import ChatOpenAI" --include="*.py" platform/
# Should only show platform/model_gateway.py
```

## Risks

### Low Risk (Default Behavior)
- All features disabled by default
- No change to existing behavior
- Audit logging continues as Phase 0

### Medium Risk (When Enabled)
- **Timeout**: May cut off long-running LLM calls
  - Mitigation: Set conservative timeout (60s default)
- **Retry**: May increase latency on failures
  - Mitigation: Cap at 3 retries, max 30s delay
- **Circuit Breaker**: May reject good requests after transient failures
  - Mitigation: 60s recovery, single test request

### Mitigation Strategy

1. Enable one feature at a time
2. Monitor audit logs for error_type distribution
3. Adjust thresholds based on observed behavior
4. Use instant rollback if issues detected

## Usage Examples

### Basic Usage (Default)

```python
from platform.model_gateway import ModelGateway

gateway = ModelGateway(model="gpt-4o-mini")
result = gateway.invoke("Hello")  # Single attempt, no timeout
```

### With Retry Enabled

```python
# Set BHT_MODEL_RETRY_ENABLED=true

gateway = ModelGateway(model="gpt-4o-mini")
try:
    result = gateway.invoke("Hello")  # Will retry on rate limit
except ModelRetryExhaustedError:
    print("All retries failed")
```

### With Timeout

```python
# Set BHT_MODEL_TIMEOUT_ENABLED=true

gateway = ModelGateway(model="gpt-4o-mini")
try:
    result = gateway.invoke("Hello", timeout=30)  # 30s timeout
except ModelTimeoutError:
    print("Request timed out")
```

### Centralized Gateway for All Agents

```python
# Set BHT_USE_CENTRALIZED_GATEWAY=true

from agents.core.base_agent import BaseAgent

# Agent automatically uses singleton gateway
agent = BaseAgent(name="Test", role="Test", goal="Test")
assert agent.has_gateway() is True
```

## Next Steps

- Phase 2: Add model routing and fallback
- Phase 3: Add budget enforcement
- Phase 4: Add kill switches
