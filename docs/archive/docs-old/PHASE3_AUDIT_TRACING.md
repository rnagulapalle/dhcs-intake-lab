# BHT Platform Phase 3 - Mandatory Audit + Tracing (Full)

## Overview

Phase 3 implements full audit and tracing infrastructure with:
- Mandatory fields across all platform logs
- Structured JSON logging
- AuditSink abstraction for flexible output destinations
- Trace correlation across LLM, retrieval, and workflow steps

**Key Principles:**
- No user-facing API breaking changes
- Prompt/response logging disabled by default
- Additive behavior only
- No directory restructure

## Feature Flags

### Logging Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `BHT_JSON_LOGS_ENABLED` | `true` | Enable JSON structured logging |
| `BHT_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### Audit Sink Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `BHT_AUDIT_SINK` | `stdout` | Sink type: `stdout`, `file`, `null` |
| `BHT_AUDIT_FILE_PATH` | `./logs/audit.jsonl` | Path for file sink |
| `BHT_AUDIT_FILE_MAX_SIZE_MB` | `10` | Max file size before rotation |
| `BHT_AUDIT_PRETTY_PRINT` | `false` | Pretty-print JSON (dev mode) |

### Privacy Configuration

| Flag | Default | Description |
|------|---------|-------------|
| `BHT_AUDIT_LOG_PROMPTS` | `false` | Log full prompt text (privacy risk) |
| `BHT_AUDIT_LOG_RESPONSES` | `false` | Log full response text (privacy risk) |

## Mandatory Audit Fields

Every audit log entry MUST contain these fields:

| Field | Type | Description |
|-------|------|-------------|
| `trace_id` | string | Unique trace identifier (links all ops in a request) |
| `request_id` | string | Unique request identifier |
| `workflow_id` | string | Workflow name (e.g., "curation", "chat") |
| `operation` | string | Operation type (see below) |
| `latency_ms` | float | Operation latency in milliseconds |
| `success` | bool | Whether operation succeeded |

### Operation Types

| Operation | Description |
|-----------|-------------|
| `llm_call` | LLM invocation via ModelGateway |
| `retrieval` | Document retrieval via RetrievalService |
| `workflow_step` | Orchestrator workflow step |
| `api_request` | API endpoint request/response |

## Log Entry Examples

### LLM Call

```json
{
  "trace_id": "abc-123-def",
  "request_id": "req-456",
  "workflow_id": "curation",
  "operation": "llm_call",
  "latency_ms": 1500.5,
  "success": true,
  "timestamp": "2024-01-15T10:30:00.123Z",
  "tenant_id": "county_la",
  "model": "gpt-4o-mini",
  "tokens_estimate": 500,
  "sub_operation": "invoke",
  "retries": 0
}
```

### Retrieval

```json
{
  "trace_id": "abc-123-def",
  "request_id": "req-456",
  "workflow_id": "curation",
  "operation": "retrieval",
  "latency_ms": 125.0,
  "success": true,
  "timestamp": "2024-01-15T10:30:01.500Z",
  "tenant_id": "county_la",
  "query_length": 45,
  "n_results": 5,
  "strategy": "semantic",
  "cache_hit": false
}
```

### Workflow Step

```json
{
  "trace_id": "abc-123-def",
  "request_id": "req-456",
  "workflow_id": "curation",
  "operation": "workflow_step",
  "latency_ms": 2500.0,
  "success": true,
  "timestamp": "2024-01-15T10:30:05.000Z",
  "tenant_id": "county_la",
  "step_name": "evidence_extraction",
  "output_summary": "Extracted 5 requirements"
}
```

### Error Entry

```json
{
  "trace_id": "abc-123-def",
  "request_id": "req-456",
  "workflow_id": "curation",
  "operation": "llm_call",
  "latency_ms": 30000.0,
  "success": false,
  "timestamp": "2024-01-15T10:30:30.000Z",
  "tenant_id": "county_la",
  "model": "gpt-4o-mini",
  "error": "Request timed out after 30 seconds",
  "error_type": "timeout"
}
```

## Usage

### Basic Audit Context

```python
from platform.audit_context import AuditContext

