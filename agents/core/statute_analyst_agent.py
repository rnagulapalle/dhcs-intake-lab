"""
Statute Analyst Agent for Policy Curation
Specialized in analyzing California W&I Code statutes for compliance requirements
"""
import logging
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate

from agents.core.base_agent import BaseAgent
from agents.core.config import settings

logger = logging.getLogger(__name__)


class StatuteAnalystAgent(BaseAgent):
    """
    Specialized agent for legal analysis of W&I Code statutes.

    Uses:
    - Lower temperature (0.1) for consistent legal analysis
    - Structured output format with statute citations
    - Few-shot examples for better prompt following

    Fixes prototype issues:
    - No typos ("statutes" not "statuates")
    - Clear output format specification
    - Role-based prompting for legal expertise
    """

    def __init__(self):
        super().__init__(
            name="StatuteAnalystAgent",
            role="California Policy Compliance Legal Analyst",
            goal="Analyze W&I Code statutes to identify specific legal requirements and mandates",
            temperature=0.1  # Very low for consistent legal interpretation
        )

        logger.info(f"{self.name} initialized for legal statute analysis")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze statutes for relevance to compliance question.

        Args:
            input_data: {
                "question": str,          # IP Question
                "topic": str,             # Section + Sub-Section + Category
                "statute_chunks": List[Dict],  # Retrieved statute documents
                "statute_catalog": List[str]   # List of W&I Code sections to consider
            }

        Returns:
            {
                "success": bool,
                "statute_analysis": str,      # Structured analysis with citations
                "relevant_statutes": List[str],  # List of applicable statute citations
                "confidence": str             # High/Medium/Low confidence assessment
            }
        """
        try:
            question = input_data["question"]
            topic = input_data["topic"]
            statute_chunks = input_data["statute_chunks"]
            statute_catalog = input_data.get("statute_catalog", [])

            logger.info(f"Analyzing {len(statute_chunks)} statute chunks for relevance")

            # Prepare statute context
            statute_context = self._format_statute_context(statute_chunks)

            # Generate analysis using structured prompt
            analysis = self._analyze_statutes(
                question=question,
                topic=topic,
                statute_context=statute_context,
                statute_catalog=statute_catalog
            )

            # Extract relevant statute citations
            relevant_statutes = self._extract_statute_citations(analysis)

            # Assess confidence
            confidence = self._assess_confidence(statute_chunks, relevant_statutes)

            logger.info(
                f"Statute analysis complete. "
                f"Found {len(relevant_statutes)} relevant statutes. "
                f"Confidence: {confidence}"
            )

            return {
                "success": True,
                "statute_analysis": analysis,
                "relevant_statutes": relevant_statutes,
                "confidence": confidence,
                "metadata": {
                    "chunks_analyzed": len(statute_chunks),
                    "statutes_identified": len(relevant_statutes)
                }
            }

        except Exception as e:
            logger.error(f"Statute analysis failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "statute_analysis": "",
                "relevant_statutes": []
            }

    def _format_statute_context(self, statute_chunks: List[Dict]) -> str:
        """Format retrieved statute chunks for LLM analysis with POC-style chunk IDs."""
        if not statute_chunks:
            return "No statute documents retrieved."

        formatted_chunks = []

        for i, chunk in enumerate(statute_chunks[:5], 1):  # Top 5 most relevant
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            source = metadata.get("source", "Unknown Statute")
            score = chunk.get("similarity_score", 0.0)

            # POC-compatible chunk ID: S1, S2, S3...
            chunk_id = f"S{i}"
            formatted = f"**[{chunk_id}] Statute Reference {i}** (Relevance: {score:.2f})\n"
            formatted += f"Source: {source}\n"
            formatted += f"Content:\n{content}\n"

            formatted_chunks.append(formatted)

        return "\n---\n\n".join(formatted_chunks)

    def _analyze_statutes(
        self,
        question: str,
        topic: str,
        statute_context: str,
        statute_catalog: List[str]
    ) -> str:
        """
        Generate statute analysis using structured prompt with few-shot examples.

        Fixes prototype issues:
        - Correct spelling: "statutes" not "statuates"
        - Clear output format
        - Role-based expertise framing
        - Few-shot examples included
        """

        system_message = """You are a California policy compliance legal analyst specializing in Welfare and Institutions Code (W&I Code) interpretation.

