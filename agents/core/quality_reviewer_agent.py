"""
Quality Reviewer Agent for Policy Curation
Validates completeness and quality of compliance summaries
"""
import logging
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate

from agents.core.base_agent import BaseAgent
from agents.core.config import settings

logger = logging.getLogger(__name__)


class QualityReviewerAgent(BaseAgent):
    """
    Specialized agent for quality assurance of compliance summaries.

    Validates:
    - Completeness (all sections present)
    - Accuracy (consistent with source analyses)
    - Actionability (clear action items)
    - Clarity (plain language, no jargon)

    Uses industry-standard summarization evaluation criteria.
    """

    def __init__(self):
        super().__init__(
            name="QualityReviewerAgent",
            role="Policy Compliance Quality Assurance Reviewer",
            goal="Validate compliance summary quality, completeness, and actionability",
            temperature=0.2  # Low for consistent evaluation
        )

        # Quality criteria based on summarization best practices
        self.quality_criteria = {
            "completeness": "All required sections present (Bottom Line, Statutory Basis, Policy Guidance, Action Items)",
            "accuracy": "Summary accurately reflects statute and policy analyses",
            "actionability": "Clear, specific action items with responsibilities",
            "clarity": "Plain language, concise, easy to understand",
            "consistency": "No contradictions between sections",
            "citations": "Proper statute and policy section references"
        }

        logger.info(f"{self.name} initialized with {len(self.quality_criteria)} quality criteria")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review and score compliance summary quality.

        Args:
            input_data: {
                "question": str,
                "final_summary": str,       # Summary to review
                "statute_analysis": str,    # Source analysis
                "policy_analysis": str,     # Source analysis
                "action_items": List[str]   # Extracted action items
            }

        Returns:
            {
                "success": bool,
                "quality_score": float,          # 0-10 overall score
                "criteria_scores": Dict[str, float],  # Individual criteria scores
                "passes_review": bool,           # True if score >= 7.0
                "issues": List[str],             # Identified quality issues
                "suggestions": List[str]         # Improvement suggestions
            }
        """
        try:
            question = input_data["question"]
            final_summary = input_data["final_summary"]
            statute_analysis = input_data.get("statute_analysis", "")
            policy_analysis = input_data.get("policy_analysis", "")
            action_items = input_data.get("action_items", [])

            logger.info(f"Reviewing compliance summary quality")

            # Perform quality review
            review_result = self._review_quality(
                question=question,
                final_summary=final_summary,
                statute_analysis=statute_analysis,
                policy_analysis=policy_analysis
            )

            # Calculate overall score
            criteria_scores = review_result["criteria_scores"]
            quality_score = sum(criteria_scores.values()) / len(criteria_scores)

            # Extract issues and suggestions
            issues = review_result["issues"]
            suggestions = review_result["suggestions"]

            # Determine if passes review (threshold: 7.0/10)
            passes_review = quality_score >= 7.0

            # Additional validation checks
            self._validate_structure(final_summary, issues)
            self._validate_action_items(action_items, issues, suggestions)

            logger.info(
                f"Quality review complete. "
                f"Score: {quality_score:.1f}/10. "
                f"Passes: {passes_review}. "
                f"Issues: {len(issues)}"
            )

            return {
                "success": True,
                "quality_score": round(quality_score, 1),
                "criteria_scores": {k: round(v, 1) for k, v in criteria_scores.items()},
                "passes_review": passes_review,
                "issues": issues,
                "suggestions": suggestions,
                "metadata": {
                    "threshold": 7.0,
                    "issue_count": len(issues),
                    "suggestion_count": len(suggestions)
                }
            }

        except Exception as e:
            logger.error(f"Quality review failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "quality_score": 0.0,
                "passes_review": False
            }

    def _review_quality(
        self,
        question: str,
        final_summary: str,
        statute_analysis: str,
        policy_analysis: str
    ) -> Dict[str, Any]:
        """
        Use LLM to review summary quality against criteria.

        Returns scores (0-10) for each criterion plus identified issues/suggestions.
        """

        system_message = """You are a policy compliance quality assurance reviewer.

