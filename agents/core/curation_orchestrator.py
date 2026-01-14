"""
Curation Orchestrator using LangGraph
Multi-agent workflow for policy compliance curation
"""
import logging
from typing import Dict, Any, TypedDict, Annotated, Sequence, List, Optional, TYPE_CHECKING
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from agents.core.config import settings
from agents.core.retrieval_agent import RetrievalAgent
# Evidence-First Pipeline Agents
from agents.core.evidence_extraction_agent import EvidenceExtractionAgent
from agents.core.grounding_verification_agent import GroundingVerificationAgent
from agents.core.evidence_composition_agent import EvidenceCompositionAgent
# Legacy agents (for backward compatibility)
from agents.core.statute_analyst_agent import StatuteAnalystAgent
from agents.core.policy_analyst_agent import PolicyAnalystAgent
from agents.core.synthesis_agent import SynthesisAgent
from agents.core.quality_reviewer_agent import QualityReviewerAgent

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


class CurationState(TypedDict):
    """State object for curation workflow"""
    # Input fields
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    question: str
    topic: str
    sub_section: str
    category: str

    # Retrieval results
    statute_chunks: List[Dict[str, Any]]
    policy_chunks: List[Dict[str, Any]]
    retrieval_metadata: Dict[str, Any]

    # Evidence extraction (NEW - Evidence-First Pipeline)
    extracted_requirements: List[Dict[str, Any]]  # All verbatim extracts
    extraction_metadata: Dict[str, Any]  # Extraction stats

    # Grounding verification (NEW - Evidence-First Pipeline)
    verified_requirements: List[Dict[str, Any]]  # Passed grounding gate
    rejected_requirements: List[Dict[str, Any]]  # Failed grounding gate
    verification_metadata: Dict[str, Any]  # Pass rate, rejection reasons
    has_sufficient_evidence: bool  # Gate flag
    missing_evidence: List[str]  # What evidence is missing

    # Evidence composition (NEW - Evidence-First Pipeline)
    final_answer: str  # With inline [REQ-ID] references
    requirement_references: List[Dict[str, Any]]  # Which requirements used
    unused_requirements: List[str]  # Verified but not used in answer
    composition_confidence: str  # high | medium | low | insufficient

    # Audit trail (NEW - Evidence-First Pipeline)
    evidence_audit_trail: Dict[str, Any]  # Full lineage from chunks to answer
    grounding_confidence: str  # Overall confidence in evidence

    # Analysis results (LEGACY - for backward compatibility)
    statute_analysis: str
    statute_summary: str  # POC compatibility: alias for statute_analysis
    statute_confidence: str
    relevant_statutes: List[str]

    policy_analysis: str
    policy_summary: str  # POC compatibility: alias for policy_analysis
    policy_confidence: str
    key_requirements: List[str]
    recommendations: List[str]

    # Synthesis results (LEGACY - for backward compatibility)
    final_summary: str  # Alias for final_answer
    action_items: List[str]
    priority: str

    # Quality review results
    quality_score: float
    passes_review: bool
    quality_issues: List[str]
    quality_suggestions: List[str]

    # Control flow
    current_stage: str
    needs_revision: bool
    revision_count: int
    final_response: str


