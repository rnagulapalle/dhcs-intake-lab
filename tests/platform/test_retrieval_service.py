"""
Unit tests for BHT Platform RetrievalService (Phase 2)

Tests:
- RetrievalService wraps DHCSKnowledgeBase correctly
- Citation schema is canonical and serializable
- Audit logging is performed with trace propagation
- Backward compatibility with Phase 0 code
- Same results pre/post migration
"""
import json
import pytest
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from platform.retrieval_service import (
    RetrievalService,
    RetrievalServiceShim,  # Backward compatibility alias
    RetrievalResult,
    Citation,
    create_retrieval_service,
    wrap_existing_kb,
    get_default_retrieval_service,
    reset_default_retrieval_service,
)
from platform.audit_context import AuditContext, _current_audit_context
from platform.errors import RetrievalError


# =============================================================================
# Citation Schema Tests
# =============================================================================

class TestCitationSchema:
    """Tests for canonical Citation schema."""

    def test_citation_to_dict(self):
        """Verify Citation.to_dict() produces valid JSON-serializable dict."""
        citation = Citation(
            source_id="dhcs_policy_v2024",
            source_name="DHCS Policy Manual",
            doc_uri="/docs/policy/manual.pdf",
            chunk_id="dhcs_policy_v2024_chunk_3",
            snippet="Mobile crisis teams must respond within 60 minutes.",
            score=0.89,
            metadata={"section": "Crisis Response", "version": "2024.1"}
        )

        d = citation.to_dict()

        assert d["source_id"] == "dhcs_policy_v2024"
        assert d["source_name"] == "DHCS Policy Manual"
        assert d["doc_uri"] == "/docs/policy/manual.pdf"
        assert d["chunk_id"] == "dhcs_policy_v2024_chunk_3"
        assert d["snippet"] == "Mobile crisis teams must respond within 60 minutes."
        assert d["score"] == 0.89
        assert d["metadata"]["section"] == "Crisis Response"

        # Verify JSON serializable
        json_str = json.dumps(d)
        assert json_str is not None

    def test_citation_from_retrieval_result(self):
        """Verify Citation.from_retrieval_result() normalizes data correctly."""
        raw_result = {
            "content": "Mobile crisis teams must respond within 60 minutes in urban areas.",
            "metadata": {
                "source": "DHCS Mobile Crisis Standards",
                "section": "Dispatch and Response",
                "version": "2024.1",
                "category": "protocol"
            },
            "distance": 0.15  # ChromaDB distance format
        }

        citation = Citation.from_retrieval_result(raw_result)

        assert citation.source_name == "DHCS Mobile Crisis Standards"
        assert citation.snippet == raw_result["content"]
        assert citation.score == pytest.approx(0.85, abs=0.01)  # 1 - 0.15
        assert citation.metadata["section"] == "Dispatch and Response"

    def test_citation_from_retrieval_result_with_similarity_score(self):
        """Verify Citation handles similarity_score format."""
        raw_result = {
            "content": "Test content",
            "metadata": {"source": "Test Source"},
            "similarity_score": 0.92
        }

        citation = Citation.from_retrieval_result(raw_result)

        assert citation.score == 0.92

    def test_citation_handles_missing_metadata(self):
        """Verify Citation handles missing/minimal metadata gracefully."""
        raw_result = {
            "content": "Some content",
            "metadata": {},
            "distance": 0.2
        }

        citation = Citation.from_retrieval_result(raw_result)

        assert citation.source_name == "Unknown"
        assert citation.snippet == "Some content"
        assert citation.score == pytest.approx(0.8, abs=0.01)

    def test_citation_contract_all_fields_present(self):
        """Verify Citation contract: all required fields are present."""
        citation = Citation(
            source_id="test_id",
            source_name="Test",
            doc_uri="/test",
            chunk_id="chunk_1",
            snippet="Test snippet",
            score=0.5
        )

        d = citation.to_dict()

        required_fields = ["source_id", "source_name", "doc_uri", "chunk_id", "snippet", "score", "metadata"]
        for field in required_fields:
            assert field in d, f"Missing required field: {field}"


# =============================================================================
# RetrievalResult Tests
# =============================================================================

