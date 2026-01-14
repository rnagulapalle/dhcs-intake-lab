"""
Retrieval Agent for Policy Curation
Handles document retrieval with hybrid search (semantic + keyword) and reranking
"""
import logging
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate

from agents.core.base_agent import BaseAgent
from agents.core.config import settings
from agents.knowledge.knowledge_base import DHCSKnowledgeBase

logger = logging.getLogger(__name__)


class RetrievalAgent(BaseAgent):
    """
    Specialized agent for retrieving policy documents and statutes.
    Uses hybrid search strategy and query enhancement for better retrieval quality.

    Improvements over prototype:
    - Query enhancement (extract key terms from verbose questions)
    - Metadata-based filtering (exclude TOC, filter by category)
    - Configurable top-k retrieval
    - Detailed logging of retrieval scores
    """

    def __init__(self):
        super().__init__(
            name="RetrievalAgent",
            role="Document Retrieval Specialist",
            goal="Retrieve most relevant policy documents and statutes for compliance questions",
            temperature=0.3  # Moderate temperature for query enhancement
        )

        # Initialize knowledge base
        self.kb = DHCSKnowledgeBase(persist_directory=settings.chroma_persist_dir)

        # W&I Code statute catalog (from prototype analysis)
        self.statute_catalog = [
            "W&I Code § 5899",
            "W&I Code § 14184",
            "W&I Code § 5892",
            "W&I Code § 5891",
            "W&I Code § 5830",
            "W&I Code § 14018",
            "W&I Code § 5840",
            "W&I Code § 8255",
            "W&I Code § 5963",
            "W&I Code § 8256",
            "W&I Code § 5604",
            "W&I Code § 14124",
            "W&I Code § 14197",
            "W&I Code § 5600",
            "W&I Code § 5835",
            "W&I Code § 5964",
            "W&I Code § 5350",
            "W&I Code § 5887"
        ]

        logger.info(f"{self.name} initialized with {len(self.statute_catalog)} statutes in catalog")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute retrieval for a policy question.

        Args:
            input_data: {
                "question": str,      # Full IP Question text
                "topic": str,         # Section + Sub-Section + Category
                "sub_section": str,   # IP Sub-Section
                "category": str,      # topic_name
                "top_k": int          # Number of results (default: 10)
            }

        Returns:
            {
                "success": bool,
                "statute_chunks": List[Dict],  # Retrieved statute documents
                "policy_chunks": List[Dict],   # Retrieved policy documents
                "retrieval_metadata": Dict     # Scores, query info, etc.
            }
        """
        try:
            question = input_data["question"]
            topic = input_data["topic"]
            top_k = input_data.get("top_k", 10)
            similarity_threshold = input_data.get("similarity_threshold", 0.5)  # POC compatibility

            logger.info(f"Retrieving documents for topic: {topic}")

            # Step 1: Enhance query (extract key terms)
            enhanced_statute_query = self._enhance_statute_query(question, topic)
            enhanced_policy_query = self._enhance_policy_query(question, topic)

            logger.info(f"Enhanced statute query: {enhanced_statute_query[:100]}...")
            logger.info(f"Enhanced policy query: {enhanced_policy_query[:100]}...")

            # Step 2: Retrieve statutes (filtered by metadata + similarity threshold)
            statute_chunks = self._retrieve_statutes(
                enhanced_statute_query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            # Step 3: Retrieve policies (excluding TOC + similarity threshold)
            policy_chunks = self._retrieve_policies(
                enhanced_policy_query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            logger.info(
                f"Retrieved {len(statute_chunks)} statute chunks, "
                f"{len(policy_chunks)} policy chunks"
            )

            return {
                "success": True,
                "statute_chunks": statute_chunks,
                "policy_chunks": policy_chunks,
                "retrieval_metadata": {
                    "statute_query": enhanced_statute_query,
                    "policy_query": enhanced_policy_query,
                    "statute_count": len(statute_chunks),
                    "policy_count": len(policy_chunks),
                    "statute_avg_score": self._avg_score(statute_chunks),
                    "policy_avg_score": self._avg_score(policy_chunks)
                }
            }

        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "statute_chunks": [],
                "policy_chunks": []
            }

    def _enhance_statute_query(self, question: str, topic: str) -> str:
        """
        Enhance statute query by extracting key legal terms.
        Fixes prototype issue: don't include entire statute list in query.
        """
        # Use LLM to extract key terms for statute search
        system_message = """You are a legal query optimizer.
Extract 3-5 key terms or phrases from the policy question that would help find relevant W&I Code statutes.

Focus on:
- Legal concepts (e.g., "documentation requirements", "staffing ratios")
- Service types (e.g., "crisis intervention", "housing interventions")
- Populations or contexts (e.g., "Medi-Cal", "BHSA-funded")

