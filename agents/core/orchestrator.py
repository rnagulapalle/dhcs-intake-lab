"""
Multi-Agent Orchestrator using LangGraph
Coordinates between specialized agents for comprehensive crisis intake support
"""
import logging
from typing import Dict, Any, TypedDict, Annotated, Sequence, Optional, TYPE_CHECKING
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate

from agents.core.config import settings
from agents.core.query_agent import QueryAgent
from agents.core.analytics_agent import AnalyticsAgent
from agents.core.triage_agent import TriageAgent
from agents.core.recommendations_agent import RecommendationsAgent

# Conditional import to avoid circular dependencies
if TYPE_CHECKING:
    from platform.model_gateway import ModelGateway

logger = logging.getLogger(__name__)


def _get_gateway(gateway: Optional["ModelGateway"] = None) -> "ModelGateway":
    """
    Get ModelGateway instance.

    All LLM access MUST go through the gateway - no direct provider imports allowed.
    """
    if gateway is not None:
        return gateway

    from platform.model_gateway import get_default_gateway
    return get_default_gateway()


class AgentState(TypedDict):
    """State object passed between agents in the graph"""
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    user_input: str
    intent: str
    current_agent: str
    query_result: Dict[str, Any]
    analytics_result: Dict[str, Any]
    triage_result: Dict[str, Any]
    recommendations_result: Dict[str, Any]
    final_response: str


