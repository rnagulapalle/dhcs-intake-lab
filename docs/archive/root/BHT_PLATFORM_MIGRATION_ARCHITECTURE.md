# BHT Governed AI Platform Migration Architecture

## Executive Summary

This document provides a comprehensive migration plan to transform the current DHCS BHT Multi-Agent AI application into a BHT Governed AI Platform architecture. The migration preserves all existing user-facing features while introducing platform primitives for model governance, centralized retrieval, mandatory tracing, evaluation harness, and safe degradation.

**Current State**: Production multi-agent system with 19 agents, 2 orchestration pipelines, direct OpenAI calls, ChromaDB retrieval, and basic logging.

**Target State**: Governed AI platform with centralized model gateway, unified retrieval service, mandatory audit trails, evaluation gates, and reliability primitives.

---

# 1. CURRENT STATE ARCHITECTURE

## 1.1 Component Inventory

### Agents (19 Total)

| Agent | File | Purpose | LLM Calls | Retrieval |
|-------|------|---------|-----------|-----------|
| **Orchestrators** |
| AgentOrchestrator | `agents/core/orchestrator.py` | Crisis intake routing | Yes (intent classification) | No |
| CurationOrchestrator | `agents/core/curation_orchestrator.py` | Policy curation workflow | Yes (coordination) | Via RetrievalAgent |
| **Crisis/Analytics Agents** |
| QueryAgent | `agents/core/query_agent.py` | Data querying | Yes | Optional RAG |
| AnalyticsAgent | `agents/core/analytics_agent.py` | Trend analysis | Yes | No |
| TriageAgent | `agents/core/triage_agent.py` | Risk prioritization | Yes | No |
| RecommendationsAgent | `agents/core/recommendations_agent.py` | Operational recommendations | Yes | No |
| **Evidence-First Pipeline** |
| EvidenceExtractionAgent | `agents/core/evidence_extraction_agent.py` | Verbatim requirement extraction | Yes (temp=0.0) | No |
| GroundingVerificationAgent | `agents/core/grounding_verification_agent.py` | Evidence validation gate | Yes | No |
| EvidenceCompositionAgent | `agents/core/evidence_composition_agent.py` | Answer composition with REQ-IDs | Yes | No |
| **Legacy Curation Pipeline** |
| RetrievalAgent | `agents/core/retrieval_agent.py` | Document retrieval | No | Yes (ChromaDB) |
| StatuteAnalystAgent | `agents/core/statute_analyst_agent.py` | Legal statute analysis | Yes | No |
| PolicyAnalystAgent | `agents/core/policy_analyst_agent.py` | Policy interpretation | Yes | No |
| SynthesisAgent | `agents/core/synthesis_agent.py` | Final summary | Yes | No |
| QualityReviewerAgent | `agents/core/quality_reviewer_agent.py` | Output validation | Yes | No |

### API Endpoints (User-Facing - MUST PRESERVE)

| Endpoint | Method | Purpose | Handler |
|----------|--------|---------|---------|
| `/health` | GET | Health check | Direct |
| `/chat` | POST | Main chat (orchestrated) | AgentOrchestrator |
| `/query` | POST | Data queries | QueryAgent |
| `/analytics` | POST | Trend analysis | AnalyticsAgent |
| `/triage` | POST | Risk prioritization | TriageAgent |
| `/recommendations` | POST | Operational recommendations | RecommendationsAgent |
| `/knowledge/search` | POST | Knowledge base search | DHCSKnowledgeBase |
| `/knowledge/stats` | GET | KB statistics | DHCSKnowledgeBase |
| `/curation/process` | POST | Single policy question | CurationOrchestrator |
| `/curation/batch` | POST | Batch policy questions | CurationOrchestrator |
| `/curation/stats` | GET | Curation KB stats | DHCSKnowledgeBase |
| `/curation/diagnose` | POST | Quality diagnostics | QualityMonitor |

### Model Integration Points

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CURRENT LLM INTEGRATION                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐   │
│  │ BaseAgent   │────▶│ ChatOpenAI  │────▶│ OpenAI API          │   │
│  │ (all agents)│     │ (LangChain) │     │ (gpt-4o-mini)       │   │
│  └─────────────┘     └─────────────┘     └─────────────────────┘   │
│         │                   │                                       │
│         │                   ├── model: settings.agent_model         │
│         │                   ├── temperature: 0.0-0.7                │
│         │                   └── api_key: settings.openai_api_key    │
│         │                                                           │
│  Direct instantiation in each agent constructor                     │
│  No centralized routing, retry, or budget tracking                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Files with Direct Model Calls:**
- `agents/core/base_agent.py` - Base class with ChatOpenAI
- `agents/core/orchestrator.py` - Intent classification
- `agents/core/curation_orchestrator.py` - Coordination LLM
- `agents/core/query_agent.py`
- `agents/core/analytics_agent.py`
- `agents/core/triage_agent.py`
- `agents/core/recommendations_agent.py`
- `agents/core/evidence_extraction_agent.py`
- `agents/core/grounding_verification_agent.py`
- `agents/core/evidence_composition_agent.py`
- `agents/core/statute_analyst_agent.py`
- `agents/core/policy_analyst_agent.py`
- `agents/core/synthesis_agent.py`
- `agents/core/quality_reviewer_agent.py`
- `agents/prompts/optimized_prompts.py`

### Retrieval Integration Points

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CURRENT RETRIEVAL ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐     ┌─────────────┐     ┌─────────────────┐  │
│  │ DHCSKnowledgeBase│────▶│ ChromaDB    │────▶│ OpenAI          │  │
│  │ knowledge_base.py│     │ (local)     │     │ Embeddings      │  │
│  └──────────────────┘     └─────────────┘     └─────────────────┘  │
│           │                                                         │
│           ├── Persist: ./chroma_data                               │
│           ├── Collection: dhcs_bht_knowledge                       │
│           └── Chunking: 1000 chars, 200 overlap                    │
│                                                                     │
│  ┌──────────────────┐                                              │
│  │ RetrievalAgent   │──── Hybrid search (semantic + metadata)      │
│  │ retrieval_agent.py    Query enhancement                         │
│  └──────────────────┘     Statute catalog lookup                   │
│                                                                     │
│  ┌──────────────────┐                                              │
│  │ CurationLoader   │──── Loads MD/CSV to ChromaDB                 │
│  │ curation_loader.py    Metadata tagging                          │
│  └──────────────────┘                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Configuration Management

```
agents/core/config.py (Pydantic Settings):
├── openai_api_key: str (required)
├── agent_model: str = "gpt-4o-mini"
├── agent_temperature: float = 0.7
├── pinot_broker_url: str = "http://localhost:8099"
├── kafka_bootstrap_servers: str = "localhost:29092"
└── chroma_persist_dir: str = "./chroma_data"
```

### Logging/Observability (Current)

```python
# Current pattern (scattered across files):
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Usage:
logger.info(f"Processing question: {question[:100]}...")
logger.error(f"Error: {e}", exc_info=True)
```

**Issues:**
- No structured logging (JSON)
- No trace IDs or correlation
- No tenant/workflow context
- No audit metadata
- No centralized log aggregation config

## 1.2 Call Graph

