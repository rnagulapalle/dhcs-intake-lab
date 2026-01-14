"""
Policy Analyst Agent for Policy Curation
Specialized in interpreting DHCS behavioral health policy requirements
"""
import logging
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate

from agents.core.base_agent import BaseAgent
from agents.core.config import settings

logger = logging.getLogger(__name__)


class PolicyAnalystAgent(BaseAgent):
    """
    Specialized agent for DHCS policy interpretation and summarization.

    Uses:
    - Low temperature (0.2) for consistent policy interpretation
    - Structured markdown output
    - Distinction between requirements ("must") vs recommendations ("should")

    Fixes prototype issues:
    - No typos ("Summary" not "Saummary")
    - Clear structured output format
    - Role-based expertise
    - Markdown formatting with headers
    """

    def __init__(self):
        super().__init__(
            name="PolicyAnalystAgent",
            role="DHCS Behavioral Health Policy Analyst",
            goal="Interpret DHCS policy guidance and extract actionable compliance requirements",
            temperature=0.2  # Low for consistent policy interpretation
        )

        logger.info(f"{self.name} initialized for policy analysis")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze DHCS policy documents for compliance guidance.

        Args:
            input_data: {
                "question": str,          # IP Question
                "topic": str,             # Section + Sub-Section + Category
                "policy_chunks": List[Dict]  # Retrieved policy documents
            }

        Returns:
            {
                "success": bool,
                "policy_analysis": str,       # Structured markdown analysis
                "key_requirements": List[str],  # Extracted mandatory requirements
                "recommendations": List[str],   # Extracted best practices
                "confidence": str             # High/Medium/Low
            }
        """
        try:
            question = input_data["question"]
            topic = input_data["topic"]
            policy_chunks = input_data["policy_chunks"]

            logger.info(f"Analyzing {len(policy_chunks)} policy chunks")

            # Format policy context
            policy_context = self._format_policy_context(policy_chunks)

            # Generate analysis
            analysis = self._analyze_policy(
                question=question,
                topic=topic,
                policy_context=policy_context
            )

            # Extract structured components
            key_requirements = self._extract_requirements(analysis)
            recommendations = self._extract_recommendations(analysis)

            # Assess confidence
            confidence = self._assess_confidence(policy_chunks, analysis)

            logger.info(
                f"Policy analysis complete. "
                f"Found {len(key_requirements)} requirements, "
                f"{len(recommendations)} recommendations. "
                f"Confidence: {confidence}"
            )

            return {
                "success": True,
                "policy_analysis": analysis,
                "key_requirements": key_requirements,
                "recommendations": recommendations,
                "confidence": confidence,
                "metadata": {
                    "chunks_analyzed": len(policy_chunks),
                    "requirements_found": len(key_requirements),
                    "recommendations_found": len(recommendations)
                }
            }

        except Exception as e:
            logger.error(f"Policy analysis failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "policy_analysis": "",
                "key_requirements": [],
                "recommendations": []
            }

    def _format_policy_context(self, policy_chunks: List[Dict]) -> str:
        """Format retrieved policy chunks for LLM analysis with POC-style chunk IDs."""
        if not policy_chunks:
            return "No policy documents retrieved."

        formatted_chunks = []

        for i, chunk in enumerate(policy_chunks[:5], 1):  # Top 5 most relevant
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            source = metadata.get("source", "DHCS Policy Manual")
            section = metadata.get("section", "Unknown Section")
            version = metadata.get("version", "")
            score = chunk.get("similarity_score", 0.0)

            # POC-compatible chunk ID: P1, P2, P3...
            chunk_id = f"P{i}"
            formatted = f"**[{chunk_id}] Policy Reference {i}** (Relevance: {score:.2f})\n"
            formatted += f"Source: {source}"
            if version:
                formatted += f" (Version {version})"
            formatted += f"\nSection: {section}\n"
            formatted += f"Content:\n{content}\n"

            formatted_chunks.append(formatted)

        return "\n---\n\n".join(formatted_chunks)

    def _analyze_policy(
        self,
        question: str,
        topic: str,
        policy_context: str
    ) -> str:
        """
        Generate policy analysis using structured prompt.

        Fixes prototype issues:
        - Correct spelling: "Summary" not "Saummary"
        - Clear markdown structure
        - Distinction between "must" and "should"
        """

        system_message = """You are a DHCS behavioral health policy analyst specializing in interpreting county compliance guidance.

