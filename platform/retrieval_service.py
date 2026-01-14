"""
BHT Platform Retrieval Service

Phase 2: Centralized retrieval with canonical citations and instrumentation.
Provides a unified interface for document retrieval with:
- Canonical Citation schema for standardized references
- Audit logging with trace propagation
- Latency tracking and instrumentation
- Optional caching (feature flagged)

Default behavior is identical to Phase 0/1 (no behavior change).
All new features are additive and behind feature flags.
"""
import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from platform.audit_context import AuditContext
from platform.config import PlatformConfig, get_platform_config
from platform.errors import RetrievalError

logger = logging.getLogger(__name__)


# =============================================================================
# Canonical Citation Schema
# =============================================================================

@dataclass
class Citation:
    """
    Canonical citation schema for retrieval results.

    This schema provides a stable contract for all retrieval results,
    regardless of underlying vector store or retrieval method.

    Fields:
        source_id: Unique identifier for the source document
        source_name: Human-readable name of the source (e.g., "DHCS Policy Manual")
        doc_uri: Document URI or path for reference
        chunk_id: Unique identifier for this specific chunk
        snippet: The actual text content retrieved
        score: Similarity/relevance score (0.0-1.0, higher is better)
        metadata: Additional source-specific metadata

    Example:
        {
            "source_id": "dhcs_policy_manual_v2024",
            "source_name": "DHCS Behavioral Health Policy Manual",
            "doc_uri": "/docs/policy/bht_manual_2024.pdf",
            "chunk_id": "988_protocol_chunk_3",
            "snippet": "Mobile crisis teams must respond within 60 minutes...",
            "score": 0.89,
            "metadata": {
                "section": "Crisis Response Protocol",
                "category": "protocol",
                "version": "2024.1"
            }
        }
    """
    source_id: str
    source_name: str
    doc_uri: str
    chunk_id: str
    snippet: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert citation to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_retrieval_result(cls, result: Dict[str, Any]) -> "Citation":
        """
        Create a Citation from a raw retrieval result.

        This normalizes the various formats returned by DHCSKnowledgeBase
        into the canonical Citation schema.

        Args:
            result: Raw result dict with 'content', 'metadata', 'distance'/'similarity_score'

        Returns:
            Citation instance
        """
        metadata = result.get("metadata", {})

        # Extract source information from metadata
        source = metadata.get("source", "Unknown")
        source_id = metadata.get("id", metadata.get("source_id", source.lower().replace(" ", "_")))
        doc_uri = metadata.get("doc_uri", metadata.get("file_path", f"/docs/{source_id}"))
        chunk_index = metadata.get("chunk_index", 0)
        chunk_id = metadata.get("chunk_id", f"{source_id}_chunk_{chunk_index}")

        # Calculate score: convert distance to similarity if needed
        if "similarity_score" in result and result["similarity_score"] is not None:
            score = result["similarity_score"]
        elif "distance" in result and result["distance"] is not None:
            # ChromaDB returns distance (lower is better), convert to similarity
            score = 1.0 - min(result["distance"], 1.0)
        else:
            score = 0.0

        # Extract snippet content
        snippet = result.get("content", "")

        return cls(
            source_id=source_id,
            source_name=source,
            doc_uri=doc_uri,
            chunk_id=chunk_id,
            snippet=snippet,
            score=score,
            metadata=metadata,
        )


# =============================================================================
# Retrieval Result
# =============================================================================

@dataclass
class RetrievalResult:
    """
    Result of a retrieval operation.

    Wraps the search results with metadata for audit and debugging.
    Includes both raw results (backward compatibility) and citations (Phase 2).
    """
    results: List[Dict[str, Any]]  # Raw results for backward compatibility
    citations: List["Citation"]  # Canonical citations (Phase 2)
    query: str
    n_results: int
    latency_ms: float
    trace_id: str
    cache_hit: bool = False
    success: bool = True
    error: Optional[str] = None
    strategy: str = "semantic"  # semantic, keyword, hybrid

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "results": self.results,
            "citations": [c.to_dict() for c in self.citations],
            "query": self.query,
            "n_results": self.n_results,
            "latency_ms": self.latency_ms,
            "trace_id": self.trace_id,
            "cache_hit": self.cache_hit,
            "success": self.success,
            "error": self.error,
            "strategy": self.strategy,
        }