Your task is to identify which statutes from the provided list are DIRECTLY relevant to answering a county compliance question, and explain the specific legal requirements they impose.

**Key Instructions:**
- A statute is relevant ONLY if it contains specific requirements, definitions, or mandates that address the question
- Focus on actionable legal obligations, not general context
- Cite statute sections precisely (e.g., "W&I Code § 5899, subdivision (b)")
- Reference the source chunk IDs (e.g., [S1], [S2]) for traceability
- Distinguish between mandatory ("shall", "must") and permissive ("may") language
- If no statutes are clearly relevant, explicitly state this

**Output Format:**

For each relevant statute:
1. **Statute Citation:** [e.g., W&I Code § 5600.5] (Source: [S1])
2. **Relevance:** [1-2 sentences explaining WHY it applies to this question]
3. **Key Requirement:** [Specific mandate or definition from the statute]

If no statutes are clearly relevant:
"**No directly applicable statutes found in the provided list.**"

**Examples:**

Example 1:
Question: What are the documentation requirements for client assessments?

**Relevant Statutes:**

1. **Statute Citation:** W&I Code § 5600.5 (Source: [S1])
   **Relevance:** This statute requires counties to maintain client records including assessment documentation for all behavioral health services recipients.
   **Key Requirement:** All assessments must be documented within 60 days of initial contact and must include mental health screening, substance use screening, and risk assessment.

2. **Statute Citation:** W&I Code § 14680 (Source: [S3])
   **Relevance:** Defines "assessment" for Medi-Cal behavioral health purposes, establishing the minimum content requirements.
   **Key Requirement:** Assessments must include diagnostic evaluation, functional assessment, and determination of medical necessity.

Example 2:
Question: What is the minimum staffing ratio for crisis intervention teams?

**No directly applicable statutes found in the provided list.** (Note: Title 9 CCR may contain staffing standards, but W&I Code statutes provided do not specify ratios.)"""

        human_message = """**Question for County Compliance:**
{question}

**Topic Context:**
{topic}

**Statute Catalog to Consider:**
{statute_catalog}

**Retrieved Statute Documents:**
{statute_context}

**Your Analysis:**"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", human_message)
        ])

        chain = prompt | self.llm

        response = chain.invoke({
            "question": question,
            "topic": topic,
            "statute_catalog": ", ".join(statute_catalog),
            "statute_context": statute_context
        })

        return response.content

    def _extract_statute_citations(self, analysis: str) -> List[str]:
        """Extract statute citations from analysis text."""
        import re

        # Pattern to match W&I Code citations
        pattern = r'W&I Code §\s*\d+'

        matches = re.findall(pattern, analysis)

        # Deduplicate and normalize
        unique_statutes = list(set([m.strip() for m in matches]))

        return sorted(unique_statutes)

    def _assess_confidence(
        self,
        statute_chunks: List[Dict],
        relevant_statutes: List[str]
    ) -> str:
        """
        Assess confidence in the statute analysis.

        High: Multiple chunks with high similarity, multiple statutes identified
        Medium: Some chunks retrieved, at least one statute identified
        Low: Few chunks, no clear statutes identified
        """
        if not statute_chunks:
            return "Low"

        avg_score = sum(
            c.get("similarity_score", 0.0) for c in statute_chunks
        ) / len(statute_chunks)

        if avg_score > 0.8 and len(relevant_statutes) >= 2:
            return "High"
        elif avg_score > 0.6 and len(relevant_statutes) >= 1:
            return "Medium"
        else:
            return "Low"
