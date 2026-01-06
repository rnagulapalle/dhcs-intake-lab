# System Architecture

**Document Version**: 1.0
**Last Updated**: January 2026

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [System Components](#system-components)
3. [Design Decisions](#design-decisions)
4. [Data Flow](#data-flow)
5. [Agent Architecture](#agent-architecture)

---

## Architecture Overview

### Architecture Pattern: **Prompt-Based Multi-Agent System**

```
┌─────────────────────────────────────────────────────────────────┐
│                       USER INTERFACE                            │
│                   (Streamlit Dashboard)                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│                    (REST API Endpoints)                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR AGENT                            │
│              (LangGraph State Machine)                          │
│                                                                 │
│  Pattern: ReAct (Reasoning + Acting)                           │
│  - Classifies user intent                                       │
│  - Routes to specialized agents                                 │
│  - Combines results                                             │
└──────┬──────┬────────┬────────┬──────────┬─────────────────────┘
       │      │        │        │          │
       ▼      ▼        ▼        ▼          ▼
   ┌──────┐ ┌────┐  ┌───────┐ ┌──────┐ ┌──────────┐
   │Query │ │Anal│  │Triage │ │ Recs │ │Knowledge │
   │Agent │ │ytics│  │Agent  │ │Agent │ │  Agent   │
   └──┬───┘ └─┬──┘  └───┬───┘ └──┬───┘ └────┬─────┘
      │       │         │        │          │
      │       │         │        │          │
      └───────┴─────────┴────────┴──────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌─────────┐   ┌─────────────┐   ┌─────────┐
    │  Pinot  │   │   OpenAI    │   │ChromaDB │
    │(Real-time│   │  GPT-4o     │   │ (RAG)   │
    │Analytics)│   │   (LLM)     │   │         │
    └─────────┘   └─────────────┘   └─────────┘
          ▲
          │
          │
    ┌─────┴─────┐
    │   Kafka   │
    │ (Streaming)│
    └─────▲─────┘
          │
          │
    ┌─────┴─────┐
    │ Generator │
    │(Synthetic)│
    └───────────┘
```

---

## System Components

### 1. Frontend Layer

#### Streamlit Dashboard
- **Purpose**: Modern web-based user interface
- **Technology**: Streamlit + Custom CSS
- **Features**:
  - 8 specialized use case interfaces
  - Real-time chat with AI agents
  - Context-aware filters and suggestions
  - Grok-inspired clean design
- **Port**: 8501
- **Container**: `dashboard`

---

### 2. API Layer

#### FastAPI Backend
- **Purpose**: REST API and agent orchestration
- **Technology**: FastAPI + Python 3.11
- **Endpoints**:
  - `/health` - Health check
  - `/chat` - General chat with orchestrator
  - `/knowledge/search` - Policy document search (RAG)
  - `/query` - Pinot SQL query execution
  - `/analytics` - Real-time analytics
  - `/triage` - Crisis triage recommendations
- **Port**: 8000
- **Container**: `agent-api`

---

### 3. Agent Layer

#### Orchestrator Agent (LangGraph)
**Pattern**: ReAct (Reasoning + Acting)

```python
def process_query(user_input):
    # THOUGHT: What is the user asking?
    intent = classify_intent(user_input)

    # ACTION: Route to appropriate agent
    if intent == "crisis_triage":
        result = triage_agent.execute(user_input)
    elif intent == "policy_question":
        result = knowledge_agent.search(user_input)
    elif intent == "analytics":
        result = analytics_agent.analyze(user_input)

    # OBSERVATION: Validate and combine results
    response = synthesize_response(result)

    return response
```

#### Specialized Agents

**Query Agent**
- Converts natural language to Pinot SQL
- Executes queries against real-time data
- Formats results for display

**Analytics Agent**
- Performs statistical analysis
- Generates insights and trends
- Creates summary reports

**Triage Agent**
- Assesses crisis severity
- Recommends interventions
- Prioritizes cases

**Recommendations Agent**
- Generates actionable suggestions
- Considers policy constraints
- Optimizes resource allocation

**Knowledge Agent**
- RAG-based document retrieval
- Semantic search over policy docs
- Citation and source tracking

---

### 4. Data Layer

#### Apache Kafka
- **Purpose**: Real-time event streaming
- **Topic**: `dhcs-crisis-intake`
- **Data**: Crisis events (JSON)
- **Retention**: 7 days
- **Partitions**: 3
- **Port**: 29092 (external), 9092 (internal)

#### Apache Pinot
- **Purpose**: Real-time OLAP analytics
- **Table**: `dhcs_crisis_intake` (REALTIME)
- **Ingestion**: Kafka consumer
- **Query**: SQL via broker
- **Ports**:
  - Controller: 9000
  - Broker: 8099
  - Server: 8098

**Schema**:
```json
{
  "event_id": "STRING",
  "event_time_ms": "LONG",
  "county": "STRING",
  "risk_level": "STRING",
  "channel": "STRING",
  "age": "INT",
  "gender": "STRING",
  "presenting_issue": "STRING",
  "response_time_minutes": "INT",
  "outcome": "STRING"
}
```

#### ChromaDB
- **Purpose**: Vector database for semantic search
- **Collections**: `dhcs_policies`
- **Embeddings**: OpenAI text-embedding-ada-002
- **Data**: 20+ policy documents
- **Use Cases**: Policy Q&A, IP Compliance

#### PostgreSQL (Optional)
- **Purpose**: Structured data storage
- **Tables**: Projects, Applications, Reports
- **Port**: 5432

---

### 5. Data Generation Layer

#### Synthetic Data Generators
- **Crisis Events**: Real-time stream to Kafka
- **Policy Documents**: Static files + vector embeddings
- **Infrastructure Projects**: JSON files
- **Licensing Applications**: JSON files
- **BHOATR Reports**: JSON files

---

## Design Decisions

### 1. Prompt Engineering > Model Training

**Why we chose prompt-based AI:**

| Aspect | Traditional ML | Our Approach |
|--------|---------------|--------------|
| Setup Time | 3-6 months | Days |
| Data Required | 10k+ labeled examples | None |
| Cost | $10k-50k+ | API usage only |
| Iteration Speed | Slow (retrain) | Fast (edit prompts) |
| Expertise Needed | ML engineers | Developers |
| Infrastructure | GPU clusters | API calls |
| Updates | Redeploy models | Update configs |

**Benefits**:
- ✅ No model training required
- ✅ Instant deployment
- ✅ Easy to iterate and improve
- ✅ Lower maintenance overhead
- ✅ No GPU infrastructure costs

---

### 2. Multi-Agent Architecture

**Why specialized agents instead of one model?**

```
Monolithic Approach:              Multi-Agent Approach:
┌──────────────────┐             ┌─────────────────┐
│                  │             │  Orchestrator   │
│   One Big Model  │             └────────┬────────┘
│                  │                      │
│ - Crisis Triage  │         ┌────────────┼────────────┐
│ - Policy Q&A     │         │            │            │
│ - Analytics      │         ▼            ▼            ▼
│ - Reporting      │     ┌───────┐   ┌───────┐   ┌───────┐
│ - etc.           │     │Triage │   │Policy │   │Query  │
│                  │     │Agent  │   │Agent  │   │Agent  │
└──────────────────┘     └───────┘   └───────┘   └───────┘

Issues:                   Benefits:
- Prompt too complex      - Specialized prompts
- Context confusion       - Clear responsibilities
- Hard to debug           - Easy to test
- Slow responses          - Parallel execution
- Expensive               - Optimize per agent
```

---

### 3. RAG Over Fine-Tuning for Policies

**Why RAG (Retrieval-Augmented Generation)?**

```
Fine-Tuning:                      RAG:
┌──────────────┐                 ┌──────────────┐
│ Train model  │  Weeks          │ Index docs   │  Hours
│ on policies  │                 │ in ChromaDB  │
└──────┬───────┘                 └──────┬───────┘
       │                                │
       ▼                                ▼
┌──────────────┐                 ┌──────────────┐
│ Deploy model │                 │ Query time:  │
│              │                 │ 1. Search DB │
│ Issues:      │                 │ 2. Add to    │
│ - Updates?   │                 │    prompt    │
│ - Sources?   │                 │ 3. Generate  │
│ - Drift?     │                 └──────────────┘
└──────────────┘
                                  Benefits:
                                  - Always current
                                  - Shows sources
                                  - Easy updates
                                  - No retraining
```

---

### 4. Real-Time Streaming Architecture

**Why Kafka + Pinot?**

```
Traditional Batch:              Real-Time Streaming:
┌──────────────┐               ┌──────────────┐
│ Events → DB  │  Write        │ Events →     │  Write
└──────┬───────┘               │   Kafka      │
       │                       └──────┬───────┘
       ▼                              │
┌──────────────┐                     ▼
│ Run ETL      │  Hours         ┌──────────────┐
│ nightly      │                │ Pinot        │  Seconds
└──────┬───────┘                │ (Real-time)  │
       │                        └──────┬───────┘
       ▼                               │
┌──────────────┐                      ▼
│ Query DW     │                ┌──────────────┐
│ (stale data) │                │ Query        │
└──────────────┘                │ (live data)  │
                                └──────────────┘
Latency: Hours                  Latency: <1 second
```

---

### 5. Recall > Precision for Crisis Triage

**Priority: Don't miss high-risk cases**

```
Confusion Matrix:

                  Predicted High    Predicted Low
Actual High           TP                FN ← DANGEROUS!
Actual Low            FP ← OK           TN

Strategy:
- Target Recall: >95% (catch almost all high-risk)
- Acceptable Precision: >70% (some false positives OK)
- Better to over-escalate than miss critical cases
- Human review for flagged cases
```

---

## Data Flow

### Use Case 1: Policy Q&A

```
User Query → Dashboard → API (/knowledge/search)
                           ↓
                    Knowledge Agent
                           ↓
                    1. Embed query (OpenAI)
                    2. Search ChromaDB (vector similarity)
                    3. Retrieve top N documents
                    4. Add to prompt context
                           ↓
                    OpenAI GPT-4o
                           ↓
                    Generate answer with citations
                           ↓
                    Format response
                           ↓
                    Dashboard ← API
```

### Use Case 2: Crisis Triage

```
Crisis Event → Kafka → Pinot (ingestion)
                          ↓
User Query → Dashboard → API (/triage)
                           ↓
                    Triage Agent
                           ↓
                    1. Query Pinot (recent events)
                    2. Analyze patterns
                    3. Apply risk scoring
                    4. Generate recommendations
                           ↓
                    OpenAI GPT-4o
                           ↓
                    Structured recommendations
                           ↓
                    Dashboard ← API
```

### Use Case 3: BHOATR Reporting

```
Synthetic Data → JSON files → PostgreSQL (optional)
                                    ↓
User Request → Dashboard → API (/analytics)
                             ↓
                      Analytics Agent
                             ↓
                      1. Query data sources
                      2. Calculate metrics
                      3. Identify trends
                      4. Generate insights
                             ↓
                      Format report
                             ↓
                      Dashboard ← API
```

---

## Agent Architecture

### LangGraph State Machine

```python
from langgraph.graph import StateGraph

# Define agent workflow
workflow = StateGraph()

# Add nodes (agents)
workflow.add_node("classifier", classify_intent)
workflow.add_node("triage", triage_agent)
workflow.add_node("knowledge", knowledge_agent)
workflow.add_node("query", query_agent)
workflow.add_node("synthesizer", synthesize_response)

# Add edges (routing)
workflow.add_conditional_edges(
    "classifier",
    route_to_agent,
    {
        "crisis": "triage",
        "policy": "knowledge",
        "data": "query"
    }
)

workflow.add_edge("triage", "synthesizer")
workflow.add_edge("knowledge", "synthesizer")
workflow.add_edge("query", "synthesizer")

# Compile
app = workflow.compile()
```

### Prompt Engineering Best Practices

**Example: SQL Generation**

```python
SQL_GENERATION_PROMPT = """
You are a SQL expert for Apache Pinot.

Schema for dhcs_crisis_intake table:
- event_id (STRING)
- event_time_ms (LONG, milliseconds since epoch)
- county (STRING)
- risk_level (STRING: 'low', 'medium', 'high', 'critical')
- channel (STRING: '988', 'mobile', 'walk-in', 'er')
- age (INT)
- presenting_issue (STRING)
- outcome (STRING)

User Question: {question}

Think step-by-step:
1. What tables are needed?
2. What columns to SELECT?
3. What filters to apply (WHERE)?
4. Time range constraints?
5. Grouping or aggregation needed?
6. Order and limits?

Generate valid Pinot SQL:
"""
```

---

## Scalability Considerations

### Horizontal Scaling

**Component Scaling Strategy**:

| Component | Scale Method | Trigger | Notes |
|-----------|-------------|---------|-------|
| API | Add containers | CPU >70% | Stateless, easy |
| Dashboard | Add instances | Users >1000 | Session state |
| Pinot Broker | Add brokers | Query latency | Read scale |
| Pinot Server | Add servers | Data volume | Storage scale |
| Kafka | Add brokers | Throughput | Partition-based |

### Performance Optimizations

1. **Caching**: Redis for frequent queries
2. **Connection Pooling**: Database connections
3. **Async Processing**: Non-blocking I/O
4. **Query Optimization**: Pinot indexes
5. **Batch Processing**: Group similar requests

---

## Security Architecture

### Authentication & Authorization
- API keys for service-to-service
- OAuth2 for user authentication (planned)
- Role-based access control (RBAC)

### Data Protection
- No PHI in synthetic data
- Encryption in transit (TLS)
- Encryption at rest (planned)
- Audit logging

### Network Security
- Container network isolation
- Firewall rules
- Rate limiting
- DDoS protection (AWS WAF)

---

## Monitoring & Observability

### Metrics
- Request latency (p50, p95, p99)
- Error rates
- Agent execution times
- API usage by endpoint
- Database query performance

### Logging
- Structured JSON logs
- Centralized log aggregation
- Log levels: DEBUG, INFO, WARN, ERROR

### Alerting
- Service health checks
- Error rate thresholds
- Latency anomalies
- Data quality issues

---

## Next Steps

- [Use Cases Documentation](./04-USE-CASES.md)
- [Deployment Guide](./deployment/AWS.md)
- [API Reference](./development/API.md)
- [Agent Development](./development/AGENTS.md)
