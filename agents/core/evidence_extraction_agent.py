"""
Evidence Extraction Agent
Extracts verbatim requirement sentences from retrieved chunks for auditable grounding.
"""
import logging
import re
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


class EvidenceExtractionAgent:
    """
    Extracts verbatim requirement sentences from statute and policy chunks.

    Design Principle: Extract ONLY explicit requirements with exact quotes (no paraphrasing).
    Every extracted requirement must be defensible to auditors.

    Rules:
    - Extract verbatim quotes only (10-40 words)
    - Only sentences with must/shall/required/prohibited/mandated
    - NO interpretation or inference
    - Each requirement gets unique ID (REQ-S001, REQ-P001, etc.)
    """

    def __init__(self, gateway: Optional["ModelGateway"] = None):
        self._gateway = _get_gateway(gateway)
        logger.info("Evidence Extraction Agent initialized (temperature=0.0 for determinism)")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract verbatim requirement sentences from chunks.

        Args:
            input_data: {
                "question": str,
                "statute_chunks": List[Dict],  # From retrieval
                "policy_chunks": List[Dict]     # From retrieval
            }

        Returns:
            {
                "extracted_requirements": List[Dict],  # All verbatim extracts
                "extraction_metadata": Dict  # Stats
            }
        """
        question = input_data["question"]
        statute_chunks = input_data.get("statute_chunks", [])
        policy_chunks = input_data.get("policy_chunks", [])

        logger.info(f"Extracting evidence from {len(statute_chunks)} statute chunks, {len(policy_chunks)} policy chunks")

        # Extract from statutes
        statute_requirements = self._extract_from_chunks(
            question=question,
            chunks=statute_chunks,
            source_type="statute",
            prefix="S"
        )

        # Extract from policies
        policy_requirements = self._extract_from_chunks(
            question=question,
            chunks=policy_chunks,
            source_type="policy",
            prefix="P"
        )

        all_requirements = statute_requirements + policy_requirements

        metadata = {
            "total_chunks_processed": len(statute_chunks) + len(policy_chunks),
            "statute_chunks_processed": len(statute_chunks),
            "policy_chunks_processed": len(policy_chunks),
            "total_requirements_extracted": len(all_requirements),
            "statute_requirements_extracted": len(statute_requirements),
            "policy_requirements_extracted": len(policy_requirements),
            "extraction_timestamp": None  # Will be populated by orchestrator
        }

        logger.info(
            f"Extracted {len(all_requirements)} total requirements "
            f"({len(statute_requirements)} statute, {len(policy_requirements)} policy)"
        )

        return {
            "extracted_requirements": all_requirements,
            "extraction_metadata": metadata
        }

    def _extract_from_chunks(
        self,
        question: str,
        chunks: List[Dict],
        source_type: str,
        prefix: str
    ) -> List[Dict]:
        """
        Extract requirements from a list of chunks.

        Args:
            question: The compliance question
            chunks: List of retrieved chunks
            source_type: "statute" or "policy"
            prefix: "S" for statute, "P" for policy (for IDs)

        Returns:
            List of extracted requirements with unique IDs
        """
        if not chunks:
            logger.info(f"No {source_type} chunks to extract from")
            return []

        # Format chunks for extraction
        formatted_chunks = self._format_chunks_for_extraction(chunks, prefix)

        # Call LLM to extract requirements
        extracted = self._llm_extract_requirements(
            question=question,
            formatted_chunks=formatted_chunks,
            source_type=source_type
        )

        # Assign unique IDs
        requirements = []
        for idx, req in enumerate(extracted, start=1):
            requirement_id = f"REQ-{prefix}{idx:03d}"
            req["requirement_id"] = requirement_id
            req["source_type"] = source_type
            requirements.append(req)

        return requirements

    def _format_chunks_for_extraction(self, chunks: List[Dict], prefix: str) -> str:
        """Format chunks with chunk IDs for LLM extraction."""
        formatted = []

        for i, chunk in enumerate(chunks, start=1):
            chunk_id = f"{prefix}{i}"
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})

            # Extract document identifiers
            source = metadata.get("source", "Unknown")
            section = metadata.get("section", "")

            chunk_text = f"""
[Chunk {chunk_id}]
Document: {source}
Section: {section}
Content:
{content}
"""
            formatted.append(chunk_text.strip())

        return "\n\n".join(formatted)

    def _llm_extract_requirements(
        self,
        question: str,
        formatted_chunks: str,
        source_type: str
    ) -> List[Dict]:
        """
        Use LLM to extract verbatim requirement sentences.

        Returns list of dicts with: chunk_id, document_id, section_heading, exact_quote, confidence
        """
        system_prompt = f"""You are an evidence extraction specialist for a regulated compliance system.

Your task: Extract ONLY explicit requirement sentences from {source_type} documents.

CRITICAL RULES:
1. Extract VERBATIM quotes only (10-40 words) - NO paraphrasing
2. Only sentences containing: must, shall, required, required to, prohibited, mandated, obligation
3. Each quote must be self-contained (understandable without surrounding context)
4. If quote exceeds 40 words, excerpt the most important 10-40 word span
5. If no clear requirement exists in a chunk, extract NOTHING from that chunk
6. DO NOT interpret, infer, or add context

OUTPUT FORMAT (JSON array):
[
  {{
    "chunk_id": "S1",
    "document_id": "W&I Code § 5899",
    "section_heading": "Mental Health Services Act",
    "exact_quote": "Counties shall provide community-based services to adults with severe mental illness.",
    "extraction_confidence": "high"
  }}
]

Confidence levels:
- high: Clear requirement with explicit must/shall
- medium: Implicit requirement with "required to" or "obligations"
- low: Unclear or ambiguous requirement language

If NO requirements found in ANY chunk, return: []
"""

        human_prompt = f"""Question: {question}

Retrieved {source_type.title()} Documents:

{formatted_chunks}

Extract all explicit requirement sentences as JSON array. If none found, return [].
"""

        try:
            response = self._gateway.invoke_raw([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_prompt}
            ])

            content = response.content.strip()

            # Parse JSON from response
            import json

            # Try to find JSON array in response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                extracted = json.loads(json_match.group(0))
                logger.info(f"Extracted {len(extracted)} requirements from {source_type} chunks")
                return extracted
            else:
                logger.warning(f"No JSON array found in LLM response for {source_type}")
                return []

        except Exception as e:
            logger.error(f"Error extracting {source_type} requirements: {e}", exc_info=True)
            return []

    def _validate_extraction(self, requirement: Dict) -> bool:
        """
        Validate that extracted requirement meets quality standards.

        Returns True if valid, False otherwise.
        """
        # Check required fields
        required_fields = ["chunk_id", "document_id", "exact_quote", "extraction_confidence"]
        if not all(field in requirement for field in required_fields):
            return False

        # Check quote length (10-40 words)
        quote = requirement.get("exact_quote", "")
        word_count = len(quote.split())
        if word_count < 10 or word_count > 40:
            logger.warning(f"Quote length {word_count} words outside range 10-40: {quote[:50]}...")
            return False

        # Check for requirement keywords
        quote_lower = quote.lower()
        requirement_keywords = ["must", "shall", "required", "prohibited", "mandated", "obligation"]
        if not any(keyword in quote_lower for keyword in requirement_keywords):
            logger.warning(f"Quote missing requirement keywords: {quote[:50]}...")
            return False

        return True
