# Operations Runbook

Guide for starting, testing, tracing, onboarding use cases, and troubleshooting.

---

## 1. Starting the System

### Development (API Only)

```bash
# Ensure .env exists with OPENAI_API_KEY
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# Start API service
docker compose up -d agent-api

# Verify
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"...","service":"DHCS BHT Multi-Agent API"}
```

### Full Stack (All Services)

```bash
# Start everything: API + Kafka + Pinot + Dashboard
docker compose --profile full up -d

# Wait for all services to be healthy (~60s)
docker compose ps

# Access points:
# - API: http://localhost:8000
# - Dashboard: http://localhost:8501
# - Pinot Controller: http://localhost:9000
```

### View Logs

```bash
# API logs
docker compose logs -f agent-api

# All services
docker compose logs -f
```

### Shutdown

```bash
# Stop services (keep volumes)
docker compose --profile full down

# Full reset (remove volumes)
docker compose --profile full down -v
```

---

## 2. Running Tests

### Automated Smoke Test (CI/CD Ready)

The smoke test verifies single-request audit correlation across all operations.

```bash
# Run automated smoke test
docker compose --profile test up --build --abort-on-container-exit --exit-code-from smoke-test
```

**What It Verifies:**
1. API health check passes
2. `/smoke/correlate` returns valid response
3. Same `trace_id` appears in audit for:
   - `api_request` (endpoint call)
   - `retrieval` (ChromaDB search)
   - `llm_call` (OpenAI call)
4. No secrets (`sk-`) in audit logs
5. No prompt/response content logged

**Expected Output:**
```
==============================================
BHT AUTOMATED AUDIT CORRELATION SMOKE TEST
==============================================

[1/6] Verifying API health...
  ✓ Health check passed

[2/6] Calling /smoke/correlate (triggers retrieval + llm_call)...
  Response received (truncated): {"success":true,"trace_id":"...

[3/6] Extracting trace_id from response...
  ✓ trace_id: 351f09cb-1dd8-464a-991c-a6d52b599e0f

[4/6] Verifying audit file...
  ✓ Audit file exists with 5 entries

[5/6] Verifying SINGLE-REQUEST CORRELATION...
  ✓ api_request: FOUND
  ✓ retrieval: FOUND
  ✓ llm_call: FOUND

[6/6] Running security checks...
  ✓ No API key patterns found
  ✓ No prompt content logged
  ✓ No response content logged

==============================================
ALL ASSERTIONS PASSED
==============================================
smoke-test exited with code 0
```

**Exit Codes:**
- `0` - All assertions passed
- `1` - One or more assertions failed

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/health

# Knowledge search
curl -X POST http://localhost:8000/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "crisis response protocols", "n_results": 3}'

# Chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are crisis intervention requirements?"}'
```

---

## 3. Tracing a Request End-to-End

### Step 1: Make a Request

```bash
curl -X POST http://localhost:8000/smoke/correlate \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the crisis response protocols?"}'
```

Response includes `trace_id`:
```json
{
  "success": true,
  "trace_id": "351f09cb-1dd8-464a-991c-a6d52b599e0f",
  "retrieval_count": 3,
  "llm_summary": "..."
}
```

### Step 2: Find Correlated Audit Entries

```bash
# For stdout logging (default profile)
docker compose logs agent-api | grep "351f09cb-1dd8-464a-991c-a6d52b599e0f"

# For file logging (test profile)
docker compose exec agent-api-test cat /app/logs/audit.jsonl | grep "351f09cb"
```

### Step 3: Analyze the Trace

You should see three entries with the same `trace_id`:

| Operation | Key Fields |
|-----------|------------|
| `retrieval` | `n_results`, `strategy`, `latency_ms` |
| `llm_call` | `model`, `tokens_estimate`, `latency_ms` |
| `api_request` | `endpoint`, `status_code`, `latency_ms` |

Example audit entries:
```json
{"trace_id": "351f09cb-...", "operation": "retrieval", "n_results": 3, "latency_ms": 2013.36}
{"trace_id": "351f09cb-...", "operation": "llm_call", "model": "gpt-4o-mini", "latency_ms": 1960.79}
{"trace_id": "351f09cb-...", "operation": "api_request", "endpoint": "/smoke/correlate", "status_code": 200}
```

---

## 4. Adding a New Use Case

### Step 1: Create the Agent

Create a new agent in `agents/core/`:

```python
# agents/core/my_new_agent.py
from agents.core.base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MyNewAgent",
            role="Description of what this agent does",
            goal="Specific goal this agent achieves",
            temperature=0.3
        )

    def execute(self, input_data: dict) -> dict:
        # Use self.llm for LLM calls (via ModelGateway)
        # Use platform.retrieval_service for RAG
        result = self.llm.invoke(...)
        return {"success": True, "result": result}