class AgentOrchestrator:
    """
    Orchestrates multi-agent workflow using LangGraph
    Routes user requests to appropriate specialized agents
    """

    def __init__(self, gateway: Optional["ModelGateway"] = None):
        self._gateway = _get_gateway(gateway)

        # Initialize specialized agents
        self.query_agent = QueryAgent()
        self.analytics_agent = AnalyticsAgent()
        self.triage_agent = TriageAgent()
        self.recommendations_agent = RecommendationsAgent()

        # Build the workflow graph
        self.workflow = self._build_workflow()

        logger.info("Agent Orchestrator initialized with LangGraph workflow")

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""

        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("query_agent", self._run_query_agent)
        workflow.add_node("analytics_agent", self._run_analytics_agent)
        workflow.add_node("triage_agent", self._run_triage_agent)
        workflow.add_node("recommendations_agent", self._run_recommendations_agent)
        workflow.add_node("generate_response", self._generate_final_response)

        # Define edges (routing logic)
        workflow.set_entry_point("classify_intent")

        # After intent classification, route to appropriate agent
        workflow.add_conditional_edges(
            "classify_intent",
            self._route_to_agent,
            {
                "query": "query_agent",
                "analytics": "analytics_agent",
                "triage": "triage_agent",
                "recommendations": "recommendations_agent",
                "comprehensive": "analytics_agent"  # Start with analytics for comprehensive
            }
        )

        # Connect agents to response generation
        workflow.add_edge("query_agent", "generate_response")
        workflow.add_edge("triage_agent", "generate_response")
        workflow.add_edge("recommendations_agent", "generate_response")

        # For analytics and comprehensive, optionally trigger recommendations
        workflow.add_conditional_edges(
            "analytics_agent",
            self._should_generate_recommendations,
            {
                "yes": "recommendations_agent",
                "no": "generate_response"
            }
        )

        # End after response generation
        workflow.add_edge("generate_response", END)

        return workflow.compile()

    def _classify_intent(self, state: AgentState) -> AgentState:
        """Classify user intent to route to appropriate agent"""

        user_input = state["user_input"]

        system_message = """You are an intent classifier for a crisis intake support system.
Classify the user's intent into one of these categories:

1. "query" - User wants to query data (e.g., "How many events?", "Show me...", "What happened...")
2. "analytics" - User wants analysis/trends (e.g., "Analyze trends", "Detect anomalies", "What patterns...")
3. "triage" - User wants to see high-risk cases (e.g., "Show high-risk cases", "What needs attention", "Priority cases")
4. "recommendations" - User wants operational recommendations (e.g., "What should we do?", "How to improve?", "Staffing recommendations")
5. "comprehensive" - User wants complete overview (e.g., "Dashboard", "Full report", "Overview")

Return ONLY the category name, nothing else."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{user_input}")
        ])

        # Use gateway for LLM access
        chain = prompt | self._gateway.get_underlying_llm()
        response = chain.invoke({"user_input": user_input})

        intent = response.content.strip().lower()

        logger.info(f"Classified intent: {intent} for input: {user_input}")

        state["intent"] = intent
        state["messages"].append(HumanMessage(content=user_input))

        return state

    def _route_to_agent(self, state: AgentState) -> str:
        """Route to appropriate agent based on intent"""
        intent = state["intent"]

        # Map intent to agent
        if "query" in intent:
            return "query"
        elif "triage" in intent:
            return "triage"
        elif "recommendation" in intent:
            return "recommendations"
        elif "comprehensive" in intent:
            return "comprehensive"
        else:
            return "analytics"

    def _run_query_agent(self, state: AgentState) -> AgentState:
        """Execute Query Agent"""
        logger.info("Running Query Agent")

        result = self.query_agent.execute({
            "question": state["user_input"]
        })

        state["query_result"] = result
        state["current_agent"] = "query"

        return state

    def _run_analytics_agent(self, state: AgentState) -> AgentState:
        """Execute Analytics Agent"""
        logger.info("Running Analytics Agent")

        result = self.analytics_agent.execute({
            "analysis_type": "comprehensive",
            "time_window_minutes": 60
        })

        state["analytics_result"] = result
        state["current_agent"] = "analytics"

        return state

    def _run_triage_agent(self, state: AgentState) -> AgentState:
        """Execute Triage Agent"""
        logger.info("Running Triage Agent")

        result = self.triage_agent.execute({
            "time_window_minutes": 30,
            "limit": 20
        })

        state["triage_result"] = result
        state["current_agent"] = "triage"

        return state

    def _run_recommendations_agent(self, state: AgentState) -> AgentState:
        """Execute Recommendations Agent"""
        logger.info("Running Recommendations Agent")

        # Determine focus based on intent
        focus_area = "comprehensive"
        if "staffing" in state["user_input"].lower():
            focus_area = "staffing"
        elif "equity" in state["user_input"].lower():
            focus_area = "equity"
        elif "efficiency" in state["user_input"].lower():
            focus_area = "efficiency"

        result = self.recommendations_agent.execute({
            "focus_area": focus_area,
            "time_window_minutes": 60
        })

        state["recommendations_result"] = result
        state["current_agent"] = "recommendations"

        return state

    def _should_generate_recommendations(self, state: AgentState) -> str:
        """Decide if recommendations should be generated after analytics"""

        # Check if analytics found concerning patterns
        analytics = state.get("analytics_result", {})

        surge = analytics.get("surge_detection", {})
        if surge.get("is_surge_detected", False):
            logger.info("Surge detected, generating recommendations")
            return "yes"

        anomalies = analytics.get("anomalies", [])
        if len(anomalies) > 0:
            logger.info("Anomalies detected, generating recommendations")
            return "yes"

        # For comprehensive requests, always generate recommendations
        if state["intent"] == "comprehensive":
            return "yes"

        return "no"

    def _generate_final_response(self, state: AgentState) -> AgentState:
        """Generate final user-facing response"""
        logger.info("Generating final response")

        current_agent = state["current_agent"]

        # Gather results
        response_parts = []

        if current_agent == "query" and state.get("query_result"):
            result = state["query_result"]
            if result.get("success"):
                response_parts.append(f"**Query Result:**\n{result['answer']}")
            else:
                response_parts.append(f"**Error:** {result.get('error', 'Unknown error')}")

        if current_agent == "triage" and state.get("triage_result"):
            result = state["triage_result"]
            if result.get("status") == "success":
                response_parts.append(f"**Triage Summary:**\n{result['triage_summary']}")
                response_parts.append(f"\n**Recommendations:**\n{result['recommendations']}")
            else:
                response_parts.append(result.get("message", "No high-risk events found"))

        if state.get("analytics_result"):
            analytics = state["analytics_result"]
            if analytics.get("insights"):
                response_parts.append(f"**Analytics Insights:**\n{analytics['insights']}")

        if state.get("recommendations_result"):
            recs = state["recommendations_result"]
            if recs.get("recommendations"):
                response_parts.append(f"**Recommendations:**\n{recs['recommendations']}")

        final_response = "\n\n".join(response_parts)
        state["final_response"] = final_response

        state["messages"].append(AIMessage(content=final_response))

        return state

    def execute(self, user_input: str) -> Dict[str, Any]:
        """
        Execute the multi-agent workflow

        Args:
            user_input: User's natural language request

        Returns:
            Dict with final response and intermediate results
        """
        logger.info(f"Orchestrator executing for input: {user_input}")

        # Initialize state
        initial_state: AgentState = {
            "messages": [],
            "user_input": user_input,
            "intent": "",
            "current_agent": "",
            "query_result": {},
            "analytics_result": {},
            "triage_result": {},
            "recommendations_result": {},
            "final_response": ""
        }

        # Run the workflow
        try:
            final_state = self.workflow.invoke(initial_state)

            return {
                "success": True,
                "response": final_state["final_response"],
                "intent": final_state["intent"],
                "agent_used": final_state["current_agent"],
                "query_result": final_state.get("query_result"),
                "analytics_result": final_state.get("analytics_result"),
                "triage_result": final_state.get("triage_result"),
                "recommendations_result": final_state.get("recommendations_result")
            }

        except Exception as e:
            logger.error(f"Error in orchestrator execution: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": f"An error occurred: {str(e)}"
            }