```
                            ┌─────────────────────────────────────┐
                            │           API Layer                 │
                            │         api/main.py                 │
                            └─────────────┬───────────────────────┘
                                          │
          ┌───────────────────────────────┼───────────────────────────────┐
          │                               │                               │
          ▼                               ▼                               ▼
┌─────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────┐
│  AgentOrchestrator  │     │  CurationOrchestrator   │     │  DHCSKnowledgeBase  │
│   (LangGraph)       │     │     (LangGraph)         │     │    (ChromaDB)       │
└─────────┬───────────┘     └───────────┬─────────────┘     └─────────────────────┘
          │                             │
          │ Intent                      │ Workflow
          │ Classification              │ Execution
          ▼                             ▼
┌─────────────────────┐     ┌─────────────────────────────────────────────────────┐
│   Route to Agent    │     │              EVIDENCE-FIRST PIPELINE                │
│   ├─ QueryAgent     │     │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│   ├─ AnalyticsAgent │     │  │Retrieval │─▶│Extract   │─▶│Verify    │─▶...     │
│   ├─ TriageAgent    │     │  │Agent     │  │Agent     │  │Agent     │          │
│   └─ RecommendAgent │     │  └──────────┘  └──────────┘  └──────────┘          │
└─────────────────────┘     │                                                     │
          │                 │              LEGACY PIPELINE                        │
          │                 │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
          │                 │  │Statute   │─▶│Policy    │─▶│Synthesis │─▶...     │
          │                 │  │Analyst   │  │Analyst   │  │Agent     │          │
          │                 │  └──────────┘  └──────────┘  └──────────┘          │
          │                 └─────────────────────────────────────────────────────┘
          │                             │
          ▼                             ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              LLM CALLS (Direct)                                 │
│                                                                                 │
│   Each agent instantiates ChatOpenAI directly:                                  │
│   self.llm = ChatOpenAI(model=settings.agent_model, ...)                       │
│                                                                                 │
│   No centralized:                                                               │
│   - Routing / load balancing                                                    │
│   - Retry logic (beyond LangChain defaults)                                     │
│   - Budget tracking / rate limiting                                             │
│   - Model versioning                                                            │
│   - Fallback models                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 1.3 Deployment Architecture (Current)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            DOCKER COMPOSE STACK                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                         │
│  │  Zookeeper  │◀──▶│   Kafka     │◀──▶│   Pinot     │                         │
│  │   :2181     │    │  :9092      │    │ :8099/:9000 │                         │
│  └─────────────┘    └─────────────┘    └─────────────┘                         │
│                            │                  │                                 │
│                            ▼                  ▼                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                         │
│  │  Generator  │───▶│  agent-api  │◀───│  Dashboard  │                         │
│  │  (producer) │    │   :8000     │    │   :8501     │                         │
│  └─────────────┘    └──────┬──────┘    └─────────────┘                         │
│                            │                                                    │
│                     ┌──────▼──────┐                                            │
│                     │  ChromaDB   │                                            │
│                     │ (volume)    │                                            │
│                     └─────────────┘                                            │
│                                                                                 │
│  AWS Production: ECR → ECS/Fargate (via CodeBuild)                             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

# 2. GAP ANALYSIS

## 2.1 Gap Analysis Table

| # | Current Behavior | Target Behavior | Gap | Proposed Change | Risk |
|---|-----------------|-----------------|-----|-----------------|------|
| **MODEL GATEWAY** |
| G1 | Direct ChatOpenAI instantiation in each agent | Centralized ModelGateway with routing, retry, budget | No abstraction layer | Introduce `platform/model_gateway.py` | **M** |
| G2 | Single model (gpt-4o-mini) hardcoded | Multi-model support with routing rules | No model selection logic | Add model routing config | **L** |
| G3 | LangChain default retry only | Configurable retry with exponential backoff, circuit breaker | No custom reliability | Add retry/circuit breaker primitives | **M** |
| G4 | No budget/cost tracking | Per-tenant, per-workflow budget tags and limits | No cost visibility | Add budget tracking middleware | **L** |
| G5 | No timeout configuration | Configurable timeouts per operation type | Uses LangChain defaults | Add timeout policies | **L** |
| **RETRIEVAL SERVICE** |
| G6 | DHCSKnowledgeBase + RetrievalAgent tightly coupled | Centralized RetrievalService with unified API | Retrieval logic scattered | Extract to `platform/retrieval_service.py` | **M** |
| G7 | ChromaDB only, local persistence | Pluggable vector store backend | Vendor lock-in | Abstract vector store interface | **L** |
| G8 | Citations via REQ-ID in evidence pipeline only | Mandatory citation tracking for all retrievals | Inconsistent citation handling | Standardize citation format | **M** |
| G9 | No retrieval metrics | Track precision/recall, latency, cache hits | No retrieval observability | Add retrieval instrumentation | **L** |
| **AUDIT/TRACING** |
| G10 | Basic Python logging, no structure | Structured JSON logging with trace context | No audit trail | Introduce `platform/audit_context.py` | **H** |
| G11 | No request correlation | Request ID + Trace ID propagation | Cannot trace requests end-to-end | Add correlation middleware | **M** |
| G12 | No tenant/workflow context | Mandatory tenant_id, workflow_id, use_case tags | No multi-tenancy support | Add context injection | **M** |
| G13 | No audit metadata on LLM calls | Log prompts, responses, latency, tokens, cost | Compliance gap | Wrap all LLM calls with audit | **H** |
| G14 | Evidence audit trail in CurationState only | Centralized audit trail service | Audit logic in workflow | Extract to platform layer | **M** |
| **EVALUATION HARNESS** |
| G15 | Scripts in `/scripts/` (benchmark, LLM judge) | Integrated EvalHarness with CI gate | No automated quality gates | Create `platform/eval_harness.py` | **M** |
| G16 | Manual benchmark execution | Regression tests run on every PR | No CI integration | Add eval to CI pipeline | **M** |
| G17 | QualityReviewerAgent (runtime) | Offline eval + runtime quality check | Mixed concerns | Separate offline vs runtime eval | **L** |
| G18 | Ad-hoc scoring in scripts | Standardized scoring rubrics and thresholds | Inconsistent evaluation | Define eval contracts | **L** |
| **SAFE DEGRADATION** |
| G19 | No kill switch | Global and per-workflow kill switches | Cannot disable AI quickly | Add kill switch config | **H** |
| G20 | No fallback behavior | Graceful degradation to cached/static responses | Hard failure on errors | Define fallback policies | **M** |
| G21 | Basic try/except error handling | Structured error taxonomy with recovery actions | Inconsistent error handling | Standardize error types | **M** |
| G22 | No rollback capability | Version-tagged deployments with instant rollback | Cannot revert quickly | Add deployment versioning | **M** |
| **BOUNDARY VIOLATIONS** |
| G23 | Workflow logic mixed with infra (logging, retry) | Clean separation: /platform vs /workflows | Tight coupling | Refactor to clean boundaries | **M** |
| G24 | Agents know about OpenAI, ChromaDB directly | Agents use platform abstractions only | Leaky abstractions | Inject dependencies | **M** |
| G25 | Config scattered (env vars, Pydantic, hardcoded) | Centralized config with environment overrides | Config fragmentation | Consolidate to platform config | **L** |

## 2.2 Risk Assessment Summary

| Risk Level | Count | Items |
|------------|-------|-------|
| **High (H)** | 3 | G10 (structured logging), G13 (LLM audit), G19 (kill switch) |
| **Medium (M)** | 14 | G1, G3, G6, G8, G11, G12, G14, G15, G16, G20, G21, G22, G23, G24 |
| **Low (L)** | 8 | G2, G4, G5, G7, G9, G17, G18, G25 |

---

# 3. TARGET ARCHITECTURE

## 3.1 Module Structure

```
dhcs-intake-lab/
├── platform/                          # NEW: Platform primitives
│   ├── __init__.py
│   ├── model_gateway.py               # Centralized LLM access
│   ├── retrieval_service.py           # Unified retrieval API
│   ├── audit_context.py               # Tracing and audit metadata
│   ├── eval_harness.py                # Offline evaluation runner
│   ├── degradation_policy.py          # Kill switch and fallbacks
│   ├── config.py                      # Platform configuration
│   ├── errors.py                      # Error taxonomy
│   └── middleware/
│       ├── __init__.py
│       ├── tracing.py                 # Request correlation
│       ├── budget.py                  # Cost tracking
│       └── circuit_breaker.py         # Reliability primitives
│
├── workflows/                         # REFACTORED: Agent definitions
│   ├── __init__.py
│   ├── base_agent.py                  # Updated to use platform
│   ├── crisis_intake/                 # Crisis workflow agents
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── query_agent.py
│   │   ├── analytics_agent.py
│   │   ├── triage_agent.py
│   │   └── recommendations_agent.py
│   ├── policy_curation/               # Curation workflow agents
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── evidence_extraction.py
│   │   ├── grounding_verification.py
│   │   ├── evidence_composition.py
│   │   ├── statute_analyst.py         # Legacy
│   │   ├── policy_analyst.py          # Legacy
│   │   ├── synthesis.py               # Legacy
│   │   └── quality_reviewer.py
│   └── prompts/
│       └── optimized_prompts.py
│
├── services/                          # REFACTORED: API and integrations
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app
│   │   ├── routes/
│   │   │   ├── chat.py
│   │   │   ├── curation.py
│   │   │   ├── knowledge.py
│   │   │   └── health.py
│   │   └── middleware.py              # CORS, auth, etc.
│   ├── dashboard/                     # Streamlit UI
│   │   └── streamlit_app.py
│   └── integrations/
│       ├── kafka_producer.py
│       └── pinot_client.py
│
├── knowledge/                         # MOVED: Knowledge base
│   ├── __init__.py
│   ├── knowledge_base.py
│   └── curation_loader.py
│
├── data/                              # Unchanged
├── scripts/                           # Unchanged (deprecated for eval)
├── tests/                             # Enhanced
│   ├── unit/
│   ├── integration/
│   └── eval/                          # Offline evaluation tests
└── deployment/                        # Unchanged
```

## 3.2 ASCII Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         BHT GOVERNED AI PLATFORM                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                           SERVICES LAYER                                 │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │   │
│  │  │  FastAPI    │    │  Streamlit  │    │ Integrations│                  │   │
│  │  │  /api       │    │  /dashboard │    │ Kafka/Pinot │                  │   │
│  │  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                  │   │
│  └─────────┼──────────────────┼──────────────────┼──────────────────────────┘   │
│            │                  │                  │                               │
│            └──────────────────┼──────────────────┘                               │
│                               │                                                  │
│  ┌────────────────────────────▼────────────────────────────────────────────┐   │
│  │                         WORKFLOWS LAYER                                  │   │
│  │                                                                          │   │
│  │  ┌──────────────────────┐    ┌──────────────────────┐                   │   │
│  │  │   Crisis Intake      │    │   Policy Curation    │                   │   │
│  │  │   Workflow           │    │   Workflow           │                   │   │
│  │  │  ┌────────────────┐  │    │  ┌────────────────┐  │                   │   │
│  │  │  │ Orchestrator   │  │    │  │ Orchestrator   │  │                   │   │
│  │  │  │ (LangGraph)    │  │    │  │ (LangGraph)    │  │                   │   │
│  │  │  └───────┬────────┘  │    │  └───────┬────────┘  │                   │   │
│  │  │          │           │    │          │           │                   │   │
│  │  │  ┌───────▼────────┐  │    │  ┌───────▼────────┐  │                   │   │
│  │  │  │ Query │ Triage │  │    │  │ Extract│Verify │  │                   │   │
│  │  │  │ Agent │ Agent  │  │    │  │ Agent │ Agent  │  │                   │   │
│  │  │  └────────────────┘  │    │  └────────────────┘  │                   │   │
│  │  └──────────────────────┘    └──────────────────────┘                   │   │
│  │                                                                          │   │
│  │  Agents call ONLY platform abstractions (no direct LLM/DB access)       │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                               │                                                  │
│  ┌────────────────────────────▼────────────────────────────────────────────┐   │
│  │                         PLATFORM LAYER                                   │   │
│  │                                                                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │   Model     │  │  Retrieval  │  │   Audit     │  │   Eval      │    │   │
│  │  │   Gateway   │  │  Service    │  │   Context   │  │   Harness   │    │   │
│  │  │             │  │             │  │             │  │             │    │   │
│  │  │ • Routing   │  │ • Search    │  │ • Trace ID  │  │ • Offline   │    │   │
│  │  │ • Retry     │  │ • Citations │  │ • Tenant    │  │ • Scoring   │    │   │
│  │  │ • Budget    │  │ • Filters   │  │ • Workflow  │  │ • CI Gate   │    │   │
│  │  │ • Timeout   │  │ • Cache     │  │ • Audit Log │  │ • Rubrics   │    │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────┘    │   │
│  │         │                │                │                             │   │
│  │  ┌──────▼────────────────▼────────────────▼──────┐                     │   │
│  │  │              Degradation Policy               │                     │   │
│  │  │  • Kill Switch  • Fallbacks  • Circuit Breaker│                     │   │
│  │  └───────────────────────────────────────────────┘                     │   │
│  │                                                                          │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                               │                                                  │
│  ┌────────────────────────────▼────────────────────────────────────────────┐   │
│  │                       EXTERNAL SERVICES                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │   OpenAI    │  │  ChromaDB   │  │   Kafka     │  │   Pinot     │    │   │
│  │  │   API       │  │  (Vector)   │  │  (Events)   │  │  (OLAP)     │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 3.3 Module Dependency Graph

```
                    ┌─────────────────┐
                    │    services/    │
                    │   (API, UI)     │
                    └────────┬────────┘
                             │ imports
                             ▼
                    ┌─────────────────┐
                    │   workflows/    │
                    │   (Agents)      │
                    └────────┬────────┘
                             │ imports
                             ▼
                    ┌─────────────────┐
                    │   platform/     │◀──────────────┐
                    │  (Primitives)   │               │
                    └────────┬────────┘               │
                             │ imports                │
              ┌──────────────┼──────────────┐        │
              ▼              ▼              ▼        │
        ┌──────────┐  ┌──────────┐  ┌──────────┐   │
        │ langchain│  │ chromadb │  │ pydantic │   │
        │ openai   │  │          │  │ logging  │   │
        └──────────┘  └──────────┘  └──────────┘   │
                                                    │
                    ┌─────────────────┐             │
                    │   knowledge/    │─────────────┘
                    │  (Data Layer)   │  (used by platform)
                    └─────────────────┘