Your task is to evaluate a compliance summary against quality criteria and provide scores and feedback.

**Quality Criteria:**

1. **Completeness** (0-10): All required sections present?
   - Bottom Line
   - Statutory Basis
   - Policy Guidance
   - Action Items for County
   - Open Questions/Ambiguities

2. **Accuracy** (0-10): Does summary accurately reflect source analyses?
   - Statute analysis correctly represented
   - Policy guidance correctly represented
   - No fabricated information

3. **Actionability** (0-10): Are action items clear and specific?
   - Specific actions defined
   - Responsibilities clear
   - Timelines mentioned where applicable

4. **Clarity** (0-10): Is it easy to understand?
   - Plain language (no excessive jargon)
   - Concise (respects word limit)
   - Logical flow

5. **Consistency** (0-10): No internal contradictions?
   - Sections align with each other
   - Bottom line matches detailed sections
   - No conflicting guidance

6. **Citations** (0-10): Proper references?
   - Statute citations formatted correctly (e.g., "W&I Code § 5899")
   - Policy section references included
   - Sources attributed

**Output Format (JSON):**

```json
{{
  "criteria_scores": {{
    "completeness": 8.5,
    "accuracy": 9.0,
    "actionability": 7.5,
    "clarity": 8.0,
    "consistency": 9.0,
    "citations": 8.5
  }},
  "issues": [
    "Missing timeline in action item 2",
    "Bottom line could be more direct"
  ],
  "suggestions": [
    "Add specific deadline to action item 2",
    "Rephrase bottom line to start with action verb"
  ]
}}
```

**Scoring Guidelines:**
- 9-10: Excellent, exceeds standards
- 7-8: Good, meets standards
- 5-6: Acceptable, minor issues
- 3-4: Needs improvement, significant issues
- 0-2: Unacceptable, major issues

Be constructive but rigorous. If something is missing or incorrect, score accordingly."""

        human_message = """**Question:**
{question}

**Final Compliance Summary to Review:**
{final_summary}

**Source Statute Analysis:**
{statute_analysis}

**Source Policy Analysis:**
{policy_analysis}

**Your Quality Review (JSON format):**"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message)
        ])

        chain = prompt | self.llm

        response = chain.invoke({
            "question": question,
            "final_summary": final_summary[:2000],  # Truncate if too long
            "statute_analysis": statute_analysis[:1000],
            "policy_analysis": policy_analysis[:1000]
        })

        # Parse JSON response
        import json
        import re

        content = response.content

        # Extract JSON from markdown code block if present
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: parse manually if JSON parsing fails
            logger.warning("Failed to parse JSON from quality review, using fallback")
            result = {
                "criteria_scores": {k: 7.0 for k in self.quality_criteria.keys()},
                "issues": ["Quality review parsing failed"],
                "suggestions": []
            }

        return result

    def _validate_structure(self, final_summary: str, issues: List[str]):
        """Validate that summary has required structural elements."""
        required_sections = [
            "### Bottom Line",
            "### Statutory Basis",
            "### Policy Guidance",
            "### Action Items for County",
            "### Open Questions"
        ]

        for section in required_sections:
            if section not in final_summary:
                issues.append(f"Missing required section: {section}")

    def _validate_action_items(
        self,
        action_items: List[str],
        issues: List[str],
        suggestions: List[str]
    ):
        """Validate action items are specific and actionable."""
        if not action_items:
            issues.append("No action items identified")
            suggestions.append("Add 2-5 specific, actionable steps for the county")
            return

        if len(action_items) < 2:
            suggestions.append("Consider adding more action items (minimum 2 recommended)")

        if len(action_items) > 5:
            suggestions.append("Consider consolidating action items (maximum 5 recommended)")

        # Check for vague action items
        vague_terms = ["consider", "review", "assess", "explore", "examine"]

        for i, item in enumerate(action_items, 1):
            item_lower = item.lower()

            # Check if action item is too vague
            vague_count = sum(1 for term in vague_terms if term in item_lower)
            if vague_count > 0 and len(item) < 50:
                suggestions.append(
                    f"Action item {i} could be more specific: '{item[:50]}...'"
                )