# =============================================================================
# Retrieval Service
# =============================================================================

class RetrievalService:
    """
    Phase 2 Retrieval Service with canonical citations.

    Wraps existing DHCSKnowledgeBase/RetrievalAgent without changing behavior.
    Adds canonical citation schema and improved instrumentation.

    Feature Flags:
    - BHT_USE_CENTRALIZED_RETRIEVAL: Use centralized service (default: true)
    - BHT_RETRIEVAL_CACHE_ENABLED: Enable result caching (default: false)

    Usage:
        # Initialize with existing knowledge base
        kb = DHCSKnowledgeBase()
        retrieval_service = RetrievalService(knowledge_base=kb)

        # Search with citations
        result = retrieval_service.search("mobile crisis team response time", n_results=5)

        # Access canonical citations
        for citation in result.citations:
            print(f"{citation.source_name}: {citation.snippet[:100]}... (score: {citation.score:.2f})")

        # Or access raw results (backward compatibility)
        for doc in result.results:
            print(doc["content"])
    """

    def __init__(
        self,
        knowledge_base: Optional[Any] = None,  # DHCSKnowledgeBase
        config: Optional[PlatformConfig] = None,
    ):
        """
        Initialize the retrieval service.

        Args:
            knowledge_base: Existing DHCSKnowledgeBase instance (lazy-loads if not provided)
            config: Platform configuration
        """
        self.config = config or get_platform_config()
        self._knowledge_base = knowledge_base
        self._initialized = knowledge_base is not None

        # Simple in-memory cache (disabled by default)
        self._cache: Dict[str, RetrievalResult] = {}
        self._cache_enabled = False  # Phase 2: cache disabled by default

        logger.debug("RetrievalService initialized (Phase 2)")

    def _get_knowledge_base(self) -> Any:
        """
        Lazy-load knowledge base if not provided.

        Returns:
            DHCSKnowledgeBase instance
        """
        if self._knowledge_base is None:
            from agents.knowledge.knowledge_base import DHCSKnowledgeBase
            from agents.core.config import settings
            self._knowledge_base = DHCSKnowledgeBase(
                persist_directory=settings.chroma_persist_dir
            )
            self._initialized = True
            logger.debug("Lazy-loaded DHCSKnowledgeBase")

        return self._knowledge_base

    def search(
        self,
        query: str,
        n_results: int = 5,
        similarity_threshold: Optional[float] = None,
        category_filter: Optional[str] = None,
        audit_context: Optional[AuditContext] = None,
    ) -> RetrievalResult:
        """
        Search the knowledge base with audit logging and canonical citations.

        Args:
            query: Search query
            n_results: Number of results to return
            similarity_threshold: Optional minimum similarity score (0.0-1.0)
            category_filter: Optional category filter (e.g., "statute", "policy")
            audit_context: Audit context for tracing (uses current if not provided)

        Returns:
            RetrievalResult with citations and metadata
        """
        audit = audit_context or AuditContext.current()
        kb = self._get_knowledge_base()

        # Check cache if enabled
        cache_key = f"{query}:{n_results}:{similarity_threshold}:{category_filter}"
        if self._cache_enabled and cache_key in self._cache:
            cached = self._cache[cache_key]
            logger.debug(f"Cache hit for query: {query[:50]}...")
            # Update cache_hit flag and return
            return RetrievalResult(
                results=cached.results,
                citations=cached.citations,
                query=cached.query,
                n_results=cached.n_results,
                latency_ms=0.0,  # Instant from cache
                trace_id=audit.trace_id,
                cache_hit=True,
                success=True,
            )

        start_time = time.time()
        error_msg = None
        results: List[Dict[str, Any]] = []
        citations: List[Citation] = []

        try:
            # Call underlying knowledge base with optional filtering
            if category_filter:
                results = self._search_with_filter(query, n_results, category_filter)
            else:
                results = kb.search(query, n_results=n_results)

            # Apply similarity threshold if specified
            if similarity_threshold is not None:
                results = [
                    r for r in results
                    if self._get_score(r) >= similarity_threshold
                ]

            # Convert to canonical citations
            citations = [Citation.from_retrieval_result(r) for r in results]
            success = True

        except Exception as e:
            error_msg = str(e)
            success = False
            logger.error(f"Retrieval failed: {e}", exc_info=True)
            raise RetrievalError(f"Retrieval failed: {e}")

        finally:
            latency_ms = (time.time() - start_time) * 1000

            # Log to audit context
            audit.log_retrieval(
                query_length=len(query),
                n_results=len(results),
                latency_ms=latency_ms,
                strategy="semantic",
                cache_hit=False,
                success=success,
                error=error_msg,
            )

        result = RetrievalResult(
            results=results,
            citations=citations,
            query=query,
            n_results=len(results),
            latency_ms=latency_ms,
            trace_id=audit.trace_id,
            cache_hit=False,
            success=success,
            error=error_msg,
            strategy="semantic",
        )

        # Store in cache if enabled
        if self._cache_enabled and success:
            self._cache[cache_key] = result

        return result

    def search_statutes(
        self,
        query: str,
        n_results: int = 10,
        similarity_threshold: float = 0.5,
        audit_context: Optional[AuditContext] = None,
    ) -> RetrievalResult:
        """
        Search for statute documents with metadata filtering.

        Convenience method that wraps search() with statute-specific settings.

        Args:
            query: Search query
            n_results: Number of results to return
            similarity_threshold: Minimum similarity score
            audit_context: Audit context for tracing

        Returns:
            RetrievalResult filtered to statutes only
        """
        return self.search(
            query=query,
            n_results=n_results,
            similarity_threshold=similarity_threshold,
            category_filter="statute",
            audit_context=audit_context,
        )

    def search_policies(
        self,
        query: str,
        n_results: int = 10,
        similarity_threshold: float = 0.5,
        exclude_toc: bool = True,
        audit_context: Optional[AuditContext] = None,
    ) -> RetrievalResult:
        """
        Search for policy documents, optionally excluding Table of Contents.

        Convenience method that wraps search() with policy-specific settings.

        Args:
            query: Search query
            n_results: Number of results to return
            similarity_threshold: Minimum similarity score
            exclude_toc: Whether to exclude Table of Contents sections
            audit_context: Audit context for tracing

        Returns:
            RetrievalResult filtered to policies only
        """
        result = self.search(
            query=query,
            n_results=n_results * 2 if exclude_toc else n_results,  # Get extra for filtering
            similarity_threshold=similarity_threshold,
            category_filter="policy",
            audit_context=audit_context,
        )

        if exclude_toc:
            # Filter out TOC entries
            filtered_results = [
                r for r in result.results
                if "Table of Contents" not in r.get("metadata", {}).get("section", "")
            ]
            filtered_citations = [
                c for c in result.citations
                if "Table of Contents" not in c.metadata.get("section", "")
            ]

            # Return limited results
            return RetrievalResult(
                results=filtered_results[:n_results],
                citations=filtered_citations[:n_results],
                query=result.query,
                n_results=min(len(filtered_results), n_results),
                latency_ms=result.latency_ms,
                trace_id=result.trace_id,
                cache_hit=result.cache_hit,
                success=result.success,
                strategy=result.strategy,
            )

        return result

    def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 2000,
        audit_context: Optional[AuditContext] = None,
    ) -> str:
        """
        Get formatted context for a query with audit logging.

        Args:
            query: User query
            max_tokens: Maximum tokens of context
            audit_context: Audit context for tracing

        Returns:
            Formatted context string (same as DHCSKnowledgeBase.get_context_for_query)
        """
        audit = audit_context or AuditContext.current()
        kb = self._get_knowledge_base()

        start_time = time.time()
        error_msg = None
        context = ""

        try:
            # Call underlying method (exact same behavior)
            context = kb.get_context_for_query(query, max_tokens=max_tokens)
            success = True

        except Exception as e:
            error_msg = str(e)
            success = False
            logger.error(f"Context retrieval failed: {e}", exc_info=True)
            raise RetrievalError(f"Context retrieval failed: {e}")

        finally:
            latency_ms = (time.time() - start_time) * 1000

            # Log to audit context (estimate n_results from context length)
            estimated_results = context.count("[Source:") if context else 0
            audit.log_retrieval(
                query_length=len(query),
                n_results=estimated_results,
                latency_ms=latency_ms,
                strategy="semantic",
                cache_hit=False,
                success=success,
                error=error_msg,
            )

        return context

    def _search_with_filter(
        self,
        query: str,
        n_results: int,
        category_filter: str,
    ) -> List[Dict[str, Any]]:
        """
        Search with metadata category filter.

        Falls back to regular search + post-filtering if ChromaDB filter fails.
        """
        kb = self._get_knowledge_base()

        try:
            # Generate embedding using knowledge base's embeddings
            query_embedding = kb.embeddings.embed_query(query)

            # Search with metadata filter
            results = kb.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 2,  # Get extra for threshold filtering
                where={"category": category_filter}
            )

            return self._format_chroma_results(results)

        except Exception as e:
            # Fallback: regular search with post-filtering
            logger.warning(f"Metadata filter failed, falling back to post-filter: {e}")
            all_results = kb.search(query, n_results=n_results * 3)

            filtered = [
                r for r in all_results
                if r.get("metadata", {}).get("category") == category_filter
            ]

            return filtered[:n_results]

    def _format_chroma_results(self, results: Dict) -> List[Dict[str, Any]]:
        """Format ChromaDB query results to standard structure."""
        formatted = []

        if not results or not results.get("documents"):
            return formatted

        documents = results["documents"][0] if results["documents"] else []
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc in enumerate(documents):
            distance = distances[i] if i < len(distances) else None
            formatted.append({
                "content": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distance,
                "similarity_score": 1.0 - distance if distance is not None else None,
            })

        return formatted

    def _get_score(self, result: Dict[str, Any]) -> float:
        """Get similarity score from a result dict."""
        if "similarity_score" in result and result["similarity_score"] is not None:
            return result["similarity_score"]
        elif "distance" in result and result["distance"] is not None:
            return 1.0 - min(result["distance"], 1.0)
        return 0.0

    def get_underlying_kb(self) -> Any:
        """
        Get the underlying DHCSKnowledgeBase instance.

        Use this for compatibility with existing code.
        Note: Direct use bypasses audit logging.
        """
        return self._get_knowledge_base()

    # Compatibility properties to match DHCSKnowledgeBase interface

    @property
    def collection(self):
        """Access underlying ChromaDB collection."""
        return self._get_knowledge_base().collection

    @property
    def persist_directory(self):
        """Access persist directory."""
        return self._get_knowledge_base().persist_directory

    @property
    def embeddings(self):
        """Access embeddings model."""
        return self._get_knowledge_base().embeddings


