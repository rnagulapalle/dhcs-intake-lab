"""
Synthesis Agent for Policy Curation
Creates final compliance summary by combining statute and policy analyses
"""
import logging
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate

from agents.core.base_agent import BaseAgent
from agents.core.config import settings

logger = logging.getLogger(__name__)


class SynthesisAgent(BaseAgent):
    """
    Specialized agent for synthesizing statute and policy analyses into
    a cohesive, actionable compliance summary for county leadership.

    Uses:
    - Moderate temperature (0.3) for clear, executive-friendly synthesis
    - Structured output with "Bottom Line" executive summary
    - Action-oriented language
    - Plain language (no legalese)

    Output is optimized for county decision-makers who need clear guidance.
    """

    def __init__(self):
        super().__init__(
            name="SynthesisAgent",
            role="Policy Compliance Consultant",
            goal="Create clear, actionable compliance summaries for county leadership",
            temperature=0.3  # Moderate for clear, varied language
        )

        logger.info(f"{self.name} initialized for compliance synthesis")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize statute and policy analyses into final summary.

        Args:
            input_data: {
                "question": str,              # IP Question
                "topic": str,                 # Section + Sub-Section + Category
                "statute_analysis": str,      # From StatuteAnalystAgent
                "policy_analysis": str,       # From PolicyAnalystAgent
                "statute_confidence": str,    # High/Medium/Low
                "policy_confidence": str      # High/Medium/Low
            }

        Returns:
            {
                "success": bool,
                "final_summary": str,        # Markdown-formatted summary
                "action_items": List[str],   # Extracted action items
                "priority": str              # High/Medium/Low
            }
        """
        try:
            question = input_data["question"]
            topic = input_data["topic"]
            statute_analysis = input_data["statute_analysis"]
            policy_analysis = input_data["policy_analysis"]
            statute_confidence = input_data.get("statute_confidence", "Medium")
            policy_confidence = input_data.get("policy_confidence", "Medium")

            logger.info(f"Synthesizing compliance summary for topic: {topic}")

            # Generate synthesis
            final_summary = self._synthesize(
                question=question,
                topic=topic,
                statute_analysis=statute_analysis,
                policy_analysis=policy_analysis,
                statute_confidence=statute_confidence,
                policy_confidence=policy_confidence
            )

            # Extract action items
            action_items = self._extract_action_items(final_summary)

            # Determine priority
            priority = self._determine_priority(statute_analysis, policy_analysis)

            logger.info(
                f"Synthesis complete. "
                f"{len(action_items)} action items identified. "
                f"Priority: {priority}"
            )

            return {
                "success": True,
                "final_summary": final_summary,
                "action_items": action_items,
                "priority": priority,
                "metadata": {
                    "statute_confidence": statute_confidence,
                    "policy_confidence": policy_confidence,
                    "action_item_count": len(action_items)
                }
            }

        except Exception as e:
            logger.error(f"Synthesis failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "final_summary": "",
                "action_items": []
            }

    def _synthesize(
        self,
        question: str,
        topic: str,
        statute_analysis: str,
        policy_analysis: str,
        statute_confidence: str,
        policy_confidence: str
    ) -> str:
        """
        Generate final compliance summary.

        Creates executive-friendly synthesis with:
        - Bottom line (1-2 sentences)
        - Statutory basis
        - Policy guidance
        - Action items
        - Open questions
        """

        system_message = """You are a policy compliance consultant creating briefings for county behavioral health leadership.

Your task is to synthesize legal statute analysis and policy guidance into a clear, actionable compliance summary.

**Key Instructions:**
- Use plain language - avoid legal jargon
- Be directive: Tell counties what to DO, not just what exists
- Prioritize actionable steps over background information
- Flag conflicts between statutes and policy guidance
- Maximum 300 words total
- Use markdown formatting with headers

**Output Format:**

## Compliance Summary

### Bottom Line
[1-2 sentence direct answer to the question - what must the county do?]

### Statutory Basis
[Which W&I Code sections require this? What specific mandates do they impose?]
[If no clear statutory requirement, state: "No specific statutory requirement identified."]

### Policy Guidance
[What does the DHCS Policy Manual say? Are there specific implementation steps?]
[Distinguish between "must" (required) and "should" (recommended)]

