"""
Grounding Verification Agent
Validates that extracted requirements explicitly address the question and are fully supported by quotes.
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


class GroundingVerificationAgent:
    """
    Validates extracted requirements through strict grounding gate.

    Design Principle: Act as a GATE - only verified, grounded evidence passes through.
    Reject anything that requires inference, speculation, or external context.

    Verification Criteria:
    1. Explicit addressing: Does requirement explicitly address the question?
    2. Quote support: Is requirement fully supported by exact quote (no inference)?
    3. Completeness: Is quote self-contained without missing context?
    """

    def __init__(self, gateway: Optional["ModelGateway"] = None):
        self._gateway = _get_gateway(gateway)
        logger.info("Grounding Verification Agent initialized (temperature=0.0 for determinism)")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify that extracted requirements are grounded and address the question.

        Args:
            input_data: {
                "question": str,
                "extracted_requirements": List[Dict]  # From extraction agent
            }

        Returns:
            {
                "verified_requirements": List[Dict],  # Passed verification
                "rejected_requirements": List[Dict],  # Failed verification with reasons
                "verification_metadata": Dict,
                "has_sufficient_evidence": bool,
                "missing_evidence": List[str]  # What evidence is missing
            }
        """
        question = input_data["question"]
        extracted_requirements = input_data.get("extracted_requirements", [])

        logger.info(f"Verifying {len(extracted_requirements)} extracted requirements")

        if not extracted_requirements:
            logger.warning("No extracted requirements to verify")
            return self._no_evidence_response(question)

        # Verify each requirement
        verified = []
        rejected = []

        for req in extracted_requirements:
            verification_result = self._verify_requirement(question, req)

            if verification_result["verified"]:
                verified.append({
                    **req,
                    "verification_rationale": verification_result["rationale"]
                })
            else:
                rejected.append({
                    **req,
                    "verified": False,
                    "rejection_reason": verification_result["rejection_reason"],
                    "rejection_rationale": verification_result["rationale"]
                })

        # Check if we have sufficient evidence
        has_sufficient = len(verified) > 0

        metadata = {
            "total_requirements_verified": len(extracted_requirements),
            "requirements_passed": len(verified),
            "requirements_rejected": len(rejected),
            "verification_pass_rate": len(verified) / len(extracted_requirements) if extracted_requirements else 0.0,
            "rejection_reasons": self._count_rejection_reasons(rejected)
        }

        logger.info(
            f"Verification complete: {len(verified)} passed, {len(rejected)} rejected "
            f"(pass rate: {metadata['verification_pass_rate']:.1%})"
        )

        if not has_sufficient:
            return self._no_evidence_response(question, rejected)

        return {
            "verified_requirements": verified,
            "rejected_requirements": rejected,
            "verification_metadata": metadata,
            "has_sufficient_evidence": True,
            "missing_evidence": []
        }

    def _verify_requirement(self, question: str, requirement: Dict) -> Dict[str, Any]:
        """
        Verify a single requirement against grounding criteria.

        Returns:
            {
                "verified": bool,
                "rejection_reason": str | None,
                "rationale": str
            }
        """
        system_prompt = """You are a grounding verification specialist for a regulated compliance system.

Your task: Verify that an extracted requirement meets STRICT grounding criteria.

VERIFICATION CRITERIA (ALL must pass):

1. EXPLICIT ADDRESSING
   ✅ Pass: Requirement directly answers the question
   ❌ Fail: Requirement is tangential, implied, or speculative

2. QUOTE SUPPORT
   ✅ Pass: The exact quote fully proves the requirement
   ❌ Fail: Requirement requires inference beyond the quote

3. COMPLETENESS
   ✅ Pass: Quote is self-contained and understandable alone
   ❌ Fail: Quote requires surrounding context to make sense

REJECTION REASONS:
- "does_not_address_question": Requirement is not relevant to question
- "requires_inference": Quote doesn't fully support requirement (needs interpretation)
- "incomplete_quote": Quote is missing context or not self-contained

OUTPUT FORMAT (JSON):
{
  "verified": true | false,
  "rejection_reason": null | "does_not_address_question" | "requires_inference" | "incomplete_quote",
  "rationale": "Brief explanation of verification decision"
}

Be STRICT - when in doubt, REJECT. Better to say "no evidence" than to hallucinate.
"""

        human_prompt = f"""Question: {question}

Requirement to Verify:
- Requirement ID: {requirement.get('requirement_id')}
- Source Type: {requirement.get('source_type')}
- Document: {requirement.get('document_id')}
- Section: {requirement.get('section_heading', 'N/A')}
- Exact Quote: "{requirement.get('exact_quote')}"

Does this requirement pass ALL verification criteria? Output JSON.
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
                logger.warning(f"No JSON found in verification response for {requirement.get('requirement_id')}")
                # Default to rejection if LLM response is malformed
                return {
                    "verified": False,
                    "rejection_reason": "verification_error",
                    "rationale": "LLM verification response was malformed"
                }

        except Exception as e:
            logger.error(f"Error verifying requirement {requirement.get('requirement_id')}: {e}", exc_info=True)
            return {
                "verified": False,
                "rejection_reason": "verification_error",
                "rationale": f"Verification failed with error: {str(e)}"
            }

    def _no_evidence_response(self, question: str, rejected_requirements: List[Dict] = None) -> Dict[str, Any]:
        """
        Generate response when no verified evidence is found.

        This is a FAIL-SAFE response - better to say "no evidence" than hallucinate.
        """
        logger.warning("No verified requirements found - returning NO_AUTHORITATIVE_EVIDENCE response")

        # Analyze rejections to understand what evidence is missing
        missing_evidence = self._infer_missing_evidence(question, rejected_requirements or [])

        return {
            "verified_requirements": [],
            "rejected_requirements": rejected_requirements or [],
            "verification_metadata": {
                "total_requirements_verified": len(rejected_requirements) if rejected_requirements else 0,
                "requirements_passed": 0,
                "requirements_rejected": len(rejected_requirements) if rejected_requirements else 0,
                "verification_pass_rate": 0.0,
                "rejection_reasons": self._count_rejection_reasons(rejected_requirements or [])
            },
            "has_sufficient_evidence": False,
            "missing_evidence": missing_evidence,
            "result": "NO_AUTHORITATIVE_EVIDENCE",
            "message": "No authoritative requirement found in provided sources."
        }

    def _infer_missing_evidence(self, question: str, rejected_requirements: List[Dict]) -> List[str]:
        """
        Infer what evidence is missing based on question and rejected requirements.
        """
        missing = []

        # Check if we have statute requirements
        statute_reqs = [r for r in rejected_requirements if r.get("source_type") == "statute"]
        if not statute_reqs:
            missing.append("Statute explicitly addressing question topic")

        # Check if we have policy requirements
        policy_reqs = [r for r in rejected_requirements if r.get("source_type") == "policy"]
        if not policy_reqs:
            missing.append("Policy guidance explicitly addressing question topic")

        # Analyze rejection reasons
        rejection_reasons = self._count_rejection_reasons(rejected_requirements)
        if rejection_reasons.get("does_not_address_question", 0) > 0:
            missing.append("Requirements directly relevant to the specific question asked")
        if rejection_reasons.get("requires_inference", 0) > 0:
            missing.append("Explicit requirements (not implied or inferred)")
        if rejection_reasons.get("incomplete_quote", 0) > 0:
            missing.append("Complete requirement context (quotes are fragmentary)")

        if not missing:
            missing.append("Authoritative source addressing this specific question")

        return missing

    def _count_rejection_reasons(self, rejected_requirements: List[Dict]) -> Dict[str, int]:
        """Count frequency of rejection reasons."""
        counts = {}
        for req in rejected_requirements:
            reason = req.get("rejection_reason", "unknown")
            counts[reason] = counts.get(reason, 0) + 1
        return counts