RULE: Arrows point DOWN only. No upward dependencies allowed.
      workflows/ never imports from services/
      platform/ never imports from workflows/ or services/
```

---

# 4. INCREMENTAL MIGRATION PLAN

## Phase 0: Shim Layer (Foundation)

**Goal**: Introduce platform adapters that wrap existing calls without changing behavior.

### Deliverables
1. Create `/platform` directory structure
2. Implement `ModelGatewayShim` - wrapper around existing ChatOpenAI calls
3. Implement `RetrievalServiceShim` - wrapper around DHCSKnowledgeBase
4. Implement `AuditContextShim` - adds trace_id to existing logging
5. Update `BaseAgent` to use shims (optional injection)

### Files Impacted
| File | Change Type | Description |
|------|-------------|-------------|
| `platform/__init__.py` | NEW | Package init |
| `platform/model_gateway.py` | NEW | ModelGatewayShim class |
| `platform/retrieval_service.py` | NEW | RetrievalServiceShim class |
| `platform/audit_context.py` | NEW | AuditContextShim class |
| `platform/config.py` | NEW | Platform configuration |
| `agents/core/base_agent.py` | MODIFY | Accept optional gateway injection |

### Test Strategy
- Unit tests for each shim (verify pass-through behavior)
- Integration test: existing API endpoints return identical responses
- Regression: run existing benchmark suite, compare scores

---

## Phase 1: Centralize Model Gateway

**Goal**: All LLM calls route through ModelGateway with retry, timeout, and routing.

### Deliverables
1. Full `ModelGateway` implementation with:
   - Model routing (default, fallback)
   - Configurable retry with exponential backoff
   - Timeout policies
   - Budget tags (tenant, workflow, operation)
2. `CircuitBreaker` primitive
3. Update all agents to use `ModelGateway.invoke()`
4. Remove direct `ChatOpenAI` instantiation from agents

### Files Impacted
| File | Change Type | Description |
|------|-------------|-------------|
| `platform/model_gateway.py` | MODIFY | Full implementation |
| `platform/middleware/circuit_breaker.py` | NEW | Circuit breaker |
| `platform/middleware/budget.py` | NEW | Budget tracking |
| `agents/core/base_agent.py` | MODIFY | Use gateway exclusively |
| `agents/core/orchestrator.py` | MODIFY | Use gateway |
| `agents/core/curation_orchestrator.py` | MODIFY | Use gateway |
| `agents/core/query_agent.py` | MODIFY | Remove direct LLM |
| `agents/core/analytics_agent.py` | MODIFY | Remove direct LLM |
| `agents/core/triage_agent.py` | MODIFY | Remove direct LLM |
| `agents/core/recommendations_agent.py` | MODIFY | Remove direct LLM |
| `agents/core/evidence_extraction_agent.py` | MODIFY | Remove direct LLM |
| `agents/core/grounding_verification_agent.py` | MODIFY | Remove direct LLM |
| `agents/core/evidence_composition_agent.py` | MODIFY | Remove direct LLM |
| `agents/core/statute_analyst_agent.py` | MODIFY | Remove direct LLM |
| `agents/core/policy_analyst_agent.py` | MODIFY | Remove direct LLM |
| `agents/core/synthesis_agent.py` | MODIFY | Remove direct LLM |
| `agents/core/quality_reviewer_agent.py` | MODIFY | Remove direct LLM |

### Test Strategy
- Unit tests for ModelGateway (routing, retry, timeout, circuit breaker)
- Mock LLM responses to test retry behavior
- Integration: verify all endpoints work with gateway
- Performance: measure latency overhead (should be < 5ms)

---

## Phase 2: Centralize Retrieval + Citations

**Goal**: Unified RetrievalService with standardized citation tracking.

### Deliverables
1. Full `RetrievalService` implementation with:
   - Unified search API (semantic, keyword, hybrid)
   - Metadata filtering
   - Citation tracking (source, chunk_id, relevance_score)
   - Caching layer
2. Citation format standardization
3. Update RetrievalAgent to use RetrievalService
4. Update knowledge endpoints to use RetrievalService

### Files Impacted
| File | Change Type | Description |
|------|-------------|-------------|
| `platform/retrieval_service.py` | MODIFY | Full implementation |
| `platform/middleware/cache.py` | NEW | Retrieval cache |
| `agents/core/retrieval_agent.py` | MODIFY | Use RetrievalService |
| `agents/knowledge/knowledge_base.py` | MODIFY | Delegate to platform |
| `api/main.py` | MODIFY | Update knowledge endpoints |

### Test Strategy
- Unit tests for RetrievalService (search, filter, cache)
- Citation format validation tests
- Integration: `/knowledge/search` returns citations
- Regression: curation pipeline produces same quality scores

---

## Phase 3: Mandatory Tracing/Audit Metadata

**Goal**: Every request has trace_id, tenant context, and audit logging.

### Deliverables
1. Full `AuditContext` implementation with:
   - Request ID generation
   - Trace ID propagation
   - Tenant/workflow/use_case context
   - Structured JSON logging
2. `TracingMiddleware` for FastAPI
3. Audit logging for all LLM calls (prompt, response, tokens, latency)
4. Audit logging for all retrieval calls

### Files Impacted
| File | Change Type | Description |
|------|-------------|-------------|
| `platform/audit_context.py` | MODIFY | Full implementation |
| `platform/middleware/tracing.py` | NEW | FastAPI middleware |
| `platform/model_gateway.py` | MODIFY | Add audit logging |
| `platform/retrieval_service.py` | MODIFY | Add audit logging |
| `api/main.py` | MODIFY | Add tracing middleware |
| `agents/core/curation_orchestrator.py` | MODIFY | Use AuditContext |

### Test Strategy
- Unit tests for AuditContext (ID generation, context propagation)
- Integration: verify trace_id appears in all log entries
- Verify audit logs contain required fields (prompt, response, tokens)
- Load test: ensure logging doesn't impact latency significantly

---

## Phase 4: Evaluation Harness + CI Gate

**Goal**: Automated quality evaluation with CI blocking on regressions.

### Deliverables
1. `EvalHarness` implementation with:
   - Offline regression test runner
   - Scoring rubrics (accuracy, grounding, completeness)
   - Threshold configuration
   - CI integration hooks
2. Migrate benchmark scripts to EvalHarness
3. GitHub Actions workflow for eval gate
4. Eval dashboard/reporting

### Files Impacted
| File | Change Type | Description |
|------|-------------|-------------|
| `platform/eval_harness.py` | NEW | Evaluation runner |
| `platform/eval_rubrics.py` | NEW | Scoring definitions |
| `tests/eval/test_curation_quality.py` | NEW | Curation eval tests |
| `tests/eval/test_crisis_intake.py` | NEW | Crisis eval tests |
| `.github/workflows/eval.yml` | NEW | CI workflow |
| `scripts/run_benchmark.py` | DEPRECATE | Move to EvalHarness |

### Test Strategy
- Unit tests for EvalHarness (scoring, thresholds)
- Run eval suite against known-good baseline
- CI integration test (PR blocked on low score)
- Verify eval results match legacy benchmark scores

---

## Phase 5: Safe Degradation + Kill Switch

**Goal**: Graceful failure handling with instant disable capability.

### Deliverables
1. `DegradationPolicy` implementation with:
   - Global kill switch
   - Per-workflow kill switch
   - Fallback behavior configuration
   - Cached/static response fallbacks
2. Kill switch admin endpoint
3. Circuit breaker integration with degradation
4. Rollback procedure documentation

### Files Impacted
| File | Change Type | Description |
|------|-------------|-------------|
| `platform/degradation_policy.py` | NEW | Degradation logic |
| `platform/config.py` | MODIFY | Kill switch config |
| `platform/model_gateway.py` | MODIFY | Check kill switch |
| `platform/retrieval_service.py` | MODIFY | Check kill switch |
| `api/main.py` | MODIFY | Add admin endpoints |
| `api/routes/admin.py` | NEW | Kill switch endpoint |

### Test Strategy
- Unit tests for DegradationPolicy (kill switch, fallbacks)
- Integration: verify kill switch disables AI responses
- Verify fallback responses are returned when AI disabled
- Chaos testing: simulate failures, verify graceful degradation

---

# 5. CONCRETE WORK ITEMS

## 5.1 PR Checklist (Ordered Commits)

### Phase 0 PRs
```
□ PR-0.1: Create platform/ directory structure
  - Add platform/__init__.py
  - Add platform/config.py (PlatformConfig dataclass)
  - Add platform/errors.py (error taxonomy)

