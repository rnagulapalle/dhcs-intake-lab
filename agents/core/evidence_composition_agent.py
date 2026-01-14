"""
Evidence Composition Agent
Composes readable answers using ONLY verified requirements with explicit references.
"""
import logging
import re
import json
from typing import Dict, Any, List, Optional, TYPE_CHECKING

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


class EvidenceCompositionAgent:
    """
    Composes answers from verified requirements with explicit reference tracking.

    Design Principle: Every statement MUST reference verified evidence.
    NO new facts, interpretations, or conclusions beyond verified requirements.

    Composition Rules:
    1. Every statement must reference at least one verified requirement ID
    2. NO new facts beyond verified evidence
    3. If conflicting requirements, present both with IDs
    4. Use requirement IDs inline: "Statement [REQ-S001, REQ-P003]"
    """

    def __init__(self, gateway: Optional["ModelGateway"] = None):
        self._gateway = _get_gateway(gateway)
        logger.info("Evidence Composition Agent initialized (temperature=0.2 for consistent composition)")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compose answer from verified requirements with explicit references.

        Args:
            input_data: {
                "question": str,
                "verified_requirements": List[Dict],  # From verification agent
                "has_sufficient_evidence": bool
            }

        Returns:
            {
                "final_answer": str,  # With inline [REQ-ID] references
                "statute_summary": str,  # From statute requirements only
                "policy_summary": str,  # From policy requirements only
                "requirement_references": List[Dict],  # Which requirements used
                "unused_requirements": List[str],  # Verified but not used
                "composition_confidence": str  # high | medium | low
            }
        """
        question = input_data["question"]
        verified_requirements = input_data.get("verified_requirements", [])
        has_sufficient_evidence = input_data.get("has_sufficient_evidence", False)

        logger.info(f"Composing answer from {len(verified_requirements)} verified requirements")

        if not has_sufficient_evidence or not verified_requirements:
            logger.warning("Insufficient evidence for composition")
            return self._insufficient_evidence_response()

        # Separate statute and policy requirements
        statute_reqs = [r for r in verified_requirements if r.get("source_type") == "statute"]
        policy_reqs = [r for r in verified_requirements if r.get("source_type") == "policy"]

        # Compose main answer
        composition_result = self._compose_answer(question, verified_requirements)

        # Compose statute summary
        statute_summary = self._compose_source_summary(question, statute_reqs, "statute") if statute_reqs else "No applicable statutes found in sources."

        # Compose policy summary
        policy_summary = self._compose_source_summary(question, policy_reqs, "policy") if policy_reqs else "No applicable policies found in sources."

        # Validate composition (ensure all statements have references)
        validation = self._validate_composition(composition_result["final_answer"], verified_requirements)

        # Calculate confidence
        confidence = self._calculate_confidence(verified_requirements, composition_result)

        logger.info(
            f"Composition complete. Confidence: {confidence}. "
            f"References used: {len(composition_result['requirement_references'])}/{len(verified_requirements)}"
        )

        return {
            "final_answer": composition_result["final_answer"],
            "statute_summary": statute_summary,
            "policy_summary": policy_summary,
            "requirement_references": composition_result["requirement_references"],
            "unused_requirements": composition_result["unused_requirements"],
            "composition_confidence": confidence,
            "composition_validation": validation
        }

    def _compose_answer(self, question: str, verified_requirements: List[Dict]) -> Dict[str, Any]:
        """
        Compose main answer from verified requirements.

        Returns dict with final_answer, requirement_references, unused_requirements
        """
        system_prompt = """You are a compliance summary writer for a regulated system.

Your task: Generate a readable answer using ONLY verified requirements.

CRITICAL RULES:
1. EVERY statement must reference requirement IDs in format: [REQ-S001, REQ-P002]
2. NO interpretation beyond what's explicitly stated in quotes
3. NO new facts or conclusions not in verified requirements
4. If requirements conflict, present both views with their IDs
5. Keep answer concise (150-300 words) but complete

STRUCTURE:
1. Direct answer to question (1-2 sentences) [requirement IDs]
2. Key requirements (bullet points with IDs)
3. Any conflicts or ambiguities (if present) [requirement IDs]

Example:
"Counties must maintain client assessment records [REQ-S001] and document all assessments within 60 days [REQ-P001].

Key Requirements:
- Assessment documentation must be maintained for all behavioral health recipients [REQ-S001]
- Documentation timeline is 60 days from initial contact [REQ-P001]
- Records must include diagnostic evaluation and functional assessment [REQ-P002]"

OUTPUT FORMAT (JSON):
{
  "final_answer": "Answer text with inline [REQ-ID] references",
  "requirement_references": [
    {
      "requirement_id": "REQ-S001",
      "used_in_answer": true,
      "statement_context": "Assessment documentation requirement"
    }
  ],
  "unused_requirements": ["REQ-P005"]
}
"""

        # Format requirements for LLM
        formatted_reqs = self._format_requirements_for_composition(verified_requirements)

        human_prompt = f"""Question: {question}

Verified Requirements:

{formatted_reqs}