class TestRetrievalResult:
    """Tests for RetrievalResult dataclass."""

    def test_retrieval_result_to_dict(self):
        """Verify RetrievalResult.to_dict() includes citations."""
        citations = [
            Citation(
                source_id="test1",
                source_name="Test 1",
                doc_uri="/test1",
                chunk_id="chunk_1",
                snippet="Snippet 1",
                score=0.9
            )
        ]

        result = RetrievalResult(
            results=[{"content": "test"}],
            citations=citations,
            query="test query",
            n_results=1,
            latency_ms=25.5,
            trace_id="abc123",
            cache_hit=False,
            success=True
        )

        d = result.to_dict()

        assert d["query"] == "test query"
        assert d["n_results"] == 1
        assert d["latency_ms"] == 25.5
        assert d["trace_id"] == "abc123"
        assert d["cache_hit"] is False
        assert len(d["citations"]) == 1
        assert d["citations"][0]["source_id"] == "test1"

        # Verify JSON serializable
        json_str = json.dumps(d)
        assert json_str is not None

    def test_retrieval_result_includes_strategy(self):
        """Verify RetrievalResult includes search strategy."""
        result = RetrievalResult(
            results=[],
            citations=[],
            query="test",
            n_results=0,
            latency_ms=10.0,
            trace_id="test123",
            strategy="hybrid"
        )

        d = result.to_dict()
        assert d["strategy"] == "hybrid"


# =============================================================================
# RetrievalService Initialization Tests
# =============================================================================

class TestRetrievalServiceInitialization:
    """Tests for RetrievalService initialization."""

    def test_init_with_knowledge_base(self):
        """Verify service accepts knowledge base."""
        mock_kb = MagicMock()
        service = RetrievalService(knowledge_base=mock_kb)

        assert service._initialized is True
        assert service.get_underlying_kb() is mock_kb

    def test_init_without_knowledge_base(self):
        """Verify service can initialize without knowledge base (lazy loading)."""
        service = RetrievalService()
        assert service._initialized is False

    def test_backward_compatibility_alias(self):
        """Verify RetrievalServiceShim alias works."""
        mock_kb = MagicMock()
        service = RetrievalServiceShim(knowledge_base=mock_kb)

        assert isinstance(service, RetrievalService)


# =============================================================================
# RetrievalService Search Tests
# =============================================================================

class TestRetrievalServiceSearch:
    """Tests for RetrievalService.search() method."""

    def test_search_returns_result_with_citations(self):
        """Verify that search returns RetrievalResult with citations."""
        mock_kb = MagicMock()
        mock_kb.search.return_value = [
            {"content": "Result 1", "metadata": {"source": "Source 1"}, "distance": 0.1},
            {"content": "Result 2", "metadata": {"source": "Source 2"}, "distance": 0.2}
        ]

        service = RetrievalService(knowledge_base=mock_kb)
        ctx = AuditContext.create(workflow_id="test")

        result = service.search("test query", n_results=5, audit_context=ctx)

        assert isinstance(result, RetrievalResult)
        assert result.n_results == 2
        assert result.success is True
        assert result.trace_id == ctx.trace_id
        assert len(result.citations) == 2
        assert result.citations[0].source_name == "Source 1"
        assert result.citations[1].source_name == "Source 2"

        _current_audit_context.set(None)

    def test_search_calls_underlying_kb(self):
        """Verify that search calls underlying knowledge base."""
        mock_kb = MagicMock()
        mock_kb.search.return_value = []

        service = RetrievalService(knowledge_base=mock_kb)

        service.search("test query", n_results=10)

        mock_kb.search.assert_called_once_with("test query", n_results=10)

        _current_audit_context.set(None)

    def test_search_logs_to_audit_context(self):
        """Verify that search logs to audit context."""
        mock_kb = MagicMock()
        mock_kb.search.return_value = [{"content": "test", "metadata": {}}]

        service = RetrievalService(knowledge_base=mock_kb)
        ctx = AuditContext.create(workflow_id="test")

        service.search("test query", n_results=5, audit_context=ctx)

        entries = ctx.get_audit_trail()
        assert len(entries) == 1
        assert entries[0]["type"] == "retrieval"
        assert entries[0]["query_length"] == len("test query")
        assert entries[0]["n_results"] == 1
        assert entries[0]["strategy"] == "semantic"
        assert entries[0]["success"] is True
        assert "latency_ms" in entries[0]

        _current_audit_context.set(None)

    def test_search_raises_on_error(self):
        """Verify that search raises RetrievalError on failure."""
        mock_kb = MagicMock()
        mock_kb.search.side_effect = Exception("Database error")

        service = RetrievalService(knowledge_base=mock_kb)
        ctx = AuditContext.create(workflow_id="test")

        with pytest.raises(RetrievalError) as exc_info:
            service.search("test query", audit_context=ctx)

        assert "Database error" in str(exc_info.value)

        # Error should still be logged
        entries = ctx.get_audit_trail()
        assert len(entries) == 1
        assert entries[0]["success"] is False

        _current_audit_context.set(None)

    def test_search_with_similarity_threshold(self):
        """Verify similarity threshold filtering works."""
        mock_kb = MagicMock()
        mock_kb.search.return_value = [
            {"content": "High score", "metadata": {}, "similarity_score": 0.9},
            {"content": "Low score", "metadata": {}, "similarity_score": 0.3},
            {"content": "Medium score", "metadata": {}, "similarity_score": 0.6},
        ]

        service = RetrievalService(knowledge_base=mock_kb)

        result = service.search("test", similarity_threshold=0.5)

        assert result.n_results == 2  # Only 0.9 and 0.6 pass threshold
        assert len(result.citations) == 2

        _current_audit_context.set(None)


