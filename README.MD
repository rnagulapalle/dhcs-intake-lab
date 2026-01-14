# DHCS BHT Multi-Agent AI System

**California Department of Health Care Services - Behavioral Health Transformation**

An AI-powered multi-agent system supporting California's $6.38 billion Behavioral Health Transformation initiative (Proposition 1, AB 531, SB 326).

---

## What This System Does

| Use Case | Description |
|----------|-------------|
| **Crisis Triage** | Real-time crisis assessment and risk prioritization |
| **Policy Q&A** | RAG-based access to DHCS policy documents |
| **Analytics** | Population and resource utilization insights |
| **Recommendations** | Operational recommendations based on data |

---

## Quick Start (Docker)

### Prerequisites
- **Docker Desktop** with Docker Compose v2+
- **OpenAI API Key** from [platform.openai.com](https://platform.openai.com/api-keys)
- **8GB RAM** minimum

### 1. Clone and Configure

```bash
git clone <repository-url> dhcs-intake-lab
cd dhcs-intake-lab

# Create .env with your OpenAI key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### 2. Start the API

```bash
# Start API only (recommended for development)
docker compose up -d agent-api

# Verify health
curl http://localhost:8000/health
```

### 3. Run Smoke Test

```bash
# Automated test with audit correlation verification
docker compose --profile test up --build --abort-on-container-exit --exit-code-from smoke-test
```

### 4. Full Stack (Optional)

```bash
# Start everything: API + Kafka + Pinot + Dashboard
docker compose --profile full up -d

# Dashboard at http://localhost:8501
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System components, agent flows, endpoints |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Operations: start, test, trace, onboard, troubleshoot |

---

## Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/chat` | POST | Main chat interface (routes to agents) |
| `/knowledge/search` | POST | Direct RAG search |
| `/smoke/correlate` | POST | Smoke test endpoint (triggers retrieval + LLM) |

---

## Docker Compose Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| (default) | agent-api | Development, API-only |
| test | agent-api-test, smoke-test | Automated smoke testing |
| infra | kafka, zookeeper, pinot-* | Full infrastructure |
| dashboard | dashboard | Streamlit UI |
| full | All services | Complete stack |

---

## Project Structure

```
dhcs-intake-lab/
├── agents/              # Multi-agent system
│   └── core/            # Agent implementations
├── api/                 # FastAPI backend
│   ├── main.py          # API endpoints
│   └── Dockerfile       # Container build
├── platform/            # Platform services
│   ├── model_gateway.py # Centralized LLM access
│   ├── retrieval_service.py # RAG service
│   └── audit_context.py # Trace correlation
├── dashboard/           # Streamlit UI
├── data/                # Policy documents (ChromaDB source)
├── docker-compose.yml   # Container orchestration
└── docs/                # Documentation
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `BHT_PLATFORM_ENABLED` | No | `true` | Enable platform features |
| `BHT_AUDIT_SINK` | No | `stdout` | Audit output: stdout, file, null |
| `LOG_LEVEL` | No | `INFO` | Logging level |

---

## License

DHCS - California Department of Health Care Services