# Create context at request boundary
with AuditContext.create(workflow_id="chat", tenant_id="county_la") as ctx:
    # All operations inherit trace_id
    result = gateway.invoke(messages)  # Auto-logs LLM call
    docs = service.search(query)       # Auto-logs retrieval

# Or get current context anywhere
ctx = AuditContext.current()
print(f"Trace ID: {ctx.trace_id}")
```

### Workflow Step Timer

```python
from platform.audit_context import WorkflowStepTimer, AuditContext

with AuditContext.create(workflow_id="curation") as ctx:
    with WorkflowStepTimer("evidence_extraction") as step:
        # Do work...
        step.set_metadata({"documents_processed": 5})
        step.set_output_summary("Extracted 5 requirements")

    # Automatically logs workflow_step with latency
```

### Custom Audit Sink

```python
from platform.audit_sink import FileAuditSink, set_default_audit_sink

# Write audit to file
sink = FileAuditSink("./logs/audit.jsonl", max_size_mb=50)
set_default_audit_sink(sink)
```

## Files Changed

### New Files

| File | Description |
|------|-------------|
| [platform/audit_sink.py](../platform/audit_sink.py) | AuditSink abstraction and implementations |
| [platform/logging.py](../platform/logging.py) | PlatformLogger and JSON formatter |
| [tests/platform/test_phase3_audit.py](../tests/platform/test_phase3_audit.py) | Contract and integration tests |

### Modified Files

| File | Changes |
|------|---------|
| [platform/config.py](../platform/config.py) | Added logging and sink config flags |
| [platform/audit_context.py](../platform/audit_context.py) | Mandatory fields, sink integration, WorkflowStepTimer |

## Validation

### Run Tests

```bash
# Run Phase 3 audit tests
pytest tests/platform/test_phase3_audit.py -v

# Run all platform tests
pytest tests/platform/ -v
```

### Validate Locally

```bash
# Start API server with JSON logs
export BHT_JSON_LOGS_ENABLED=true
export BHT_AUDIT_SINK=stdout
python -m api.main

# Send request and observe logs
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the mobile crisis response requirements?"}'

# Expected output (JSON lines):
# {"trace_id":"abc-123","operation":"workflow_step","step_name":"intent_classification",...}
# {"trace_id":"abc-123","operation":"retrieval","n_results":5,...}
# {"trace_id":"abc-123","operation":"llm_call","model":"gpt-4o-mini",...}
# {"trace_id":"abc-123","operation":"api_request","endpoint":"/chat","status_code":200,...}
```

### Verify Trace Correlation

```bash
# Extract trace_id from logs and verify all entries share it
cat logs/audit.jsonl | jq -r '.trace_id' | sort | uniq -c

# Should show single trace_id with multiple entries
```

### Verify Mandatory Fields

```python
from platform.audit_sink import validate_audit_entry

entry = {"trace_id": "abc", "operation": "llm_call", ...}
missing = validate_audit_entry(entry)
assert len(missing) == 0, f"Missing fields: {missing}"
```

## Risks

### Low Risk (Default Behavior)
- All new features are additive
- Prompt/response logging disabled by default
- No API breaking changes
- Audit failures don't break application

### Medium Risk (When Enabled)
- **File sink rotation**: May lose logs during rotation
  - Mitigation: Write to new file before deleting old
- **High log volume**: May impact disk/bandwidth
  - Mitigation: Use null sink in high-volume testing

## Rollback

### Disable JSON Logging

```bash
export BHT_JSON_LOGS_ENABLED=false
```

### Disable All Audit

```bash
export BHT_AUDIT_SINK=null
```

### Revert to Phase 2 Behavior

Phase 3 is fully backward compatible. Existing code continues to work.
The only change is that audit entries now include the `operation` field.

## Assumptions / Needs Confirmation

1. **Log aggregator compatibility**: Assumes log aggregator (CloudWatch, Datadog, etc.) can parse JSON lines from stdout
2. **Trace ID format**: Using UUID v4 - confirm this is acceptable
3. **Tenant ID source**: Currently passed explicitly - confirm how this should be extracted from requests
4. **Log retention**: File sink rotation deletes old files - confirm retention policy