□ PR-0.2: Implement ModelGatewayShim
  - Add platform/model_gateway.py (shim only)
  - Unit tests for shim

□ PR-0.3: Implement RetrievalServiceShim
  - Add platform/retrieval_service.py (shim only)
  - Unit tests for shim

□ PR-0.4: Implement AuditContextShim
  - Add platform/audit_context.py (shim only)
  - Unit tests for shim

□ PR-0.5: Wire shims into BaseAgent
  - Modify agents/core/base_agent.py
  - Integration tests
```

### Phase 1 PRs
```
□ PR-1.1: Implement CircuitBreaker
  - Add platform/middleware/circuit_breaker.py
  - Unit tests

□ PR-1.2: Implement full ModelGateway
  - Modify platform/model_gateway.py
  - Add retry, timeout, routing logic
  - Unit tests

□ PR-1.3: Migrate orchestrators to ModelGateway
  - Modify agents/core/orchestrator.py
  - Modify agents/core/curation_orchestrator.py
  - Integration tests

□ PR-1.4: Migrate crisis agents to ModelGateway
  - Modify query_agent, analytics_agent, triage_agent, recommendations_agent
  - Integration tests

□ PR-1.5: Migrate curation agents to ModelGateway
  - Modify all curation pipeline agents
  - Integration tests
```

### Phase 2 PRs
```
□ PR-2.1: Implement full RetrievalService
  - Modify platform/retrieval_service.py
  - Add citation tracking
  - Unit tests

□ PR-2.2: Add retrieval caching
  - Add platform/middleware/cache.py
  - Unit tests

□ PR-2.3: Migrate RetrievalAgent
  - Modify agents/core/retrieval_agent.py
  - Integration tests

□ PR-2.4: Update knowledge endpoints
  - Modify api/main.py knowledge routes
  - Integration tests
```

### Phase 3 PRs
```
□ PR-3.1: Implement full AuditContext
  - Modify platform/audit_context.py
  - Add structured logging
  - Unit tests

□ PR-3.2: Add TracingMiddleware
  - Add platform/middleware/tracing.py
  - Integration tests

□ PR-3.3: Add audit logging to ModelGateway
  - Modify platform/model_gateway.py
  - Verify audit logs

□ PR-3.4: Add audit logging to RetrievalService
  - Modify platform/retrieval_service.py
  - Verify audit logs

□ PR-3.5: Wire tracing into FastAPI
  - Modify api/main.py
  - End-to-end tracing test
```

### Phase 4 PRs
```
□ PR-4.1: Implement EvalHarness
  - Add platform/eval_harness.py
  - Add platform/eval_rubrics.py
  - Unit tests

□ PR-4.2: Create eval test suite
  - Add tests/eval/test_curation_quality.py
  - Add tests/eval/test_crisis_intake.py

□ PR-4.3: Add CI eval workflow
  - Add .github/workflows/eval.yml
  - Verify CI blocking
```

### Phase 5 PRs
```
□ PR-5.1: Implement DegradationPolicy
  - Add platform/degradation_policy.py
  - Unit tests

□ PR-5.2: Add kill switch to gateway
  - Modify platform/model_gateway.py
  - Modify platform/retrieval_service.py
  - Integration tests

□ PR-5.3: Add admin endpoints
  - Add api/routes/admin.py
  - End-to-end kill switch test
```

## 5.2 Code Skeletons and Interfaces

### ModelGateway Interface

```python
# platform/model_gateway.py
"""
Centralized Model Gateway for all LLM operations.
Provides routing, retry, timeout, budget tracking, and audit logging.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import logging
import time
from contextlib import contextmanager

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage

from platform.config import PlatformConfig
from platform.audit_context import AuditContext
from platform.middleware.circuit_breaker import CircuitBreaker
from platform.errors import ModelGatewayError, ModelTimeoutError, ModelRateLimitError

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model tiers for routing decisions."""
    PRIMARY = "primary"
    FALLBACK = "fallback"
    BUDGET = "budget"


@dataclass
class ModelInvocationResult:
    """Result of a model invocation."""
    content: str
    model_used: str
    latency_ms: float
    tokens_used: int
    cost_estimate: float
    trace_id: str
    retries: int = 0


@dataclass
class BudgetTags:
    """Budget tracking tags for cost attribution."""
    tenant_id: str
    workflow_id: str
    operation: str
    use_case: Optional[str] = None


@dataclass
class ModelConfig:
    """Configuration for a model."""
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_base_delay: float = 1.0