# =============================================================================
# RetrievalService Specialized Search Tests
# =============================================================================

class TestRetrievalServiceSpecializedSearch:
    """Tests for specialized search methods."""

    def test_search_statutes(self):
        """Verify search_statutes uses correct category filter."""
        mock_kb = MagicMock()
        mock_kb.embeddings.embed_query.return_value = [0.1] * 768
        mock_kb.collection.query.return_value = {
            "documents": [["Statute content"]],
            "metadatas": [[{"category": "statute", "source": "W&I Code"}]],
            "distances": [[0.2]]
        }

        service = RetrievalService(knowledge_base=mock_kb)

        result = service.search_statutes("documentation requirements")

        assert result.success is True
        mock_kb.collection.query.assert_called_once()
        call_kwargs = mock_kb.collection.query.call_args[1]
        assert call_kwargs["where"] == {"category": "statute"}

        _current_audit_context.set(None)

    def test_search_policies_excludes_toc(self):
        """Verify search_policies filters out Table of Contents."""
        mock_kb = MagicMock()
        mock_kb.embeddings.embed_query.return_value = [0.1] * 768
        mock_kb.collection.query.return_value = {
            "documents": [["Policy content", "Table of Contents entry"]],
            "metadatas": [[
                {"category": "policy", "section": "Requirements", "source": "DHCS Policy"},
                {"category": "policy", "section": "Table of Contents", "source": "DHCS Policy"}
            ]],
            "distances": [[0.2, 0.3]]
        }

        service = RetrievalService(knowledge_base=mock_kb)

        result = service.search_policies("requirements", exclude_toc=True)

        # TOC entry should be filtered out
        assert all("Table of Contents" not in c.metadata.get("section", "") for c in result.citations)

        _current_audit_context.set(None)


# =============================================================================
# GetContext Tests
# =============================================================================

class TestRetrievalServiceGetContext:
    """Tests for RetrievalService.get_context_for_query() method."""

    def test_get_context_returns_string(self):
        """Verify that get_context_for_query returns string."""
        mock_kb = MagicMock()
        mock_kb.get_context_for_query.return_value = "[Source: test]\nContent here"

        service = RetrievalService(knowledge_base=mock_kb)
        ctx = AuditContext.create(workflow_id="test")

        result = service.get_context_for_query("test query", max_tokens=1000, audit_context=ctx)

        assert isinstance(result, str)
        assert "Content here" in result

        _current_audit_context.set(None)

    def test_get_context_calls_underlying_kb(self):
        """Verify that get_context_for_query calls underlying method."""
        mock_kb = MagicMock()
        mock_kb.get_context_for_query.return_value = "context"

        service = RetrievalService(knowledge_base=mock_kb)

        service.get_context_for_query("test query", max_tokens=500)

        mock_kb.get_context_for_query.assert_called_once_with("test query", max_tokens=500)

        _current_audit_context.set(None)