```

### Step 2: Add API Endpoint

Add endpoint in `api/main.py`:

```python
from agents.core.my_new_agent import MyNewAgent

@app.post("/my-use-case")
async def my_use_case(request: MyRequest) -> Dict[str, Any]:
    agent = MyNewAgent()
    result = agent.execute(request.dict())
    return result
```

### Step 3: Register with Orchestrator (Optional)

If the use case should be routable via `/chat`, update `agents/core/orchestrator.py`:

```python
# Add to intent classification
if "my keyword" in user_input.lower():
    return "my_new_use_case"

# Add routing
elif intent == "my_new_use_case":
    agent = MyNewAgent()
    result = agent.execute({"query": user_input})
```

### Step 4: Add Data (If Needed)

For RAG-based use cases, add documents to `data/`:
- Markdown or text files
- Will be indexed by ChromaDB on startup

---

## 5. Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs agent-api

# Common issues:
# 1. Missing OPENAI_API_KEY
#    Fix: echo "OPENAI_API_KEY=sk-..." > .env

# 2. Port already in use
#    Fix: docker compose down && docker compose up -d

# 3. Not enough memory
#    Fix: Allocate 8GB+ in Docker Desktop settings
```

### Health Check Failing

```bash
# Check if container is running
docker compose ps

# Check container health
docker inspect agent-api | grep -A 10 "Health"

# View recent logs
docker compose logs agent-api --tail=50
```

### Audit Logs Not Appearing

```bash
# Check audit sink configuration
docker compose exec agent-api env | grep BHT_AUDIT

# Expected for default profile:
# BHT_AUDIT_SINK=stdout

# View logs with audit entries
docker compose logs agent-api | grep '"operation"'
```

### LLM Calls Failing

```bash
# Check API key is set
docker compose exec agent-api env | grep OPENAI
# Should show: OPENAI_API_KEY=sk-... (redacted)

# Check for rate limiting in logs
docker compose logs agent-api | grep -i "rate\|429\|error"
```

### ChromaDB Issues

```bash
# Check ChromaDB initialization
docker compose logs agent-api | grep -i "chroma\|knowledge"

# Reset ChromaDB data
docker compose down -v
docker compose up -d agent-api
```

---

## 6. Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `BHT_PLATFORM_ENABLED` | No | `true` | Enable platform features |
| `BHT_AUDIT_SINK` | No | `stdout` | Audit output: `stdout`, `file`, `null` |
| `BHT_AUDIT_FILE_PATH` | No | `/app/logs/audit.jsonl` | Path for file sink |
| `BHT_AUDIT_LOG_PROMPTS` | No | `false` | Log prompt content |
| `BHT_AUDIT_LOG_RESPONSES` | No | `false` | Log response content |
| `BHT_JSON_LOGS_ENABLED` | No | `true` | Structured JSON logs |
| `LOG_LEVEL` | No | `INFO` | Log level |
| `CHROMA_PERSIST_DIR` | No | `/app/chroma_data` | ChromaDB storage |

---

## 7. Common Commands Reference

```bash
# Start/Stop
docker compose up -d agent-api              # API only
docker compose --profile full up -d         # Full stack
docker compose down                         # Stop
docker compose down -v                      # Stop + remove volumes

# Logs
docker compose logs -f agent-api            # Follow API logs
docker compose logs agent-api | grep '"operation"'  # Audit entries

# Testing
docker compose --profile test up --build --abort-on-container-exit --exit-code-from smoke-test

# Debugging
docker compose exec agent-api bash          # Shell into container
docker compose exec agent-api env           # View environment
docker inspect agent-api                    # Container details
```

---

## Related Documentation

- [README.md](../README.md) - Quick start
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
