"""
FastAPI backend for DHCS BHT Multi-Agent System
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


class KnowledgeSearchRequest(BaseModel):
    query: str
    n_results: int = 5


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "DHCS BHT Multi-Agent API"
    }


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
        return result
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
        results = kb.search(request.query, n_results=request.n_results)

        return {
            "query": request.query,
            "results": results,
            "count": len(results)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
