"""
FastAPI backend for DHCS BHT Multi-Agent System

BHT Platform Integration (Phase 0):
- AuditContextMiddleware for request tracing
- trace_id propagation via response headers
- Structured audit logging
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from agents.core.orchestrator import AgentOrchestrator
from agents.core.query_agent import QueryAgent
from agents.core.analytics_agent import AnalyticsAgent
from agents.core.triage_agent import TriageAgent
from agents.core.recommendations_agent import RecommendationsAgent
from agents.knowledge.knowledge_base import DHCSKnowledgeBase
from agents.core.curation_orchestrator import CurationOrchestrator
from agents.monitoring import QualityMonitor, AgentWeights

# BHT Platform imports
from platform.middleware import AuditContextMiddleware
from platform.audit_context import AuditContext
from platform.config import get_platform_config
from platform.retrieval_service import RetrievalService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DHCS BHT Multi-Agent API",
    description="API for DHCS Behavioral Health Treatment crisis intake AI agents",
    version="0.1.0"
)

# BHT Platform: Add AuditContext middleware for request tracing
# This creates trace_id for every request and adds it to response headers
app.add_middleware(AuditContextMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents (lazy loading to avoid startup delays)
orchestrator: Optional[AgentOrchestrator] = None
query_agent: Optional[QueryAgent] = None
analytics_agent: Optional[AnalyticsAgent] = None
triage_agent: Optional[TriageAgent] = None
recommendations_agent: Optional[RecommendationsAgent] = None
knowledge_base: Optional[DHCSKnowledgeBase] = None
curation_orchestrator: Optional[CurationOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Lazy load orchestrator"""
    global orchestrator
    if orchestrator is None:
        logger.info("Initializing Agent Orchestrator")
        orchestrator = AgentOrchestrator()
    return orchestrator


def get_knowledge_base() -> DHCSKnowledgeBase:
    """Lazy load knowledge base"""
    global knowledge_base
    if knowledge_base is None:
        logger.info("Initializing Knowledge Base")
        knowledge_base = DHCSKnowledgeBase()
        # Initialize with DHCS policies if empty
        if knowledge_base.collection.count() == 0:
            knowledge_base.initialize_with_dhcs_policies()
    return knowledge_base


def get_curation_orchestrator() -> CurationOrchestrator:
    """Lazy load curation orchestrator"""
    global curation_orchestrator
    if curation_orchestrator is None:
        logger.info("Initializing Curation Orchestrator")
        curation_orchestrator = CurationOrchestrator()
    return curation_orchestrator


# Request/Response Models
class QueryRequest(BaseModel):
    question: str
    use_rag: bool = False


class AnalyticsRequest(BaseModel):
    analysis_type: str = "comprehensive"
    time_window_minutes: int = 60


class TriageRequest(BaseModel):
    time_window_minutes: int = 30
    limit: int = 20


class RecommendationsRequest(BaseModel):
    focus_area: str = "comprehensive"
    time_window_minutes: int = 60


class ChatRequest(BaseModel):
    message: str


class CurationRequest(BaseModel):
    question: str
    topic: str
    sub_section: str = ""
    category: str = ""


class CurationBatchRequest(BaseModel):
    questions: list[Dict[str, str]]  # List of question dicts with IP Question, IP Section, etc.


class KnowledgeSearchRequest(BaseModel):
    query: str
    n_results: int = 5