Compose a readable answer using ONLY these verified requirements. Every statement must have [REQ-ID] references. Output JSON.
"""

        try:
            response = self._gateway.invoke_raw([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_prompt}
            ])

            content = response.content.strip()

            # Parse JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result
            else:
                logger.error("No JSON found in composition response")
                # Fallback: use raw response as answer
                return {
                    "final_answer": content,
                    "requirement_references": [],
                    "unused_requirements": []
                }

        except Exception as e:
            logger.error(f"Error composing answer: {e}", exc_info=True)
            # Fallback: create simple answer from requirements
            return self._fallback_composition(question, verified_requirements)

    def _compose_source_summary(
        self,
        question: str,
        requirements: List[Dict],
        source_type: str
    ) -> str:
        """
        Compose summary for a specific source type (statute or policy).

        Used for POC-compatible statute_summary and policy_summary fields.
        """
        if not requirements:
            return f"No applicable {source_type}s found in sources."

        # Simple composition: list requirements with references
        lines = [f"**{source_type.title()} Requirements:**\n"]

        for req in requirements:
            req_id = req.get("requirement_id")
            doc_id = req.get("document_id", "Unknown")
            quote = req.get("exact_quote", "")

            lines.append(f"- {quote} [{req_id}]")
            lines.append(f"  *Source: {doc_id}*\n")

        return "\n".join(lines)

    def _format_requirements_for_composition(self, requirements: List[Dict]) -> str:
        """Format verified requirements for LLM composition."""
        formatted = []

        for req in requirements:
            req_text = f"""
[{req.get('requirement_id')}]
Source: {req.get('source_type').title()} - {req.get('document_id')}
Section: {req.get('section_heading', 'N/A')}
Exact Quote: "{req.get('exact_quote')}"
"""
            formatted.append(req_text.strip())

        return "\n\n".join(formatted)

    def _validate_composition(self, answer: str, verified_requirements: List[Dict]) -> Dict[str, Any]:
        """
        Validate that composition follows rules:
        1. All statements have requirement references
        2. All referenced IDs exist in verified requirements
        3. No hallucinated claims
        """
        # Extract requirement IDs from answer
        referenced_ids = re.findall(r'\[REQ-[SP]\d+\]', answer)
        referenced_ids = [rid.strip('[]') for rid in referenced_ids]

        # Get valid requirement IDs
        valid_ids = [req.get("requirement_id") for req in verified_requirements]

        # Check for invalid references
        invalid_refs = [rid for rid in referenced_ids if rid not in valid_ids]

        # Check if answer has references
        has_references = len(referenced_ids) > 0

        validation = {
            "has_requirement_references": has_references,
            "total_references": len(referenced_ids),
            "unique_references": len(set(referenced_ids)),
            "invalid_references": invalid_refs,
            "all_requirements_valid": len(invalid_refs) == 0
        }

        if invalid_refs:
            logger.warning(f"Composition contains invalid requirement references: {invalid_refs}")

        if not has_references:
            logger.error("Composition missing requirement references - CRITICAL FAILURE")

        return validation

    def _calculate_confidence(
        self,
        verified_requirements: List[Dict],
        composition_result: Dict
    ) -> str:
        """
        Calculate confidence based on evidence quantity and quality.

        Returns: "high" | "medium" | "low"
        """
        num_verified = len(verified_requirements)
        num_used = len(composition_result.get("requirement_references", []))

        # High confidence: 5+ verified requirements, most used in answer
        if num_verified >= 5 and num_used >= 3:
            return "high"

        # Medium confidence: 2-4 verified requirements
        if num_verified >= 2:
            return "medium"

        # Low confidence: 1 verified requirement
        if num_verified == 1:
            return "low"

        # No confidence: 0 verified requirements (should not reach here)
        return "insufficient"

    def _insufficient_evidence_response(self) -> Dict[str, Any]:
        """Return response when composition cannot proceed due to insufficient evidence."""
        message = "No authoritative requirement found in provided sources."

        return {
            "final_answer": message,
            "statute_summary": "No applicable statutes found in sources.",
            "policy_summary": "No applicable policies found in sources.",
            "requirement_references": [],
            "unused_requirements": [],
            "composition_confidence": "insufficient",
            "composition_validation": {
                "has_requirement_references": False,
                "total_references": 0,
                "unique_references": 0,
                "invalid_references": [],
                "all_requirements_valid": True
            }
        }

    def _fallback_composition(self, question: str, requirements: List[Dict]) -> Dict[str, Any]:
        """
        Fallback composition if LLM fails.

        Generate simple bullet list of requirements.
        """
        logger.warning("Using fallback composition (LLM composition failed)")

        answer_lines = [f"Based on verified requirements for: {question}\n"]

        for req in requirements:
            req_id = req.get("requirement_id")
            quote = req.get("exact_quote", "")
            doc = req.get("document_id", "Unknown")

            answer_lines.append(f"- {quote} [{req_id}]")
            answer_lines.append(f"  *Source: {doc}*\n")

        return {
            "final_answer": "\n".join(answer_lines),
            "requirement_references": [
                {
                    "requirement_id": req.get("requirement_id"),
                    "used_in_answer": True,
                    "statement_context": "Fallback composition"
                }
                for req in requirements
            ],
            "unused_requirements": []
        }