class ModelGateway:
    """
    Centralized gateway for all LLM operations.

    Features:
    - Model routing (primary/fallback/budget)
    - Configurable retry with exponential backoff
    - Timeout enforcement
    - Circuit breaker for fault tolerance
    - Budget tracking and cost attribution
    - Audit logging for compliance

    Usage:
        gateway = ModelGateway(config)
        result = gateway.invoke(
            messages=[HumanMessage(content="Hello")],
            budget_tags=BudgetTags(tenant_id="county_la", workflow_id="curation", operation="synthesis"),
            audit_context=AuditContext.current()
        )
    """

    def __init__(self, config: Optional[PlatformConfig] = None):
        self.config = config or PlatformConfig()
        self._models: Dict[ModelTier, ChatOpenAI] = {}
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_threshold,
            recovery_timeout=self.config.circuit_breaker_recovery_seconds
        )
        self._initialize_models()

    def _initialize_models(self) -> None:
        """Initialize model instances for each tier."""
        self._models[ModelTier.PRIMARY] = ChatOpenAI(
            model=self.config.primary_model,
            temperature=self.config.default_temperature,
            openai_api_key=self.config.openai_api_key,
        )

        if self.config.fallback_model:
            self._models[ModelTier.FALLBACK] = ChatOpenAI(
                model=self.config.fallback_model,
                temperature=self.config.default_temperature,
                openai_api_key=self.config.openai_api_key,
            )

    def invoke(
        self,
        messages: List[BaseMessage],
        budget_tags: BudgetTags,
        audit_context: Optional[AuditContext] = None,
        model_config: Optional[ModelConfig] = None,
        tier: ModelTier = ModelTier.PRIMARY,
    ) -> ModelInvocationResult:
        """
        Invoke model with full platform guarantees.

        Args:
            messages: List of messages to send to model
            budget_tags: Cost attribution tags
            audit_context: Tracing and audit context
            model_config: Override default model configuration
            tier: Which model tier to use

        Returns:
            ModelInvocationResult with response and metadata

        Raises:
            ModelGatewayError: On unrecoverable failure
            ModelTimeoutError: On timeout after retries
        """
        config = model_config or ModelConfig(model_name=self.config.primary_model)
        audit = audit_context or AuditContext.current()

        # Check kill switch
        if self._is_killed(budget_tags.workflow_id):
            return self._fallback_response(messages, budget_tags, audit, "kill_switch")

        # Check circuit breaker
        if not self._circuit_breaker.allow_request():
            logger.warning(f"Circuit breaker open, using fallback for {budget_tags.operation}")
            return self._invoke_with_fallback(messages, budget_tags, audit, config)

        start_time = time.time()
        last_error = None

        for attempt in range(config.max_retries):
            try:
                result = self._invoke_single(
                    messages=messages,
                    tier=tier,
                    config=config,
                    timeout=config.timeout_seconds
                )

                latency_ms = (time.time() - start_time) * 1000

                # Record success
                self._circuit_breaker.record_success()

                # Audit log
                self._audit_invocation(
                    messages=messages,
                    result=result,
                    budget_tags=budget_tags,
                    audit_context=audit,
                    latency_ms=latency_ms,
                    retries=attempt
                )

                return ModelInvocationResult(
                    content=result.content,
                    model_used=config.model_name,
                    latency_ms=latency_ms,
                    tokens_used=self._estimate_tokens(messages, result.content),
                    cost_estimate=self._estimate_cost(config.model_name, messages, result.content),
                    trace_id=audit.trace_id,
                    retries=attempt
                )

            except Exception as e:
                last_error = e
                self._circuit_breaker.record_failure()

                if attempt < config.max_retries - 1:
                    delay = config.retry_base_delay * (2 ** attempt)
                    logger.warning(f"Model invocation failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    time.sleep(delay)

        # All retries exhausted
        logger.error(f"Model invocation failed after {config.max_retries} attempts: {last_error}")
        raise ModelGatewayError(f"Model invocation failed: {last_error}")

    def _invoke_single(
        self,
        messages: List[BaseMessage],
        tier: ModelTier,
        config: ModelConfig,
        timeout: float
    ) -> Any:
        """Single invocation attempt."""
        model = self._models.get(tier, self._models[ModelTier.PRIMARY])
        # Implementation with timeout
        return model.invoke(messages)

    def _invoke_with_fallback(
        self,
        messages: List[BaseMessage],
        budget_tags: BudgetTags,
        audit: AuditContext,
        config: ModelConfig
    ) -> ModelInvocationResult:
        """Invoke using fallback model."""
        if ModelTier.FALLBACK in self._models:
            return self.invoke(
                messages=messages,
                budget_tags=budget_tags,
                audit_context=audit,
                model_config=config,
                tier=ModelTier.FALLBACK
            )
        return self._fallback_response(messages, budget_tags, audit, "circuit_breaker")

    def _fallback_response(
        self,
        messages: List[BaseMessage],
        budget_tags: BudgetTags,
        audit: AuditContext,
        reason: str
    ) -> ModelInvocationResult:
        """Return fallback response when AI is disabled."""
        fallback_content = (
            "AI service is temporarily unavailable. "
            "Please try again later or contact support."
        )
        return ModelInvocationResult(
            content=fallback_content,
            model_used="fallback_static",
            latency_ms=0,
            tokens_used=0,
            cost_estimate=0,
            trace_id=audit.trace_id,
        )

    def _is_killed(self, workflow_id: str) -> bool:
        """Check if workflow is killed."""
        # Will be implemented with DegradationPolicy
        return False

    def _audit_invocation(
        self,
        messages: List[BaseMessage],
        result: Any,
        budget_tags: BudgetTags,
        audit_context: AuditContext,
        latency_ms: float,
        retries: int
    ) -> None:
        """Log audit entry for invocation."""
        audit_context.log_llm_call(
            prompt=[m.content for m in messages],
            response=result.content,
            model=self.config.primary_model,
            latency_ms=latency_ms,
            tokens=self._estimate_tokens(messages, result.content),
            budget_tags=budget_tags,
            retries=retries
        )

    def _estimate_tokens(self, messages: List[BaseMessage], response: str) -> int:
        """Estimate token usage."""
        # Rough estimation: 4 chars per token
        input_chars = sum(len(m.content) for m in messages)
        output_chars = len(response)
        return (input_chars + output_chars) // 4

    def _estimate_cost(self, model: str, messages: List[BaseMessage], response: str) -> float:
        """Estimate cost in dollars."""
        tokens = self._estimate_tokens(messages, response)
        # gpt-4o-mini pricing: ~$0.15 per 1M input, ~$0.60 per 1M output
        return tokens * 0.0000003
```

### RetrievalService Interface

```python
# platform/retrieval_service.py
"""
Centralized Retrieval Service for all document retrieval operations.
Provides unified search API, citation tracking, caching, and audit logging.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import logging
import hashlib
import time

from platform.config import PlatformConfig
from platform.audit_context import AuditContext
from platform.errors import RetrievalError

logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """Search strategy options."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


@dataclass
class Citation:
    """Standardized citation format."""
    source_id: str
    source_name: str
    chunk_id: str
    content: str
    relevance_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_reference(self) -> str:
        """Generate reference string for inline citation."""
        return f"[{self.source_id}:{self.chunk_id}]"


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""
    chunks: List[Dict[str, Any]]
    citations: List[Citation]
    query: str
    strategy: SearchStrategy
    latency_ms: float
    cache_hit: bool
    trace_id: str


@dataclass
class RetrievalFilters:
    """Filters for retrieval queries."""
    categories: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    date_range: Optional[tuple] = None
    metadata: Optional[Dict[str, Any]] = None
    exclude_toc: bool = True


class RetrievalService:
    """
    Centralized service for document retrieval.

    Features:
    - Unified search API (semantic, keyword, hybrid)
    - Standardized citation tracking
    - Configurable caching
    - Metadata filtering
    - Audit logging

    Usage:
        service = RetrievalService(config, knowledge_base)
        result = service.search(
            query="mobile crisis team response time",
            filters=RetrievalFilters(categories=["policy"]),
            strategy=SearchStrategy.HYBRID,
            n_results=5,
            audit_context=AuditContext.current()
        )
    """

    def __init__(
        self,
        config: Optional[PlatformConfig] = None,
        knowledge_base: Any = None  # DHCSKnowledgeBase
    ):
        self.config = config or PlatformConfig()
        self.knowledge_base = knowledge_base
        self._cache: Dict[str, RetrievalResult] = {}
        self._cache_ttl = self.config.retrieval_cache_ttl_seconds

    def search(
        self,
        query: str,
        filters: Optional[RetrievalFilters] = None,
        strategy: SearchStrategy = SearchStrategy.HYBRID,
        n_results: int = 5,
        audit_context: Optional[AuditContext] = None,
    ) -> RetrievalResult:
        """
        Search documents with citation tracking.

        Args:
            query: Search query
            filters: Optional filters to apply
            strategy: Search strategy to use
            n_results: Number of results to return
            audit_context: Tracing and audit context

        Returns:
            RetrievalResult with chunks, citations, and metadata
        """
        audit = audit_context or AuditContext.current()
        filters = filters or RetrievalFilters()

        # Check cache
        cache_key = self._cache_key(query, filters, strategy, n_results)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return RetrievalResult(
                chunks=cached.chunks,
                citations=cached.citations,
                query=query,
                strategy=strategy,
                latency_ms=0,
                cache_hit=True,
                trace_id=audit.trace_id
            )

        start_time = time.time()

        try:
            # Execute search based on strategy
            if strategy == SearchStrategy.SEMANTIC:
                chunks = self._semantic_search(query, filters, n_results)
            elif strategy == SearchStrategy.KEYWORD:
                chunks = self._keyword_search(query, filters, n_results)
            else:  # HYBRID
                chunks = self._hybrid_search(query, filters, n_results)

            # Generate citations
            citations = self._generate_citations(chunks)

            latency_ms = (time.time() - start_time) * 1000

            result = RetrievalResult(
                chunks=chunks,
                citations=citations,
                query=query,
                strategy=strategy,
                latency_ms=latency_ms,
                cache_hit=False,
                trace_id=audit.trace_id
            )

            # Cache result
            self._cache[cache_key] = result

            # Audit log
            self._audit_retrieval(query, result, audit)

            return result

        except Exception as e:
            logger.error(f"Retrieval failed for query '{query[:50]}...': {e}")
            raise RetrievalError(f"Retrieval failed: {e}")

    def search_statutes(
        self,
        query: str,
        statute_sections: Optional[List[str]] = None,
        audit_context: Optional[AuditContext] = None,
    ) -> RetrievalResult:
        """Search statute documents specifically."""
        filters = RetrievalFilters(
            categories=["statute"],
            metadata={"sections": statute_sections} if statute_sections else None
        )
        return self.search(
            query=query,
            filters=filters,
            strategy=SearchStrategy.HYBRID,
            audit_context=audit_context
        )

    def search_policies(
        self,
        query: str,
        policy_sections: Optional[List[str]] = None,
        audit_context: Optional[AuditContext] = None,
    ) -> RetrievalResult:
        """Search policy documents specifically."""
        filters = RetrievalFilters(
            categories=["policy"],
            metadata={"sections": policy_sections} if policy_sections else None
        )
        return self.search(
            query=query,
            filters=filters,
            strategy=SearchStrategy.HYBRID,
            audit_context=audit_context
        )

    def _semantic_search(
        self,
        query: str,
        filters: RetrievalFilters,
        n_results: int
    ) -> List[Dict[str, Any]]:
        """Execute semantic search."""
        # Delegate to knowledge base
        return self.knowledge_base.search(query, n_results=n_results)

    def _keyword_search(
        self,
        query: str,
        filters: RetrievalFilters,
        n_results: int
    ) -> List[Dict[str, Any]]:
        """Execute keyword search."""
        # Implementation
        return []

    def _hybrid_search(
        self,
        query: str,
        filters: RetrievalFilters,
        n_results: int
    ) -> List[Dict[str, Any]]:
        """Execute hybrid search (semantic + keyword)."""
        semantic_results = self._semantic_search(query, filters, n_results)
        # Combine with keyword results
        return semantic_results

    def _generate_citations(self, chunks: List[Dict[str, Any]]) -> List[Citation]:
        """Generate standardized citations from chunks."""
        citations = []
        for i, chunk in enumerate(chunks):
            citations.append(Citation(
                source_id=chunk.get("metadata", {}).get("source", f"src_{i}"),
                source_name=chunk.get("metadata", {}).get("source_name", "Unknown"),
                chunk_id=f"chunk_{i}",
                content=chunk.get("content", ""),
                relevance_score=chunk.get("score", 0.0),
                metadata=chunk.get("metadata", {})
            ))
        return citations

    def _cache_key(
        self,
        query: str,
        filters: RetrievalFilters,
        strategy: SearchStrategy,
        n_results: int
    ) -> str:
        """Generate cache key."""
        key_data = f"{query}|{filters}|{strategy.value}|{n_results}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _audit_retrieval(
        self,
        query: str,
        result: RetrievalResult,
        audit_context: AuditContext
    ) -> None:
        """Log audit entry for retrieval."""
        audit_context.log_retrieval(
            query=query,
            n_results=len(result.chunks),
            strategy=result.strategy.value,
            latency_ms=result.latency_ms,
            cache_hit=result.cache_hit
        )

    def clear_cache(self) -> None:
        """Clear retrieval cache."""
        self._cache.clear()
        logger.info("Retrieval cache cleared")