# =============================================================================
# Compatibility Tests
# =============================================================================

class TestRetrievalServiceCompatibility:
    """Tests for backward compatibility features."""

    def test_collection_property(self):
        """Verify collection property access."""
        mock_kb = MagicMock()
        mock_collection = MagicMock()
        mock_kb.collection = mock_collection

        service = RetrievalService(knowledge_base=mock_kb)

        assert service.collection is mock_collection

    def test_persist_directory_property(self):
        """Verify persist_directory property access."""
        mock_kb = MagicMock()
        mock_kb.persist_directory = "/path/to/data"

        service = RetrievalService(knowledge_base=mock_kb)

        assert service.persist_directory == "/path/to/data"

    def test_embeddings_property(self):
        """Verify embeddings property access."""
        mock_kb = MagicMock()
        mock_embeddings = MagicMock()
        mock_kb.embeddings = mock_embeddings

        service = RetrievalService(knowledge_base=mock_kb)

        assert service.embeddings is mock_embeddings


# =============================================================================
# Factory Functions Tests
# =============================================================================

class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_retrieval_service(self):
        """Verify create_retrieval_service factory."""
        mock_kb = MagicMock()
        service = create_retrieval_service(knowledge_base=mock_kb)

        assert isinstance(service, RetrievalService)
        assert service.get_underlying_kb() is mock_kb

    def test_wrap_existing_kb(self):
        """Verify wrap_existing_kb factory."""
        mock_kb = MagicMock()
        service = wrap_existing_kb(mock_kb)

        assert isinstance(service, RetrievalService)
        assert service.get_underlying_kb() is mock_kb


# =============================================================================
# Singleton Tests
# =============================================================================

class TestSingletonService:
    """Tests for singleton retrieval service."""

    def test_get_default_retrieval_service(self):
        """Verify get_default_retrieval_service returns singleton."""
        reset_default_retrieval_service()

        service1 = get_default_retrieval_service()
        service2 = get_default_retrieval_service()

        assert service1 is service2

    def test_reset_default_retrieval_service(self):
        """Verify reset clears singleton."""
        service1 = get_default_retrieval_service()
        reset_default_retrieval_service()
        service2 = get_default_retrieval_service()

        assert service1 is not service2


# =============================================================================
# Contract Tests
# =============================================================================

class TestCitationContract:
    """Contract tests for Citation schema stability."""

    def test_citation_json_roundtrip(self):
        """Verify Citation survives JSON roundtrip."""
        original = Citation(
            source_id="test_source",
            source_name="Test Source Name",
            doc_uri="/docs/test.pdf",
            chunk_id="test_chunk_1",
            snippet="This is the test snippet content.",
            score=0.87,
            metadata={"key": "value", "number": 42}
        )

        # Serialize
        json_str = json.dumps(original.to_dict())

        # Deserialize
        parsed = json.loads(json_str)

        # Verify all fields
        assert parsed["source_id"] == "test_source"
        assert parsed["source_name"] == "Test Source Name"
        assert parsed["doc_uri"] == "/docs/test.pdf"
        assert parsed["chunk_id"] == "test_chunk_1"
        assert parsed["snippet"] == "This is the test snippet content."
        assert parsed["score"] == 0.87
        assert parsed["metadata"]["key"] == "value"
        assert parsed["metadata"]["number"] == 42

    def test_retrieval_result_json_serializable(self):
        """Verify entire RetrievalResult is JSON serializable."""
        citations = [
            Citation(
                source_id="s1",
                source_name="Source 1",
                doc_uri="/s1",
                chunk_id="c1",
                snippet="Snippet 1",
                score=0.9
            ),
            Citation(
                source_id="s2",
                source_name="Source 2",
                doc_uri="/s2",
                chunk_id="c2",
                snippet="Snippet 2",
                score=0.8
            )
        ]

        result = RetrievalResult(
            results=[{"content": "r1"}, {"content": "r2"}],
            citations=citations,
            query="test query",
            n_results=2,
            latency_ms=123.45,
            trace_id="trace-uuid-here",
            cache_hit=False,
            success=True
        )

        # Should not raise
        json_str = json.dumps(result.to_dict())
        parsed = json.loads(json_str)

        assert len(parsed["citations"]) == 2
        assert parsed["trace_id"] == "trace-uuid-here"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