# Helper function to conditionally add trace metadata
def _maybe_add_trace(response: dict) -> dict:
    """Add _trace metadata to response if enabled by config."""
    config = get_platform_config()
    if config.platform_enabled and config.include_trace_in_response:
        ctx = AuditContext.current()
        response["_trace"] = ctx.get_trace_metadata()
    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint with optional trace metadata"""
    response = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "DHCS BHT Multi-Agent API",
    }
    return _maybe_add_trace(response)


# Main chat endpoint (uses orchestrator)
@app.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    """
    Main chat endpoint - routes to appropriate agent via orchestrator

    Example:
        POST /chat
        {"message": "How many high-risk events in the last hour?"}
    """
    try:
        orch = get_orchestrator()
        result = orch.execute(request.message)
        return _maybe_add_trace(result)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Direct agent endpoints
@app.post("/query")
async def query(request: QueryRequest) -> Dict[str, Any]:
    """
    Query agent endpoint - answer data questions

    Example:
        POST /query
        {"question": "What counties have the most events?", "use_rag": false}
    """
    try:
        global query_agent
        if query_agent is None:
            query_agent = QueryAgent()

        result = query_agent.execute({"question": request.question})

        # Optionally enhance with RAG knowledge
        if request.use_rag:
            kb = get_knowledge_base()
            context = kb.get_context_for_query(request.question, max_tokens=500)
            result["knowledge_context"] = context

        return result
    except Exception as e:
        logger.error(f"Error in query endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analytics")
async def analytics(request: AnalyticsRequest) -> Dict[str, Any]:
    """
    Analytics agent endpoint - analyze trends and anomalies

    Example:
        POST /analytics
        {"analysis_type": "comprehensive", "time_window_minutes": 60}
    """
    try:
        global analytics_agent
        if analytics_agent is None:
            analytics_agent = AnalyticsAgent()

        result = analytics_agent.execute({
            "analysis_type": request.analysis_type,
            "time_window_minutes": request.time_window_minutes
        })

        return result
    except Exception as e:
        logger.error(f"Error in analytics endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/triage")
async def triage(request: TriageRequest) -> Dict[str, Any]:
    """
    Triage agent endpoint - prioritize high-risk cases

    Example:
        POST /triage
        {"time_window_minutes": 30, "limit": 20}
    """
    try:
        global triage_agent
        if triage_agent is None:
            triage_agent = TriageAgent()

        result = triage_agent.execute({
            "time_window_minutes": request.time_window_minutes,
            "limit": request.limit
        })

        return result
    except Exception as e:
        logger.error(f"Error in triage endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommendations")
async def recommendations(request: RecommendationsRequest) -> Dict[str, Any]:
    """
    Recommendations agent endpoint - get operational recommendations

    Example:
        POST /recommendations
        {"focus_area": "staffing", "time_window_minutes": 60}
    """
    try:
        global recommendations_agent
        if recommendations_agent is None:
            recommendations_agent = RecommendationsAgent()

        result = recommendations_agent.execute({
            "focus_area": request.focus_area,
            "time_window_minutes": request.time_window_minutes
        })

        return result
    except Exception as e:
        logger.error(f"Error in recommendations endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/knowledge/search")
async def knowledge_search(request: KnowledgeSearchRequest) -> Dict[str, Any]:
    """
    Search DHCS knowledge base

    Example:
        POST /knowledge/search
        {"query": "mobile crisis team response time", "n_results": 5}
    """
    try:
        kb = get_knowledge_base()
        # Use RetrievalService for audit logging
        retrieval_service = RetrievalService(knowledge_base=kb)
        result = retrieval_service.search(request.query, n_results=request.n_results)

        return {
            "query": request.query,
            "results": [c.to_dict() for c in result.citations],
            "count": len(result.citations)
        }
    except Exception as e:
        logger.error(f"Error in knowledge search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge/stats")
async def knowledge_stats():
    """Get knowledge base statistics"""
    try:
        kb = get_knowledge_base()
        return {
            "document_count": kb.collection.count(),
            "collection_name": kb.collection.name,
            "persist_directory": kb.persist_directory
        }
    except Exception as e:
        logger.error(f"Error getting knowledge stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POLICY CURATION ENDPOINTS
# =============================================================================

@app.post("/curation/process")
async def process_curation_question(request: CurationRequest):
    """
    Process a single policy curation question through multi-agent workflow.

    Uses 5-agent pipeline:
    1. RetrievalAgent - Document retrieval with query enhancement
    2. StatuteAnalystAgent - Legal statute analysis
    3. PolicyAnalystAgent - Policy interpretation
    4. SynthesisAgent - Final summary creation
    5. QualityReviewerAgent - Output validation

    Returns:
        Compliance summary with quality score and metadata
    """
    try:
        config = get_platform_config()
        trace_id = ""
        if config.platform_enabled:
            ctx = AuditContext.current()
            trace_id = ctx.trace_id
        logger.info(f"Processing curation question: {request.question[:100]}... (trace_id={trace_id})")

        orchestrator = get_curation_orchestrator()

        result = orchestrator.execute({
            "question": request.question,
            "topic": request.topic,
            "sub_section": request.sub_section,
            "category": request.category
        })

        response = {
            "success": result["success"],
            # POC-compatible output fields (3-stage summaries)
            "statute_summary": result.get("statute_summary", ""),
            "policy_summary": result.get("policy_summary", ""),
            "final_summary": result["final_summary"],
            # Additional detailed fields
            "statute_analysis": result.get("statute_analysis", ""),
            "policy_analysis": result.get("policy_analysis", ""),
            "final_response": result["final_response"],
            "action_items": result["action_items"],
            "priority": result["priority"],
            "quality_score": result["quality_score"],
            "passes_review": result["passes_review"],
            "metadata": result["metadata"],
        }
        return _maybe_add_trace(response)

    except Exception as e:
        logger.error(f"Curation processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/curation/batch")
async def process_curation_batch(request: CurationBatchRequest):
    """
    Process batch of policy curation questions.

    Input:
        questions: List of dicts with keys:
            - IP Question
            - IP Section
            - IP Sub-Section
            - topic_name

    Returns:
        List of results with processing metadata
    """
    try:
        logger.info(f"Processing curation batch: {len(request.questions)} questions")

        orchestrator = get_curation_orchestrator()
        results = []

        for i, q_data in enumerate(request.questions):
            logger.info(f"Processing question {i+1}/{len(request.questions)}")

            # Construct topic string (matching prototype format)
            topic = (
                f"Section Topic {q_data.get('IP Section', '')}: "
                f"{q_data.get('IP Sub-Section', '')} "
                f"Category: {q_data.get('topic_name', '')}"
            )

            result = orchestrator.execute({
                "question": q_data.get("IP Question", ""),
                "topic": topic,
                "sub_section": q_data.get("IP Sub-Section", ""),
                "category": q_data.get("topic_name", "")
            })

            # Add original question data to result
            result["question_index"] = i
            result["original_data"] = q_data

            results.append(result)

        return {
            "success": True,
            "total_questions": len(results),
            "results": results,
            "summary": {
                "avg_quality_score": sum(r["quality_score"] for r in results) / len(results),
                "passed_review": sum(1 for r in results if r["passes_review"]),
                "high_priority": sum(1 for r in results if r.get("priority") == "High")
            }
        }

    except Exception as e:
        logger.error(f"Batch curation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/curation/stats")
async def get_curation_stats():
    """
    Get statistics about the curation knowledge base.

    Returns document counts by category, version info, etc.
    """
    try:
        kb = get_knowledge_base()

        total_docs = kb.collection.count()

        # Try to get category breakdowns
        stats = {
            "total_documents": total_docs,
            "collection_name": kb.collection.name,
            "persist_directory": kb.persist_directory
        }

        # Attempt to count by category
        try:
            policy_results = kb.collection.query(
                query_texts=["test"],
                n_results=1,
                where={"category": "policy"}
            )
            stats["policy_documents"] = len(policy_results.get("metadatas", [[]])[0])
        except:
            stats["policy_documents"] = "unknown"

        try:
            statute_results = kb.collection.query(
                query_texts=["test"],
                n_results=1,
                where={"category": "statute"}
            )
            stats["statute_documents"] = len(statute_results.get("metadatas", [[]])[0])
        except:
            stats["statute_documents"] = "unknown"

        return stats

    except Exception as e:
        logger.error(f"Error getting curation stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/curation/diagnose")
async def diagnose_curation_result(request: dict):
    """
    Diagnostic endpoint for quality analysis.

    Accepts a curation result and provides:
    - Root cause analysis
    - Component-level scores (retrieval, analysis, synthesis, quality review)
    - Precision/Recall metrics
    - Confidence intervals
    - Prioritized recommendations

    Input:
        Complete workflow result from /curation/process

    Returns:
        Comprehensive diagnostic report with:
        - summary: High-level quality assessment
        - diagnostics: Root cause and component scores
        - recommendations: Prioritized improvement actions
        - quality_score_detailed: Score with confidence intervals
    """
    try:
        logger.info("Running quality diagnostics on curation result")

        # Initialize monitor with configurable weights
        weights = AgentWeights(
            retrieval_weight=0.25,
            statute_analysis_weight=0.25,
            policy_analysis_weight=0.25,
            synthesis_weight=0.15,
            quality_review_weight=0.10
        )
        monitor = QualityMonitor(weights=weights)

        # Generate comprehensive report
        report = monitor.generate_report(request)

        logger.info(
            f"Diagnostic complete: Root cause={report['diagnostics']['root_cause']['component']}, "
            f"Severity={report['summary']['severity']}"
        )

        return report

    except Exception as e:
        logger.error(f"Diagnostic analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SMOKE TEST ENDPOINT (for audit correlation verification)
# =============================================================================

import os

class SmokeCorrelationRequest(BaseModel):
    """Request for smoke correlation test"""
    query: str = "What are the crisis response protocols?"


@app.post("/smoke/correlate")
async def smoke_correlate(request: SmokeCorrelationRequest) -> Dict[str, Any]:
    """
    Smoke test endpoint that exercises BOTH retrieval AND LLM in a single request.

    This endpoint is used to verify that:
    1. api_request, llm_call, and retrieval all share the same trace_id
    2. Audit correlation works end-to-end

    Only enabled when BHT_SMOKE_ENDPOINT_ENABLED=true (default in Docker).
    """
    # Check if smoke endpoint is enabled
    if os.getenv("BHT_SMOKE_ENDPOINT_ENABLED", "true").lower() != "true":
        raise HTTPException(status_code=404, detail="Smoke endpoint disabled")

    try:
        config = get_platform_config()
        ctx = AuditContext.current()
        trace_id = ctx.trace_id if config.platform_enabled else "disabled"

        logger.info(f"Smoke correlation test: trace_id={trace_id}")

        # Step 1: Perform retrieval (triggers retrieval audit log)
        kb = get_knowledge_base()
        retrieval_service = RetrievalService(knowledge_base=kb)
        retrieval_result = retrieval_service.search(request.query, n_results=3)

        retrieval_context = "\n".join([
            f"- {c.snippet[:200]}..." for c in retrieval_result.citations[:3]
        ])

        logger.info(f"Smoke: Retrieved {len(retrieval_result.citations)} documents")

        # Step 2: Perform LLM call using retrieved context (triggers llm_call audit log)
        from langchain_core.prompts import ChatPromptTemplate
        from platform.model_gateway import ModelGateway

        gateway = ModelGateway()
        llm = gateway.get_underlying_llm(with_audit_callback=True)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Summarize the following policy information in 2-3 sentences."),
            ("human", "Context:\n{context}\n\nQuestion: {question}\n\nBrief summary:")
        ])

        chain = prompt | llm
        llm_response = chain.invoke({
            "context": retrieval_context,
            "question": request.query
        })

        summary = llm_response.content.strip()
        logger.info(f"Smoke: LLM summarization complete")

        return {
            "success": True,
            "trace_id": trace_id,
            "retrieval_count": len(retrieval_result.citations),
            "llm_summary": summary,
            "message": "Smoke correlation test completed. Check audit logs for api_request + retrieval + llm_call with same trace_id."
        }

    except Exception as e:
        logger.error(f"Smoke correlation test failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