class CurationOrchestrator:
    """
    Orchestrates multi-agent curation workflow using LangGraph.

    Evidence-First Pipeline Workflow:
    1. Retrieval: Get relevant statute and policy documents
    2. Extract: Extract verbatim requirement sentences from chunks
    3. Verify: Validate requirements through grounding gate
    4. Compose: Generate answer from verified requirements only
    5. Quality Review: Validate output quality and grounding
    6. Revision: If quality fails, revise composition (max 2 iterations)

    This follows an auditable Extract → Verify → Compose pattern.
    """

    def __init__(self, use_evidence_pipeline: bool = True, gateway: Optional["ModelGateway"] = None):
        """
        Initialize orchestrator with evidence-first or legacy pipeline.

        Args:
            use_evidence_pipeline: If True, use Extract→Verify→Compose pipeline.
                                   If False, use legacy free-form analysis pipeline.
            gateway: Optional ModelGateway for centralized LLM access.
        """
        self._gateway = _get_gateway(gateway)

        self.use_evidence_pipeline = use_evidence_pipeline

        # Initialize retrieval agent (used by both pipelines)
        self.retrieval_agent = RetrievalAgent()

        if use_evidence_pipeline:
            # Initialize Evidence-First Pipeline agents
            self.extraction_agent = EvidenceExtractionAgent()
            self.verification_agent = GroundingVerificationAgent()
            self.composition_agent = EvidenceCompositionAgent()
            self.quality_reviewer = QualityReviewerAgent()
            logger.info("Curation Orchestrator initialized with Evidence-First Pipeline")
        else:
            # Initialize legacy agents (backward compatibility)
            self.statute_analyst = StatuteAnalystAgent()
            self.policy_analyst = PolicyAnalystAgent()
            self.synthesis_agent = SynthesisAgent()
            self.quality_reviewer = QualityReviewerAgent()
            logger.info("Curation Orchestrator initialized with Legacy Pipeline")

        # Build workflow graph
        self.workflow = self._build_workflow()

        logger.info(f"Workflow type: {'Evidence-First' if use_evidence_pipeline else 'Legacy'}")

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph curation workflow"""

        # Create the graph
        workflow = StateGraph(CurationState)

        # Add common nodes
        workflow.add_node("retrieval", self._run_retrieval)

        if self.use_evidence_pipeline:
            # Evidence-First Pipeline nodes
            workflow.add_node("extract_evidence", self._run_evidence_extraction)
            workflow.add_node("verify_grounding", self._run_grounding_verification)
            workflow.add_node("compose_answer", self._run_evidence_composition)
            workflow.add_node("quality_review", self._run_quality_review)
            workflow.add_node("finalize", self._finalize_response)

            # Define Evidence-First workflow edges
            workflow.set_entry_point("retrieval")
            workflow.add_edge("retrieval", "extract_evidence")
            workflow.add_edge("extract_evidence", "verify_grounding")

            # Conditional: If no verified evidence, skip composition
            workflow.add_conditional_edges(
                "verify_grounding",
                self._has_verified_evidence,
                {
                    "compose": "compose_answer",
                    "no_evidence": "finalize"  # Return "No authoritative evidence" message
                }
            )

            workflow.add_edge("compose_answer", "quality_review")

            # After quality review, decide if revision needed
            workflow.add_conditional_edges(
                "quality_review",
                self._should_revise,
                {
                    "revise": "compose_answer",  # Retry composition
                    "finalize": "finalize"
                }
            )

            workflow.add_edge("finalize", END)

        else:
            # Legacy Pipeline nodes
            workflow.add_node("analyze_statutes", self._run_statute_analysis)
            workflow.add_node("analyze_policies", self._run_policy_analysis)
            workflow.add_node("synthesis", self._run_synthesis)
            workflow.add_node("quality_review", self._run_quality_review)
            workflow.add_node("finalize", self._finalize_response)

            # Define Legacy workflow edges
            workflow.set_entry_point("retrieval")
            workflow.add_edge("retrieval", "analyze_statutes")
            workflow.add_edge("analyze_statutes", "analyze_policies")
            workflow.add_edge("analyze_policies", "synthesis")
            workflow.add_edge("synthesis", "quality_review")

            workflow.add_conditional_edges(
                "quality_review",
                self._should_revise,
                {
                    "revise": "synthesis",
                    "finalize": "finalize"
                }
            )

            workflow.add_edge("finalize", END)

        return workflow.compile()

    def _run_retrieval(self, state: CurationState) -> CurationState:
        """Execute retrieval agent"""
        logger.info(f"Stage 1/5: Retrieval for question: {state['question'][:100]}...")

        result = self.retrieval_agent.execute({
            "question": state["question"],
            "topic": state["topic"],
            "sub_section": state.get("sub_section", ""),
            "category": state.get("category", ""),
            "top_k": 10
        })

        state["statute_chunks"] = result.get("statute_chunks", [])
        state["policy_chunks"] = result.get("policy_chunks", [])
        state["retrieval_metadata"] = result.get("retrieval_metadata", {})
        state["current_stage"] = "retrieval_complete"

        logger.info(
            f"Retrieved {len(state['statute_chunks'])} statute chunks, "
            f"{len(state['policy_chunks'])} policy chunks"
        )

        return state

    # Evidence-First Pipeline Methods

    def _run_evidence_extraction(self, state: CurationState) -> CurationState:
        """Execute evidence extraction agent (Stage 2: Extract)"""
        logger.info(f"Stage 2/6: Evidence Extraction")

        result = self.extraction_agent.execute({
            "question": state["question"],
            "statute_chunks": state["statute_chunks"],
            "policy_chunks": state["policy_chunks"]
        })

        state["extracted_requirements"] = result.get("extracted_requirements", [])
        state["extraction_metadata"] = result.get("extraction_metadata", {})
        state["current_stage"] = "extraction_complete"

        logger.info(
            f"Extracted {len(state['extracted_requirements'])} requirements "
            f"({state['extraction_metadata'].get('statute_requirements_extracted', 0)} statute, "
            f"{state['extraction_metadata'].get('policy_requirements_extracted', 0)} policy)"
        )

        return state

    def _run_grounding_verification(self, state: CurationState) -> CurationState:
        """Execute grounding verification agent (Stage 3: Verify)"""
        logger.info(f"Stage 3/6: Grounding Verification")

        result = self.verification_agent.execute({
            "question": state["question"],
            "extracted_requirements": state["extracted_requirements"]
        })

        state["verified_requirements"] = result.get("verified_requirements", [])
        state["rejected_requirements"] = result.get("rejected_requirements", [])
        state["verification_metadata"] = result.get("verification_metadata", {})
        state["has_sufficient_evidence"] = result.get("has_sufficient_evidence", False)
        state["missing_evidence"] = result.get("missing_evidence", [])
        state["current_stage"] = "verification_complete"

        logger.info(
            f"Verification complete: {len(state['verified_requirements'])} passed, "
            f"{len(state['rejected_requirements'])} rejected "
            f"(pass rate: {state['verification_metadata'].get('verification_pass_rate', 0):.1%})"
        )

        if not state["has_sufficient_evidence"]:
            logger.warning("INSUFFICIENT EVIDENCE - No verified requirements found")

        return state

    def _has_verified_evidence(self, state: CurationState) -> str:
        """
        Conditional gate: Check if we have sufficient verified evidence to compose answer.

        Returns:
            "compose" if evidence exists, "no_evidence" otherwise
        """
        has_evidence = state.get("has_sufficient_evidence", False)

        if has_evidence:
            logger.info("✅ Sufficient evidence found - proceeding to composition")
            return "compose"
        else:
            logger.warning("❌ No sufficient evidence - skipping composition")
            return "no_evidence"

    def _run_evidence_composition(self, state: CurationState) -> CurationState:
        """Execute evidence composition agent (Stage 4: Compose)"""
        revision_count = state.get("revision_count", 0)

        if revision_count > 0:
            logger.info(f"Stage 4/6: Evidence Composition (Revision #{revision_count})")
        else:
            logger.info(f"Stage 4/6: Evidence Composition")

        result = self.composition_agent.execute({
            "question": state["question"],
            "verified_requirements": state["verified_requirements"],
            "has_sufficient_evidence": state["has_sufficient_evidence"]
        })

        # Update state with composition results
        state["final_answer"] = result.get("final_answer", "")
        state["statute_summary"] = result.get("statute_summary", "")
        state["policy_summary"] = result.get("policy_summary", "")
        state["requirement_references"] = result.get("requirement_references", [])
        state["unused_requirements"] = result.get("unused_requirements", [])
        state["composition_confidence"] = result.get("composition_confidence", "insufficient")

        # Backward compatibility: set legacy fields
        state["final_summary"] = state["final_answer"]
        state["statute_analysis"] = state["statute_summary"]
        state["policy_analysis"] = state["policy_summary"]

        state["current_stage"] = "composition_complete"

        logger.info(
            f"Composition complete. Confidence: {state['composition_confidence']}. "
            f"Requirements used: {len(state['requirement_references'])}/{len(state['verified_requirements'])}"
        )

        return state

    # Legacy Pipeline Methods (for backward compatibility)

    def _run_statute_analysis(self, state: CurationState) -> CurationState:
        """Execute statute analyst agent"""
        logger.info(f"Stage 2a/5: Statute analysis")

        result = self.statute_analyst.execute({
            "question": state["question"],
            "topic": state["topic"],
            "statute_chunks": state["statute_chunks"],
            "statute_catalog": self.retrieval_agent.statute_catalog
        })

        state["statute_analysis"] = result.get("statute_analysis", "")
        state["statute_summary"] = result.get("statute_analysis", "")  # POC compatibility
        state["statute_confidence"] = result.get("confidence", "Medium")
        state["relevant_statutes"] = result.get("relevant_statutes", [])

        logger.info(
            f"Statute analysis complete. "
            f"Confidence: {state['statute_confidence']}. "
            f"Statutes found: {len(state['relevant_statutes'])}"
        )

        return state

    def _run_policy_analysis(self, state: CurationState) -> CurationState:
        """Execute policy analyst agent"""
        logger.info(f"Stage 2b/5: Policy analysis")

        result = self.policy_analyst.execute({
            "question": state["question"],
            "topic": state["topic"],
            "policy_chunks": state["policy_chunks"]
        })

        state["policy_analysis"] = result.get("policy_analysis", "")
        state["policy_summary"] = result.get("policy_analysis", "")  # POC compatibility
        state["policy_confidence"] = result.get("confidence", "Medium")
        state["key_requirements"] = result.get("key_requirements", [])
        state["recommendations"] = result.get("recommendations", [])

        logger.info(
            f"Policy analysis complete. "
            f"Confidence: {state['policy_confidence']}. "
            f"Requirements: {len(state['key_requirements'])}"
        )

        return state

    def _run_synthesis(self, state: CurationState) -> CurationState:
        """Execute synthesis agent"""
        revision_count = state.get("revision_count", 0)

        if revision_count > 0:
            logger.info(f"Stage 3/5: Synthesis (Revision #{revision_count})")
        else:
            logger.info(f"Stage 3/5: Synthesis")

        result = self.synthesis_agent.execute({
            "question": state["question"],
            "topic": state["topic"],
            "statute_analysis": state["statute_analysis"],
            "policy_analysis": state["policy_analysis"],
            "statute_confidence": state["statute_confidence"],
            "policy_confidence": state["policy_confidence"]
        })

        state["final_summary"] = result.get("final_summary", "")
        state["action_items"] = result.get("action_items", [])
        state["priority"] = result.get("priority", "Medium")
        state["current_stage"] = "synthesis_complete"

        logger.info(
            f"Synthesis complete. "
            f"Priority: {state['priority']}. "
            f"Action items: {len(state['action_items'])}"
        )

        return state

    def _run_quality_review(self, state: CurationState) -> CurationState:
        """Execute quality reviewer agent"""
        logger.info(f"Stage 4/5: Quality review")

        result = self.quality_reviewer.execute({
            "question": state["question"],
            "final_summary": state["final_summary"],
            "statute_analysis": state["statute_analysis"],
            "policy_analysis": state["policy_analysis"],
            "action_items": state["action_items"]
        })

        state["quality_score"] = result.get("quality_score", 0.0)
        state["passes_review"] = result.get("passes_review", False)
        state["quality_issues"] = result.get("issues", [])
        state["quality_suggestions"] = result.get("suggestions", [])
        state["current_stage"] = "quality_review_complete"

        logger.info(
            f"Quality review complete. "
            f"Score: {state['quality_score']}/10. "
            f"Passes: {state['passes_review']}. "
            f"Issues: {len(state['quality_issues'])}"
        )

        return state

    def _should_revise(self, state: CurationState) -> str:
        """
        Decide if synthesis should be revised based on quality review.

        Revise if:
        - Quality score < 7.0 AND
        - Revision count < 2 (max 2 revision attempts)
        """
        revision_count = state.get("revision_count", 0)
        passes = state.get("passes_review", False)

        if not passes and revision_count < 2:
            state["needs_revision"] = True
            state["revision_count"] = revision_count + 1
            logger.info(
                f"Quality review failed (score: {state['quality_score']}/10). "
                f"Attempting revision #{revision_count + 1}"
            )
            return "revise"
        else:
            state["needs_revision"] = False
            logger.info(
                f"Quality review {'passed' if passes else 'completed with issues'}. "
                f"Finalizing output."
            )
            return "finalize"

    def _finalize_response(self, state: CurationState) -> CurationState:
        """Generate final user-facing response"""
        logger.info(f"Stage 5/5: Finalizing response")

        # Construct final response with all components
        response_parts = []

        # Add quality score banner
        score = state["quality_score"]
        if score >= 9.0:
            quality_badge = "🌟 **Excellent Quality** (Score: {:.1f}/10)".format(score)
        elif score >= 7.0:
            quality_badge = "✅ **Good Quality** (Score: {:.1f}/10)".format(score)
        else:
            quality_badge = "⚠️ **Review Recommended** (Score: {:.1f}/10)".format(score)

        response_parts.append(quality_badge)
        response_parts.append("")  # Blank line

        # Add final summary
        response_parts.append(state["final_summary"])

        # Add metadata footer
        response_parts.append("")
        response_parts.append("---")
        response_parts.append("")
        response_parts.append("**Processing Metadata:**")
        response_parts.append(f"- Priority: {state['priority']}")
        response_parts.append(f"- Statute Confidence: {state['statute_confidence']}")
        response_parts.append(f"- Policy Confidence: {state['policy_confidence']}")
        response_parts.append(f"- Relevant Statutes: {', '.join(state['relevant_statutes'][:5]) if state['relevant_statutes'] else 'None identified'}")
        response_parts.append(f"- Revision Count: {state.get('revision_count', 0)}")

        # Add quality issues if any
        if state["quality_issues"]:
            response_parts.append("")
            response_parts.append("**Quality Issues Noted:**")
            for issue in state["quality_issues"]:
                response_parts.append(f"- {issue}")

        final_response = "\n".join(response_parts)

        state["final_response"] = final_response
        state["current_stage"] = "complete"

        # Add to message history
        state["messages"].append(AIMessage(content=final_response))

        logger.info("Curation workflow complete")

        return state

    def _build_audit_trail(self, state: CurationState) -> Dict[str, Any]:
        """
        Build complete evidence audit trail from state.

        Returns comprehensive lineage from chunks → extracts → verified → composed answer.
        """
        return {
            "retrieval_stage": {
                "statute_chunks_retrieved": len(state.get("statute_chunks", [])),
                "policy_chunks_retrieved": len(state.get("policy_chunks", [])),
                "total_chunks": len(state.get("statute_chunks", [])) + len(state.get("policy_chunks", []))
            },
            "extraction_stage": {
                "total_requirements_extracted": len(state.get("extracted_requirements", [])),
                "statute_requirements": len([r for r in state.get("extracted_requirements", []) if r.get("source_type") == "statute"]),
                "policy_requirements": len([r for r in state.get("extracted_requirements", []) if r.get("source_type") == "policy"]),
                "extraction_metadata": state.get("extraction_metadata", {})
            },
            "verification_stage": {
                "total_requirements_verified": len(state.get("verified_requirements", [])),
                "requirements_passed": len(state.get("verified_requirements", [])),
                "requirements_rejected": len(state.get("rejected_requirements", [])),
                "verification_pass_rate": state.get("verification_metadata", {}).get("verification_pass_rate", 0.0),
                "rejection_reasons": state.get("verification_metadata", {}).get("rejection_reasons", {}),
                "has_sufficient_evidence": state.get("has_sufficient_evidence", False),
                "missing_evidence": state.get("missing_evidence", [])
            },
            "composition_stage": {
                "requirements_used": len(state.get("requirement_references", [])),
                "requirements_unused": len(state.get("unused_requirements", [])),
                "composition_confidence": state.get("composition_confidence", "insufficient"),
                "has_requirement_references": len(state.get("requirement_references", [])) > 0
            },
            "overall": {
                "pipeline_type": "evidence_first" if self.use_evidence_pipeline else "legacy",
                "grounding_confidence": state.get("grounding_confidence", "insufficient"),
                "quality_score": state.get("quality_score", 0.0),
                "passes_review": state.get("passes_review", False),
                "revision_count": state.get("revision_count", 0)
            }
        }

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the multi-agent curation workflow.

        Args:
            input_data: {
                "question": str,      # IP Question from CSV
                "topic": str,         # Section + Sub-Section + Category
                "sub_section": str,   # IP Sub-Section
                "category": str       # topic_name
            }

        Returns:
            {
                "success": bool,
                "final_summary": str,
                "final_response": str,  # Formatted with metadata
                "action_items": List[str],
                "priority": str,
                "quality_score": float,
                "passes_review": bool,
                "metadata": {...}
            }
        """
        logger.info(f"Curation orchestrator executing for: {input_data.get('question', '')[:100]}...")

        # Initialize state
        initial_state: CurationState = {
            "messages": [HumanMessage(content=input_data["question"])],
            "question": input_data["question"],
            "topic": input_data["topic"],
            "sub_section": input_data.get("sub_section", ""),
            "category": input_data.get("category", ""),

            # Retrieval
            "statute_chunks": [],
            "policy_chunks": [],
            "retrieval_metadata": {},

            # Evidence extraction (Evidence-First Pipeline)
            "extracted_requirements": [],
            "extraction_metadata": {},

            # Grounding verification (Evidence-First Pipeline)
            "verified_requirements": [],
            "rejected_requirements": [],
            "verification_metadata": {},
            "has_sufficient_evidence": False,
            "missing_evidence": [],

            # Evidence composition (Evidence-First Pipeline)
            "final_answer": "",
            "requirement_references": [],
            "unused_requirements": [],
            "composition_confidence": "insufficient",

            # Audit trail (Evidence-First Pipeline)
            "evidence_audit_trail": {},
            "grounding_confidence": "insufficient",

            # Legacy fields (for backward compatibility)
            "statute_analysis": "",
            "statute_summary": "",
            "statute_confidence": "",
            "relevant_statutes": [],
            "policy_analysis": "",
            "policy_summary": "",
            "policy_confidence": "",
            "key_requirements": [],
            "recommendations": [],
            "final_summary": "",
            "action_items": [],
            "priority": "",

            # Quality review
            "quality_score": 0.0,
            "passes_review": False,
            "quality_issues": [],
            "quality_suggestions": [],

            # Control
            "current_stage": "initialized",
            "needs_revision": False,
            "revision_count": 0,
            "final_response": ""
        }

        # Run the workflow
        try:
            final_state = self.workflow.invoke(initial_state)

            # Build evidence audit trail
            evidence_audit_trail = self._build_audit_trail(final_state)

            return {
                "success": True,
                # POC-compatible output fields (3-stage summaries)
                "statute_summary": final_state.get("statute_summary", ""),
                "policy_summary": final_state.get("policy_summary", ""),
                "final_summary": final_state.get("final_summary", ""),
                # Evidence-First Pipeline fields
                "final_answer": final_state.get("final_answer", ""),
                "extracted_requirements": final_state.get("extracted_requirements", []),
                "verified_requirements": final_state.get("verified_requirements", []),
                "rejected_requirements": final_state.get("rejected_requirements", []),
                "requirement_references": final_state.get("requirement_references", []),
                "missing_evidence": final_state.get("missing_evidence", []),
                "composition_confidence": final_state.get("composition_confidence", "insufficient"),
                "evidence_audit_trail": evidence_audit_trail,
                # Additional detailed fields
                "statute_analysis": final_state.get("statute_analysis", ""),
                "policy_analysis": final_state.get("policy_analysis", ""),
                "final_response": final_state["final_response"],
                "action_items": final_state.get("action_items", []),
                "priority": final_state.get("priority", ""),
                "quality_score": final_state["quality_score"],
                "passes_review": final_state["passes_review"],
                "metadata": {
                    "statute_confidence": final_state.get("statute_confidence", ""),
                    "policy_confidence": final_state.get("policy_confidence", ""),
                    "relevant_statutes": final_state.get("relevant_statutes", []),
                    "revision_count": final_state["revision_count"],
                    "quality_issues": final_state["quality_issues"],
                    "quality_suggestions": final_state["quality_suggestions"],
                    "statute_chunks_retrieved": len(final_state["statute_chunks"]),
                    "policy_chunks_retrieved": len(final_state["policy_chunks"]),
                    # Evidence-First Pipeline metadata
                    "extraction_metadata": final_state.get("extraction_metadata", {}),
                    "verification_metadata": final_state.get("verification_metadata", {}),
                    "grounding_confidence": final_state.get("grounding_confidence", "insufficient"),
                    "has_sufficient_evidence": final_state.get("has_sufficient_evidence", False)
                }
            }

        except Exception as e:
            logger.error(f"Curation orchestrator failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "final_summary": "",
                "final_response": f"An error occurred during curation: {str(e)}"
            }
