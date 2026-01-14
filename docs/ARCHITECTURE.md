# System Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  Streamlit Dashboard (8501)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (8000)                         │
│                   api/main.py endpoints                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR AGENT                             │
│                   agents/core/orchestrator.py                    │
│                   (LangGraph ReAct pattern)                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Query    │    │ Triage   │    │Knowledge │
    │ Agent    │    │ Agent    │    │ Agent    │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │  Pinot   │   │  OpenAI  │   │ ChromaDB │
   │  (OLAP)  │   │ GPT-4o   │   │  (RAG)   │
   └──────────┘   └──────────┘   └──────────┘
         ▲
         │
   ┌──────────┐
   │  Kafka   │
   │(Streaming)│
   └──────────┘
```

---

## Components

### API Layer

| File | Purpose |
|------|---------|
| `api/main.py` | FastAPI endpoints, middleware, request handling |
| `api/Dockerfile` | Multi-stage build, non-root user (bht:1000) |

**Key Endpoints:**
- `/health` - Health check
- `/chat` - Main orchestrator endpoint
- `/knowledge/search` - Direct RAG search
- `/smoke/correlate` - Smoke test (retrieval + LLM)

### Platform Layer

| File | Purpose |
|------|---------|
| `platform/model_gateway.py` | Centralized LLM access with audit callbacks |
| `platform/retrieval_service.py` | RAG with audit logging |
| `platform/audit_context.py` | Trace ID propagation (ContextVar) |
| `platform/middleware.py` | Request correlation middleware |

### Agent Layer

| Agent | File | Purpose |
|-------|------|---------|
| Orchestrator | `agents/core/orchestrator.py` | Intent classification, routing |
| Query | `agents/core/query_agent.py` | Natural language → SQL |
| Analytics | `agents/core/analytics_agent.py` | Trend analysis |
| Triage | `agents/core/triage_agent.py` | Risk prioritization |
| Recommendations | `agents/core/recommendations_agent.py` | Operational suggestions |
| Knowledge | `agents/knowledge/knowledge_base.py` | ChromaDB RAG |

### Data Layer

| Component | Port | Purpose |
|-----------|------|---------|
| ChromaDB | (embedded) | Vector search for policy docs |
| Apache Pinot | 8099 (broker) | Real-time OLAP analytics |
| Apache Kafka | 9092 | Event streaming |
| Zookeeper | 2181 | Coordination |

---

## Audit Trace Flow

Every request generates a `trace_id` that correlates across:

```
Request → api_request audit → retrieval audit → llm_call audit
               │                    │                 │
               └────────────────────┴─────────────────┘
                        Same trace_id
```

**Audit Fields:**
```json
{
  "trace_id": "351f09cb-1dd8-464a-991c-a6d52b599e0f",
  "request_id": "f6a5ef11-5143-488a-8513-93638123c0a6",
  "operation": "api_request|retrieval|llm_call",
  "timestamp": "2026-01-14T17:05:05.260678Z",
  "latency_ms": 4221.57,
  "success": true
}
```

---

## Key Design Decisions

### 1. Prompt-Based vs ML Training
- No model training required
- Fast iteration via prompt updates
- Easy to deploy and update

### 2. Multi-Agent vs Monolithic
- Specialized prompts per domain
- Easier debugging and testing
- Parallel execution possible

### 3. RAG vs Fine-Tuning
- Always current with latest docs
- Shows sources and citations
- Easy updates without retraining

### 4. Kafka + Pinot for Real-Time
- Sub-second query latency
- Live data ingestion
- SQL interface for analytics

---

## Security

- Secrets via environment only (never in images)
- Non-root container user (bht:1000)
- Prompt/response logging disabled by default
- No API keys in audit logs

---

## Related Documentation

- [README.md](../README.md) - Quick start
- [RUNBOOK.md](RUNBOOK.md) - Operations guide