Your task is to analyze DHCS Policy Manual sections and extract relevant compliance requirements and recommendations for counties.

**Key Instructions:**
- Distinguish between mandatory requirements ("must", "shall", "required") and recommendations ("should", "encouraged", "may")
- Include specific section references when available (e.g., "Policy Manual Section 4.2.1")
- Reference the source chunk IDs (e.g., [P1], [P2]) for traceability
- Focus on actionable guidance that counties can implement
- Note any timelines or effective dates
- Flag any ambiguities or areas needing DHCS clarification
- Maximum 400 words

**Output Format (Markdown):**

## Policy Context

### Key Requirements
- [Bulleted list of MANDATORY requirements from policy manual]
- [Use "must" or "required" language]
- [Include section references]

### Recommended Practices
- [Bulleted list of RECOMMENDED/ENCOURAGED approaches]
- [Use "should" or "encouraged" language]

### Compliance Guidance
- [Specific steps counties should take to meet requirements]
- [Include any deadlines or timelines]

### Related Policy Sections
- [References to other relevant manual sections, if mentioned in retrieved docs]

### Ambiguities/Open Questions
- [Any unclear guidance or areas needing clarification]
- [Conflicts between policy sections]

**Example:**

Question: How should counties ensure cultural competency in workforce?

## Policy Context

### Key Requirements
- Counties must implement cultural competency training for all clinical staff ([P1], Policy Manual Section 4.2.1)
- Training must occur within 90 days of hire and annually thereafter ([P1])
- Training curriculum must be approved by DHCS ([P2])

### Recommended Practices
- Counties are encouraged to hire staff reflecting the demographic composition of the service area ([P1])
- Peer support specialists from diverse backgrounds should be integrated into care teams ([P3])
- Use of community advisory boards to guide culturally responsive service design ([P3])

### Compliance Guidance
- Document training completion in personnel files with dates and curriculum version ([P1])
- Maintain training curriculum and DHCS approval documentation on file ([P2])
- Track workforce demographics by language, ethnicity, and county and report annually ([P1])
- Effective Date: FY 2025-2026

### Related Policy Sections
- Section 4.1: Provider Network Adequacy
- Section 4.3: Language Access Services
- Section 2.5: Quality Metrics for Workforce Diversity

### Ambiguities/Open Questions
- None identified"""

        human_message = """**Question for County Compliance:**
{question}

**Topic Context:**
{topic}

**Retrieved Policy Documents:**
{policy_context}

**Your Analysis:**"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message)
        ])

        chain = prompt | self.llm

        response = chain.invoke({
            "question": question,
            "topic": topic,
            "policy_context": policy_context
        })

        return response.content

    def _extract_requirements(self, analysis: str) -> List[str]:
        """Extract mandatory requirements from analysis."""
        import re

        # Find text under "### Key Requirements" section
        match = re.search(
            r'### Key Requirements\s*\n(.*?)(?=###|\Z)',
            analysis,
            re.DOTALL
        )

        if not match:
            return []

        requirements_text = match.group(1)

        # Extract bullet points
        bullets = re.findall(r'^[-*]\s*(.+)$', requirements_text, re.MULTILINE)

        return [b.strip() for b in bullets if b.strip()]

    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract recommended practices from analysis."""
        import re

        # Find text under "### Recommended Practices" section
        match = re.search(
            r'### Recommended Practices\s*\n(.*?)(?=###|\Z)',
            analysis,
            re.DOTALL
        )

        if not match:
            return []

        recommendations_text = match.group(1)

        # Extract bullet points
        bullets = re.findall(r'^[-*]\s*(.+)$', recommendations_text, re.MULTILINE)

        return [b.strip() for b in bullets if b.strip()]

    def _assess_confidence(
        self,
        policy_chunks: List[Dict],
        analysis: str
    ) -> str:
        """
        Assess confidence in the policy analysis.

        High: Multiple high-quality chunks, clear requirements identified
        Medium: Some chunks, some requirements found
        Low: Few chunks, ambiguous or no clear requirements
        """
        if not policy_chunks:
            return "Low"

        avg_score = sum(
            c.get("similarity_score", 0.0) for c in policy_chunks
        ) / len(policy_chunks)

        # Check if requirements were found
        has_requirements = "### Key Requirements" in analysis
        has_content = len(analysis) > 200

        if avg_score > 0.8 and has_requirements and has_content:
            return "High"
        elif avg_score > 0.6 and has_content:
            return "Medium"
        else:
            return "Low"