Return ONLY the key terms, comma-separated, no explanation."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "Topic: {topic}\n\nQuestion: {question}\n\nKey terms:")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"topic": topic, "question": question[:500]})

        key_terms = response.content.strip()

        # Construct enhanced query
        enhanced_query = f"{topic}: {key_terms}"

        return enhanced_query

    def _enhance_policy_query(self, question: str, topic: str) -> str:
        """
        Enhance policy query by extracting key policy concepts.
        """
        # Use LLM to extract key policy concepts
        system_message = """You are a policy query optimizer.
Extract 3-5 key concepts from the policy question that would help find relevant DHCS policy manual sections.

Focus on:
- Policy requirements (e.g., "workforce requirements", "provider standards")
- Implementation topics (e.g., "quality metrics", "language access")
- Compliance areas (e.g., "eligibility criteria", "reporting standards")

Return ONLY the key concepts, comma-separated, no explanation."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "Topic: {topic}\n\nQuestion: {question}\n\nKey concepts:")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"topic": topic, "question": question[:500]})

        key_concepts = response.content.strip()

        # Construct enhanced query
        enhanced_query = f"{topic}: {key_concepts}"

        return enhanced_query

    def _retrieve_statutes(self, query: str, top_k: int = 10, similarity_threshold: float = 0.5) -> List[Dict]:
        """
        Retrieve statute documents with metadata filtering and similarity threshold.

        Filters to statute category if metadata exists.
        Applies POC-compatible similarity threshold filtering.
        """
        try:
            # Generate embedding using knowledge base's OpenAI embeddings
            query_embedding = self.kb.embeddings.embed_query(query)

            # Search with metadata filter for statutes
            results = self.kb.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2,  # Get extra candidates for threshold filtering
                where={"category": "statute"}  # Filter by category
            )

            formatted = self._format_retrieval_results(results)

            # Apply similarity threshold filter (POC compatibility)
            filtered = [c for c in formatted if c.get("similarity_score", 0.0) >= similarity_threshold]

            return filtered[:top_k]

        except Exception as e:
            # If metadata filtering fails (e.g., no category field), fall back to regular search
            logger.warning(f"Metadata filter failed, falling back to regular search: {e}")
            return self._fallback_search(query, top_k, similarity_threshold)

    def _retrieve_policies(self, query: str, top_k: int = 10, similarity_threshold: float = 0.5) -> List[Dict]:
        """
        Retrieve policy documents, excluding Table of Contents.
        Applies POC-compatible similarity threshold filtering.

        Fixes prototype issue: TOC sections contaminate results.
        """
        try:
            # Generate embedding using knowledge base's OpenAI embeddings
            query_embedding = self.kb.embeddings.embed_query(query)

            # Search with metadata filters
            results = self.kb.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 3,  # Get extra candidates for TOC + threshold filtering
                where={
                    "$and": [
                        {"category": "policy"},
                        {"section": {"$ne": "Table of Contents"}}  # Exclude TOC
                    ]
                }
            )

            formatted = self._format_retrieval_results(results)

            # Apply similarity threshold filter (POC compatibility)
            filtered = [c for c in formatted if c.get("similarity_score", 0.0) >= similarity_threshold]

            # Return top_k after filtering
            return filtered[:top_k]

        except Exception as e:
            # Fallback without filtering
            logger.warning(f"Metadata filter failed, falling back to regular search: {e}")
            results = self._fallback_search(query, top_k * 2, similarity_threshold)

            # Manual TOC filtering
            filtered = [
                r for r in results
                if "Table of Contents" not in r.get("metadata", {}).get("section", "")
            ]

            return filtered[:top_k]

    def _fallback_search(self, query: str, top_k: int, similarity_threshold: float = 0.5) -> List[Dict]:
        """
        Fallback search without metadata filtering.
        Used when metadata doesn't exist yet (before data migration).
        Applies similarity threshold if provided.
        """
        results = self.kb.search(query, n_results=top_k * 2)

        # Apply similarity threshold filter
        filtered = [c for c in results if c.get("similarity_score", 0.0) >= similarity_threshold]

        return filtered[:top_k]

    def _format_retrieval_results(self, results: Dict) -> List[Dict]:
        """Format ChromaDB query results to standard structure."""
        formatted = []

        if not results or not results.get("documents"):
            return formatted

        documents = results["documents"][0] if results["documents"] else []
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc in enumerate(documents):
            formatted.append({
                "content": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
                "similarity_score": 1 - distances[i] if i < len(distances) else None  # Convert distance to similarity
            })

        return formatted

    def _avg_score(self, chunks: List[Dict]) -> float:
        """Calculate average similarity score."""
        if not chunks:
            return 0.0

        scores = [c.get("similarity_score", 0.0) for c in chunks if c.get("similarity_score")]

        if not scores:
            return 0.0

        return sum(scores) / len(scores)