```

### AuditContext Interface

```python
# platform/audit_context.py
"""
Audit Context for tracing and compliance logging.
Provides trace ID propagation, tenant context, and structured audit logging.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from contextvars import ContextVar
import logging
import json
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Context variable for request-scoped audit context
_audit_context: ContextVar[Optional["AuditContext"]] = ContextVar(
    "audit_context", default=None
)


@dataclass
class AuditContext:
    """
    Request-scoped audit context for tracing and compliance.

    Features:
    - Unique request and trace IDs
    - Tenant and workflow context
    - Structured JSON audit logging
    - LLM call logging (prompt, response, tokens, cost)
    - Retrieval call logging

    Usage:
        # In middleware
        with AuditContext.create(tenant_id="county_la", workflow_id="curation") as ctx:
            # All operations within this context will have trace_id
            result = gateway.invoke(messages, audit_context=ctx)

        # Or get current context
        ctx = AuditContext.current()
    """

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default"
    workflow_id: str = "unknown"
    use_case: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # Accumulated audit entries
    _entries: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        tenant_id: str = "default",
        workflow_id: str = "unknown",
        use_case: str = "",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        parent_trace_id: Optional[str] = None,
    ) -> "AuditContext":
        """
        Create new audit context and set as current.

        Args:
            tenant_id: Tenant identifier (e.g., county code)
            workflow_id: Workflow identifier (e.g., curation, crisis_intake)
            use_case: Specific use case within workflow
            user_id: Optional user identifier
            session_id: Optional session identifier
            parent_trace_id: Optional parent trace for distributed tracing

        Returns:
            New AuditContext instance
        """
        ctx = cls(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            use_case=use_case,
            user_id=user_id,
            session_id=session_id,
            trace_id=parent_trace_id or str(uuid.uuid4())
        )
        _audit_context.set(ctx)
        return ctx

    @classmethod
    def current(cls) -> "AuditContext":
        """
        Get current audit context or create default.

        Returns:
            Current AuditContext or new default instance
        """
        ctx = _audit_context.get()
        if ctx is None:
            ctx = cls()
            _audit_context.set(ctx)
        return ctx

    def __enter__(self) -> "AuditContext":
        _audit_context.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.flush()
        _audit_context.set(None)

    def log_llm_call(
        self,
        prompt: List[str],
        response: str,
        model: str,
        latency_ms: float,
        tokens: int,
        budget_tags: Any = None,
        retries: int = 0,
        error: Optional[str] = None,
    ) -> None:
        """
        Log LLM invocation for audit trail.

        Args:
            prompt: List of prompt messages
            response: Model response
            model: Model identifier
            latency_ms: Invocation latency
            tokens: Token usage estimate
            budget_tags: Cost attribution tags
            retries: Number of retries
            error: Error message if failed
        """
        entry = {
            "type": "llm_call",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "tenant_id": self.tenant_id,
            "workflow_id": self.workflow_id,
            "use_case": self.use_case,
            "model": model,
            "prompt_length": sum(len(p) for p in prompt),
            "response_length": len(response),
            "tokens": tokens,
            "latency_ms": latency_ms,
            "retries": retries,
            "success": error is None,
            "error": error,
        }

        if budget_tags:
            entry["budget"] = {
                "tenant": budget_tags.tenant_id,
                "workflow": budget_tags.workflow_id,
                "operation": budget_tags.operation,
            }

        self._entries.append(entry)

        # Immediate structured log
        self._emit_log(entry)

    def log_retrieval(
        self,
        query: str,
        n_results: int,
        strategy: str,
        latency_ms: float,
        cache_hit: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        Log retrieval operation for audit trail.

        Args:
            query: Search query
            n_results: Number of results returned
            strategy: Search strategy used
            latency_ms: Operation latency
            cache_hit: Whether result was from cache
            error: Error message if failed
        """
        entry = {
            "type": "retrieval",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "tenant_id": self.tenant_id,
            "workflow_id": self.workflow_id,
            "query_length": len(query),
            "n_results": n_results,
            "strategy": strategy,
            "latency_ms": latency_ms,
            "cache_hit": cache_hit,
            "success": error is None,
            "error": error,
        }

        self._entries.append(entry)
        self._emit_log(entry)

    def log_workflow_step(
        self,
        step_name: str,
        input_summary: str,
        output_summary: str,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log workflow step execution.

        Args:
            step_name: Name of workflow step (e.g., "evidence_extraction")
            input_summary: Summary of step input
            output_summary: Summary of step output
            latency_ms: Step execution time
            metadata: Additional step metadata
        """
        entry = {
            "type": "workflow_step",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "tenant_id": self.tenant_id,
            "workflow_id": self.workflow_id,
            "step_name": step_name,
            "input_length": len(input_summary),
            "output_length": len(output_summary),
            "latency_ms": latency_ms,
            "metadata": metadata or {},
        }

        self._entries.append(entry)
        self._emit_log(entry)

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get all audit entries for this context."""
        return self._entries.copy()

    def flush(self) -> None:
        """Flush any buffered audit entries."""
        # In production, this would write to audit log store
        logger.debug(f"Flushing {len(self._entries)} audit entries for trace {self.trace_id}")

    def _emit_log(self, entry: Dict[str, Any]) -> None:
        """Emit structured log entry."""
        # JSON structured logging for log aggregation
        logger.info(json.dumps(entry))
```

### EvalHarness Interface

```python
# platform/eval_harness.py
"""
Evaluation Harness for offline regression testing and quality gates.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import logging
import json
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class EvalMetric(Enum):
    """Standard evaluation metrics."""
    ACCURACY = "accuracy"
    GROUNDING = "grounding"
    COMPLETENESS = "completeness"
    RELEVANCE = "relevance"
    COHERENCE = "coherence"


@dataclass
class EvalResult:
    """Result of a single evaluation."""
    test_id: str
    passed: bool
    scores: Dict[EvalMetric, float]
    threshold_scores: Dict[EvalMetric, float]
    latency_ms: float
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalSuiteResult:
    """Result of running an evaluation suite."""
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    overall_score: float
    threshold: float
    passed: bool
    results: List[EvalResult]
    duration_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class EvalRubric:
    """Scoring rubric for evaluation."""
    metric: EvalMetric
    weight: float
    threshold: float
    scorer: Callable[[Any, Any], float]  # (expected, actual) -> score
    description: str = ""


class EvalHarness:
    """
    Evaluation harness for offline regression testing.

    Features:
    - Run evaluation suites against test cases
    - Configurable scoring rubrics
    - Threshold-based pass/fail
    - CI integration (exit code based on results)
    - Result persistence and comparison

    Usage:
        harness = EvalHarness()
        harness.register_suite("curation_quality", rubrics, test_cases)
        result = harness.run_suite("curation_quality")

        # CI gate
        if not result.passed:
            sys.exit(1)
    """

    def __init__(self, results_dir: str = "./eval_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._suites: Dict[str, Dict[str, Any]] = {}

    def register_suite(
        self,
        suite_name: str,
        rubrics: List[EvalRubric],
        test_cases: List[Dict[str, Any]],
        threshold: float = 0.8,
    ) -> None:
        """
        Register an evaluation suite.

        Args:
            suite_name: Name of the suite
            rubrics: List of scoring rubrics
            test_cases: List of test cases with 'input' and 'expected' keys
            threshold: Overall pass threshold (0-1)
        """
        self._suites[suite_name] = {
            "rubrics": rubrics,
            "test_cases": test_cases,
            "threshold": threshold,
        }
        logger.info(f"Registered eval suite '{suite_name}' with {len(test_cases)} test cases")

    def run_suite(
        self,
        suite_name: str,
        executor: Callable[[Dict[str, Any]], Any],
    ) -> EvalSuiteResult:
        """
        Run an evaluation suite.

        Args:
            suite_name: Name of the suite to run
            executor: Function that takes test input and returns output

        Returns:
            EvalSuiteResult with pass/fail status and detailed scores
        """
        if suite_name not in self._suites:
            raise ValueError(f"Unknown eval suite: {suite_name}")

        suite = self._suites[suite_name]
        rubrics = suite["rubrics"]
        test_cases = suite["test_cases"]
        threshold = suite["threshold"]

        import time
        start_time = time.time()
        results = []

        for i, test_case in enumerate(test_cases):
            test_id = test_case.get("id", f"test_{i}")

            try:
                # Execute test
                test_start = time.time()
                actual = executor(test_case["input"])
                latency_ms = (time.time() - test_start) * 1000

                # Score against rubrics
                scores = {}
                threshold_scores = {}
                for rubric in rubrics:
                    score = rubric.scorer(test_case["expected"], actual)
                    scores[rubric.metric] = score
                    threshold_scores[rubric.metric] = rubric.threshold

                # Calculate weighted score
                weighted_score = sum(
                    scores[r.metric] * r.weight for r in rubrics
                ) / sum(r.weight for r in rubrics)

                # Determine pass/fail
                passed = all(
                    scores[r.metric] >= r.threshold for r in rubrics
                )

                results.append(EvalResult(
                    test_id=test_id,
                    passed=passed,
                    scores=scores,
                    threshold_scores=threshold_scores,
                    latency_ms=latency_ms,
                    details={"weighted_score": weighted_score}
                ))

            except Exception as e:
                logger.error(f"Test {test_id} failed with error: {e}")
                results.append(EvalResult(
                    test_id=test_id,
                    passed=False,
                    scores={},
                    threshold_scores={},
                    latency_ms=0,
                    error=str(e)
                ))

        duration = time.time() - start_time
        passed_count = sum(1 for r in results if r.passed)
        overall_score = passed_count / len(results) if results else 0

        suite_result = EvalSuiteResult(
            suite_name=suite_name,
            total_tests=len(results),
            passed_tests=passed_count,
            failed_tests=len(results) - passed_count,
            overall_score=overall_score,
            threshold=threshold,
            passed=overall_score >= threshold,
            results=results,
            duration_seconds=duration,
        )

        # Persist results
        self._save_result(suite_result)

        return suite_result

    def compare_results(
        self,
        suite_name: str,
        baseline_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare current results against baseline.

        Args:
            suite_name: Name of the suite
            baseline_path: Path to baseline results (uses latest if not specified)

        Returns:
            Comparison report with regressions highlighted
        """
        # Implementation
        return {}

    def _save_result(self, result: EvalSuiteResult) -> None:
        """Save evaluation result to file."""
        filename = f"{result.suite_name}_{result.timestamp.replace(':', '-')}.json"
        filepath = self.results_dir / filename

        with open(filepath, "w") as f:
            json.dump({
                "suite_name": result.suite_name,
                "total_tests": result.total_tests,
                "passed_tests": result.passed_tests,
                "failed_tests": result.failed_tests,
                "overall_score": result.overall_score,
                "threshold": result.threshold,
                "passed": result.passed,
                "duration_seconds": result.duration_seconds,
                "timestamp": result.timestamp,
                "results": [
                    {
                        "test_id": r.test_id,
                        "passed": r.passed,
                        "scores": {k.value: v for k, v in r.scores.items()},
                        "latency_ms": r.latency_ms,
                        "error": r.error,
                    }
                    for r in result.results
                ]
            }, f, indent=2)

        logger.info(f"Saved eval results to {filepath}")
```

### DegradationPolicy Interface

```python
# platform/degradation_policy.py
"""
Degradation Policy for safe failure handling and kill switches.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable
from enum import Enum
import logging
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    """Degradation levels."""
    NORMAL = "normal"           # Full AI capability
    REDUCED = "reduced"         # Fallback model only
    CACHED = "cached"           # Cached responses only
    STATIC = "static"           # Static fallback responses
    DISABLED = "disabled"       # AI completely disabled


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior."""
    level: DegradationLevel
    fallback_response: Optional[str] = None
    cache_key: Optional[str] = None
    ttl_seconds: int = 3600


@dataclass
class KillSwitchState:
    """Kill switch state."""
    global_killed: bool = False
    workflow_killed: Dict[str, bool] = field(default_factory=dict)
    killed_at: Optional[str] = None
    killed_by: Optional[str] = None
    reason: Optional[str] = None


class DegradationPolicy:
    """
    Degradation policy manager for safe failure handling.

    Features:
    - Global and per-workflow kill switches
    - Configurable fallback behaviors
    - Circuit breaker integration
    - Audit logging for kill switch events

    Usage:
        policy = DegradationPolicy()

        # Check if workflow is allowed
        if policy.is_allowed("curation"):
            result = gateway.invoke(...)
        else:
            result = policy.get_fallback("curation", request)

        # Kill a workflow (admin action)
        policy.kill_workflow("curation", reason="Quality degradation detected")

        # Restore
        policy.restore_workflow("curation")
    """

    def __init__(
        self,
        config_path: str = "./config/degradation.json",
        state_path: str = "./state/kill_switch.json",
    ):
        self.config_path = Path(config_path)
        self.state_path = Path(state_path)
        self._state = self._load_state()
        self._fallbacks: Dict[str, FallbackConfig] = {}
        self._load_config()

    def is_allowed(self, workflow_id: str) -> bool:
        """
        Check if a workflow is allowed to execute.

        Args:
            workflow_id: Workflow identifier

        Returns:
            True if workflow can execute, False if killed
        """
        if self._state.global_killed:
            logger.warning(f"Global kill switch active, blocking {workflow_id}")
            return False

        if self._state.workflow_killed.get(workflow_id, False):
            logger.warning(f"Workflow kill switch active for {workflow_id}")
            return False

        return True

    def get_degradation_level(self, workflow_id: str) -> DegradationLevel:
        """
        Get current degradation level for a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Current DegradationLevel
        """
        if self._state.global_killed:
            return DegradationLevel.DISABLED

        if self._state.workflow_killed.get(workflow_id, False):
            return DegradationLevel.DISABLED

        if workflow_id in self._fallbacks:
            return self._fallbacks[workflow_id].level

        return DegradationLevel.NORMAL

    def get_fallback(
        self,
        workflow_id: str,
        request: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get fallback response for a killed/degraded workflow.

        Args:
            workflow_id: Workflow identifier
            request: Original request

        Returns:
            Fallback response
        """
        level = self.get_degradation_level(workflow_id)

        if level == DegradationLevel.DISABLED:
            return {
                "success": False,
                "error": "Service temporarily unavailable",
                "degradation_level": level.value,
                "message": "AI capabilities are temporarily disabled. Please try again later.",
            }

        if workflow_id in self._fallbacks:
            config = self._fallbacks[workflow_id]
            if config.fallback_response:
                return {
                    "success": True,
                    "response": config.fallback_response,
                    "degradation_level": level.value,
                    "is_fallback": True,
                }

        return {
            "success": False,
            "error": "No fallback configured",
            "degradation_level": level.value,
        }

    def kill_global(self, reason: str, killed_by: str = "system") -> None:
        """
        Activate global kill switch.

        Args:
            reason: Reason for killing
            killed_by: Who initiated the kill
        """
        self._state.global_killed = True
        self._state.killed_at = datetime.utcnow().isoformat()
        self._state.killed_by = killed_by
        self._state.reason = reason

        self._save_state()
        logger.critical(f"GLOBAL KILL SWITCH ACTIVATED by {killed_by}: {reason}")

    def kill_workflow(
        self,
        workflow_id: str,
        reason: str,
        killed_by: str = "system",
    ) -> None:
        """
        Activate kill switch for specific workflow.

        Args:
            workflow_id: Workflow to kill
            reason: Reason for killing
            killed_by: Who initiated the kill
        """
        self._state.workflow_killed[workflow_id] = True
        self._state.killed_at = datetime.utcnow().isoformat()
        self._state.killed_by = killed_by
        self._state.reason = reason

        self._save_state()
        logger.warning(f"Kill switch activated for {workflow_id} by {killed_by}: {reason}")

    def restore_global(self, restored_by: str = "system") -> None:
        """Restore global AI capabilities."""
        self._state.global_killed = False
        self._save_state()
        logger.info(f"Global kill switch deactivated by {restored_by}")

    def restore_workflow(self, workflow_id: str, restored_by: str = "system") -> None:
        """Restore specific workflow."""
        self._state.workflow_killed[workflow_id] = False
        self._save_state()
        logger.info(f"Kill switch deactivated for {workflow_id} by {restored_by}")

    def get_status(self) -> Dict[str, Any]:
        """Get current kill switch status."""
        return {
            "global_killed": self._state.global_killed,
            "workflow_killed": self._state.workflow_killed.copy(),
            "killed_at": self._state.killed_at,
            "killed_by": self._state.killed_by,
            "reason": self._state.reason,
        }

    def register_fallback(
        self,
        workflow_id: str,
        config: FallbackConfig,
    ) -> None:
        """Register fallback configuration for a workflow."""
        self._fallbacks[workflow_id] = config
        logger.info(f"Registered fallback for {workflow_id}: level={config.level.value}")

    def _load_state(self) -> KillSwitchState:
        """Load kill switch state from file."""
        if self.state_path.exists():
            with open(self.state_path) as f:
                data = json.load(f)
                return KillSwitchState(
                    global_killed=data.get("global_killed", False),
                    workflow_killed=data.get("workflow_killed", {}),
                    killed_at=data.get("killed_at"),
                    killed_by=data.get("killed_by"),
                    reason=data.get("reason"),
                )
        return KillSwitchState()

    def _save_state(self) -> None:
        """Save kill switch state to file."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump({
                "global_killed": self._state.global_killed,
                "workflow_killed": self._state.workflow_killed,
                "killed_at": self._state.killed_at,
                "killed_by": self._state.killed_by,
                "reason": self._state.reason,
            }, f, indent=2)

    def _load_config(self) -> None:
        """Load degradation config from file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                data = json.load(f)
                for workflow_id, config in data.get("fallbacks", {}).items():
                    self._fallbacks[workflow_id] = FallbackConfig(
                        level=DegradationLevel(config.get("level", "normal")),
                        fallback_response=config.get("fallback_response"),
                        cache_key=config.get("cache_key"),
                        ttl_seconds=config.get("ttl_seconds", 3600),
                    )
```

## 5.3 Example: Updated Agent Using Platform

```python
# workflows/policy_curation/evidence_extraction.py
"""
Evidence Extraction Agent - Updated to use platform primitives.
"""
from typing import Dict, Any, List

from platform.model_gateway import ModelGateway, BudgetTags, ModelConfig
from platform.audit_context import AuditContext
from workflows.base_agent import BaseAgent


class EvidenceExtractionAgent(BaseAgent):
    """
    Extract verbatim requirements from retrieved documents.

    Updated to use platform ModelGateway instead of direct ChatOpenAI.
    """

    def __init__(self, gateway: ModelGateway = None):
        super().__init__()
        # Use injected gateway or create default
        self.gateway = gateway or ModelGateway()

        # Model config for extraction (deterministic)
        self.model_config = ModelConfig(
            model_name="gpt-4o-mini",
            temperature=0.0,  # Deterministic for extraction
            max_tokens=4096,
            timeout_seconds=60.0,
        )

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute evidence extraction.

        Args:
            state: Workflow state with statute_chunks and policy_chunks

        Returns:
            Updated state with extracted_requirements
        """
        audit = AuditContext.current()

        # Prepare extraction prompt
        chunks = state.get("statute_chunks", []) + state.get("policy_chunks", [])
        prompt = self._build_extraction_prompt(state["question"], chunks)

        # Invoke via gateway (with retry, audit, budget tracking)
        result = self.gateway.invoke(
            messages=[HumanMessage(content=prompt)],
            budget_tags=BudgetTags(
                tenant_id=audit.tenant_id,
                workflow_id="curation",
                operation="evidence_extraction",
            ),
            audit_context=audit,
            model_config=self.model_config,
        )

        # Parse extraction results
        requirements = self._parse_requirements(result.content)

        # Log workflow step
        audit.log_workflow_step(
            step_name="evidence_extraction",
            input_summary=f"{len(chunks)} chunks for question: {state['question'][:50]}...",
            output_summary=f"Extracted {len(requirements)} requirements",
            latency_ms=result.latency_ms,
            metadata={"tokens_used": result.tokens_used}
        )

        return {
            **state,
            "extracted_requirements": requirements,
            "extraction_metadata": {
                "model_used": result.model_used,
                "latency_ms": result.latency_ms,
                "tokens_used": result.tokens_used,
                "trace_id": result.trace_id,
            }
        }

    def _build_extraction_prompt(self, question: str, chunks: List[Dict]) -> str:
        """Build extraction prompt from question and chunks."""
        # Implementation unchanged from current
        pass

    def _parse_requirements(self, response: str) -> List[Dict[str, Any]]:
        """Parse requirements from LLM response."""
        # Implementation unchanged from current
        pass
