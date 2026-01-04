"""
ChromaDB Knowledge Base for DHCS BHT policies and procedures
Implements RAG (Retrieval Augmented Generation) for agent knowledge
"""
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from agents.core.config import settings

logger = logging.getLogger(__name__)


class DHCSKnowledgeBase:
    """
    Knowledge base for DHCS behavioral health policies, procedures, and best practices
    Uses ChromaDB for vector storage and retrieval
    """

    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or settings.chroma_persist_dir

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="dhcs_bht_knowledge",
            metadata={"description": "DHCS Behavioral Health Treatment knowledge base"}
        )

        logger.info(f"Knowledge base initialized with {self.collection.count()} documents")

    def add_documents(self, documents: List[Dict[str, str]]):
        """
        Add documents to the knowledge base

        Args:
            documents: List of dicts with 'content', 'metadata', and 'id' keys
        """
        if not documents:
            logger.warning("No documents to add")
            return

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )

        chunks = []
        metadatas = []
        ids = []

        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            doc_id = doc.get("id", "")

            # Split text into chunks
            splits = text_splitter.split_text(content)

            for i, chunk in enumerate(splits):
                chunks.append(chunk)
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = i
                chunk_metadata["total_chunks"] = len(splits)
                metadatas.append(chunk_metadata)
                ids.append(f"{doc_id}_chunk_{i}")

        # Generate embeddings
        embeddings = self.embeddings.embed_documents(chunks)

        # Add to ChromaDB
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(f"Added {len(chunks)} chunks from {len(documents)} documents")

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the knowledge base

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            List of relevant documents with metadata
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)

        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        # Format results
        formatted_results = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None
                })

        logger.info(f"Found {len(formatted_results)} results for query: {query}")
        return formatted_results

    def get_context_for_query(self, query: str, max_tokens: int = 2000) -> str:
        """
        Get relevant context for a query, formatted for LLM consumption

        Args:
            query: User query
            max_tokens: Maximum tokens of context to return (approximate)

        Returns:
            Formatted context string
        """
        results = self.search(query, n_results=5)

        if not results:
            return "No relevant information found in knowledge base."

        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough approximation

        for result in results:
            content = result["content"]
            metadata = result["metadata"]

            # Format with metadata
            source = metadata.get("source", "Unknown")
            section = metadata.get("section", "")

            formatted = f"[Source: {source}"
            if section:
                formatted += f", Section: {section}"
            formatted += f"]\n{content}\n"

            if total_chars + len(formatted) > max_chars:
                break

            context_parts.append(formatted)
            total_chars += len(formatted)

        return "\n---\n\n".join(context_parts)

    def initialize_with_dhcs_policies(self):
        """Initialize knowledge base with DHCS BHT policies and procedures"""

        # Sample DHCS/BHT knowledge - In production, load from actual policy documents
        documents = [
            {
                "id": "988_protocol",
                "content": """
                988 Crisis Hotline Protocol

                The 988 Suicide and Crisis Lifeline is a national network providing 24/7 free and confidential
                support for people in distress, prevention and crisis resources.

                Risk Assessment:
                - Imminent Risk: Active suicidal ideation with plan and means. Requires immediate intervention,
                  possible 911 transfer or mobile crisis team dispatch.
                - High Risk: Suicidal ideation with plan but no immediate means. Requires urgent follow-up
                  within 24 hours, safety planning, and connection to services.
                - Moderate Risk: Suicidal ideation without plan. Provide crisis counseling, safety planning,
                  and referral to outpatient services.
                - Low Risk: General distress without suicidal ideation. Provide support, resources, and referrals.

                Response Times:
                - Imminent risk calls should be answered within 30 seconds
                - All calls should be answered within 60 seconds
                - Target average call duration: 20-30 minutes for crisis counseling
                """,
                "metadata": {
                    "source": "DHCS 988 Operations Manual",
                    "section": "Crisis Response Protocol",
                    "version": "2024.1",
                    "category": "protocol"
                }
            },
            {
                "id": "mobile_crisis_team",
                "content": """
                Mobile Crisis Response Team Guidelines

                Mobile crisis teams provide in-person crisis intervention and assessment in community settings,
                homes, or other locations outside of emergency departments.

                Dispatch Criteria:
                - High or imminent risk level with location information
                - Request for in-person assessment
                - Cases where transportation to services is needed
                - De-escalation requiring in-person presence

                Response Requirements:
                - Teams must include licensed mental health clinician
                - Response time target: Within 60 minutes in urban areas, 90 minutes in rural
                - Teams should have capacity for voluntary transport
                - Law enforcement should only be involved when safety requires it

                Documentation:
                - Complete risk assessment
                - Disposition and safety plan
                - Follow-up coordination
                """,
                "metadata": {
                    "source": "DHCS Mobile Crisis Standards",
                    "section": "Dispatch and Response",
                    "version": "2024.1",
                    "category": "protocol"
                }
            },
            {
                "id": "language_access",
                "content": """
                Language Access Requirements

                California law requires meaningful access to services for Limited English Proficient (LEP) individuals.

                Requirements:
                - Interpreter services must be available in all threshold languages (15+ languages in California)
                - Interpreters must be qualified and trained in mental health terminology
                - Wait times for LEP callers should not exceed wait times for English speakers
                - Cultural competency training required for all crisis counselors

                Threshold Languages in California (by county):
                - Statewide: Spanish, Chinese (Mandarin/Cantonese), Vietnamese, Korean, Tagalog, Armenian
                - Additional languages vary by county demographics

                Quality Standards:
                - Use qualified interpreters, not family members
                - Document language needs in crisis record
                - Track and report language access metrics
                """,
                "metadata": {
                    "source": "DHCS Language Access Policy",
                    "section": "LEP Services",
                    "version": "2024.1",
                    "category": "equity"
                }
            },
            {
                "id": "data_privacy",
                "content": """
                Data Privacy and HIPAA Compliance

                All crisis intake data is Protected Health Information (PHI) under HIPAA.

                Requirements:
                - Minimum necessary standard: Only access data needed for job function
                - Use de-identified data for analytics and reporting when possible
                - Audit logs for all PHI access
                - Encryption in transit and at rest

                Permissible Uses:
                - Treatment, payment, and healthcare operations (TPO)
                - Public health reporting (aggregate, de-identified)
                - Quality improvement and analytics (de-identified)
                - Emergency circumstances for health and safety

                Synthetic Data:
                - For testing, training, and demos, use only synthetic data
                - Synthetic data should be realistic but completely fabricated
                - No real PHI should ever be used in non-production environments
                """,
                "metadata": {
                    "source": "DHCS Privacy and Security Policy",
                    "section": "HIPAA Compliance",
                    "version": "2024.1",
                    "category": "compliance"
                }
            },
            {
                "id": "quality_metrics",
                "content": """
                Crisis System Quality Metrics

                Key Performance Indicators (KPIs) for crisis intake systems:

                Access Metrics:
                - Call answer rate: Target >95%
                - Average speed of answer: Target <60 seconds
                - Abandonment rate: Target <5%
                - Language access: LEP wait times equal to English

                Clinical Metrics:
                - Risk assessment completion rate: 100%
                - Safety plan completion for moderate+ risk: 100%
                - Follow-up contact attempted within 24 hours for high-risk: 100%
                - Linkage to continuing care: >80%

                Equity Metrics:
                - Service access by language, county, and demographic group
                - Outcome equity across populations
                - Cultural competency metrics

                Operational Metrics:
                - Mobile crisis response time
                - ED diversion rate
                - Staff utilization and capacity
                """,
                "metadata": {
                    "source": "DHCS Quality Standards",
                    "section": "Performance Metrics",
                    "version": "2024.1",
                    "category": "quality"
                }
            },
            {
                "id": "staffing_guidelines",
                "content": """
                Crisis System Staffing Guidelines

                Staffing Requirements:
                - Licensed clinicians (LCSW, LMFT, PhD/PsyD, Psychiatric NP) for supervision
                - Crisis counselors with minimum Associate's degree in related field
                - Peer support specialists (certified)
                - Language interpreters for threshold languages

                Staffing Ratios:
                - Supervisor to counselor ratio: 1:8-10
                - Target: 1 counselor per 4-6 simultaneous calls
                - After-hours coverage must maintain same standards

                Training Requirements:
                - 40 hours initial crisis intervention training
                - 20 hours annual continuing education
                - Suicide risk assessment certification
                - Cultural competency and trauma-informed care training
                - De-escalation techniques

                Surge Capacity:
                - On-call staff roster for surge events
                - Cross-county mutual aid agreements
                - Backup call center capacity
                """,
                "metadata": {
                    "source": "DHCS Workforce Standards",
                    "section": "Staffing Requirements",
                    "version": "2024.1",
                    "category": "operations"
                }
            }
        ]

        logger.info("Initializing knowledge base with DHCS BHT policies")
        self.add_documents(documents)
        logger.info("Knowledge base initialization complete")

    def reset(self):
        """Reset the knowledge base (delete all documents)"""
        self.client.delete_collection("dhcs_bht_knowledge")
        self.collection = self.client.get_or_create_collection(
            name="dhcs_bht_knowledge",
            metadata={"description": "DHCS Behavioral Health Treatment knowledge base"}
        )
        logger.info("Knowledge base reset")