### Action Items for County
1. [Specific, actionable step 1 with timeline if applicable]
2. [Specific, actionable step 2]
3. [Specific, actionable step 3]
[Minimum 2, maximum 5 action items]

### Open Questions / Ambiguities
[Any areas of uncertainty, conflicts between statute and policy, or need for DHCS clarification]
[If none, state: "No significant ambiguities identified."]

**Example:**

Question: Must counties use the same provider standards for BHSA and Medi-Cal programs?

## Compliance Summary

### Bottom Line
Starting FY 2027-2028, DHCS strongly encourages but does not mandate that counties apply identical provider qualification standards to both BHSA-funded and Medi-Cal providers.

### Statutory Basis
W&I Code § 5899 requires BHSA providers to be "qualified" but does not define qualification standards. W&I Code § 14680 establishes Medi-Cal provider standards but does not explicitly extend them to BHSA programs. No statutory mandate for alignment exists.

### Policy Guidance
Policy Manual Section 3.4.2 states counties "should consider" aligning BHSA and Medi-Cal provider standards to reduce administrative burden and improve quality consistency. Specific areas to align include: (1) license verification processes, (2) cultural competency training requirements, and (3) nondiscrimination compliance documentation.

### Action Items for County
1. Review current BHSA provider qualification policies and compare with Medi-Cal standards (by March 2027)
2. Identify gaps and assess feasibility of alignment, including provider impact analysis
3. If pursuing alignment, develop timeline for policy updates and communicate changes to contracted providers (by April 2027)
4. Document decision and rationale in County Portal regardless of approach chosen

### Open Questions / Ambiguities
- Does DHCS plan to mandate alignment in future policy years?
- What happens if a BHSA provider cannot meet Medi-Cal standards - can they continue BHSA services only?

---

**Your Task:**
Synthesize the statute and policy analyses below into this format."""

        human_message = """**Question for County Compliance:**
{question}

**Topic Context:**
{topic}

**Statute Analysis:**
{statute_analysis}

**Policy Analysis:**
{policy_analysis}

**Confidence Levels:**
- Statute Analysis Confidence: {statute_confidence}
- Policy Analysis Confidence: {policy_confidence}

**Your Compliance Summary:**"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message)
        ])

        chain = prompt | self.llm

        response = chain.invoke({
            "question": question,
            "topic": topic,
            "statute_analysis": statute_analysis,
            "policy_analysis": policy_analysis,
            "statute_confidence": statute_confidence,
            "policy_confidence": policy_confidence
        })

        return response.content

    def _extract_action_items(self, final_summary: str) -> List[str]:
        """Extract action items from summary."""
        import re

        # Find text under "### Action Items for County" section
        match = re.search(
            r'### Action Items for County\s*\n(.*?)(?=###|\Z)',
            final_summary,
            re.DOTALL
        )

        if not match:
            return []

        action_text = match.group(1)

        # Extract numbered items
        items = re.findall(r'^\d+\.\s*(.+)$', action_text, re.MULTILINE)

        return [item.strip() for item in items if item.strip()]

    def _determine_priority(
        self,
        statute_analysis: str,
        policy_analysis: str
    ) -> str:
        """
        Determine priority level based on analysis content.

        High: Statutory mandates present, clear requirements
        Medium: Policy guidance present, recommended practices
        Low: No clear mandates, informational only
        """
        # Check for high-priority indicators
        high_priority_terms = [
            "must", "shall", "required", "mandatory",
            "statutory requirement", "W&I Code §"
        ]

        medium_priority_terms = [
            "should", "encouraged", "recommended",
            "best practice", "policy guidance"
        ]

        statute_lower = statute_analysis.lower()
        policy_lower = policy_analysis.lower()

        combined_text = statute_lower + " " + policy_lower

        # Count high-priority terms
        high_count = sum(
            combined_text.count(term.lower())
            for term in high_priority_terms
        )

        # Count medium-priority terms
        medium_count = sum(
            combined_text.count(term.lower())
            for term in medium_priority_terms
        )

        if high_count >= 3:
            return "High"
        elif medium_count >= 3 or high_count >= 1:
            return "Medium"
        else:
            return "Low"