```

---

# 6. ASSUMPTIONS / NEEDS CONFIRMATION

| # | Item | Assumption | Action Needed |
|---|------|------------|---------------|
| A1 | Single tenant vs multi-tenant | Currently single tenant; migration adds tenant context | Confirm if multi-tenant support needed now |
| A2 | Kill switch persistence | Using file-based state (`kill_switch.json`) | Confirm if Redis/DB preferred for HA |
| A3 | Audit log destination | Structured JSON to stdout (for log aggregation) | Confirm log aggregation tool (CloudWatch, Datadog, etc.) |
| A4 | Fallback model | Assuming `gpt-3.5-turbo` as fallback | Confirm fallback model preference |
| A5 | Circuit breaker thresholds | 5 failures in 60s triggers open state | Confirm threshold values |
| A6 | Eval CI blocking | Fail CI if overall score < 80% | Confirm threshold and blocking behavior |
| A7 | Cost tracking granularity | Per-request cost estimate | Confirm if actual billing integration needed |
| A8 | Prompt logging | Log prompt length only (not content) for privacy | Confirm if full prompt logging acceptable |
| A9 | Cache TTL | 5 minutes for retrieval cache | Confirm cache duration |
| A10 | Module reorganization | Move agents to `/workflows` directory | Confirm if directory restructure acceptable |

---

# 7. NEXT STEPS

1. **Review and approve** this architecture document
2. **Confirm assumptions** in Section 6
3. **Prioritize phases** based on urgency (recommend: Phase 0 + 3 first for audit compliance)
4. **Create JIRA tickets** from PR checklist
5. **Begin Phase 0** implementation

---

*Document Version: 1.0*
*Created: January 2026*
*Author: Senior Principal Architect (AI-assisted)*