# =============================================================================
# Backward Compatibility Alias
# =============================================================================

# Alias for Phase 0 code compatibility
RetrievalServiceShim = RetrievalService


# =============================================================================
# Singleton Service
# =============================================================================

_default_retrieval_service: Optional[RetrievalService] = None


def get_default_retrieval_service() -> RetrievalService:
    """
    Get or create the default singleton RetrievalService.

    Used when agents don't have a service injected.
    Thread-safe initialization.
    """
    global _default_retrieval_service

    if _default_retrieval_service is None:
        _default_retrieval_service = RetrievalService()

    return _default_retrieval_service


def reset_default_retrieval_service() -> None:
    """Reset the default retrieval service (for testing)."""
    global _default_retrieval_service
    _default_retrieval_service = None


# =============================================================================
# Factory Functions
# =============================================================================

def create_retrieval_service(
    knowledge_base: Optional[Any] = None,
) -> RetrievalService:
    """
    Factory function to create a RetrievalService.

    Args:
        knowledge_base: Optional existing DHCSKnowledgeBase instance

    Returns:
        Configured RetrievalService instance
    """
    return RetrievalService(knowledge_base=knowledge_base)


def wrap_existing_kb(knowledge_base: Any) -> RetrievalService:
    """
    Wrap an existing DHCSKnowledgeBase instance with RetrievalService.

    Use this for gradual migration of existing code.

    Args:
        knowledge_base: Existing DHCSKnowledgeBase instance

    Returns:
        RetrievalService wrapping the existing instance
    """
    return RetrievalService(knowledge_base=knowledge_base)
