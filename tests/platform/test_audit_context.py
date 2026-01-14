"""
Unit tests for BHT Platform AuditContext

Tests:
- trace_id and request_id generation
- Context propagation via ContextVar
- Audit logging methods
- Context manager behavior
"""
import pytest
import uuid
import json
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from platform.audit_context import AuditContext, _current_audit_context
from platform.config import PlatformConfig


class TestAuditContextCreation:
    """Tests for AuditContext creation and initialization."""

    def test_create_generates_unique_ids(self):
        """Verify that create() generates unique trace_id and request_id."""
        ctx1 = AuditContext.create(workflow_id="test1")
        ctx2 = AuditContext.create(workflow_id="test2")

        assert ctx1.trace_id != ctx2.trace_id
        assert ctx1.request_id != ctx2.request_id

        # Clean up
        _current_audit_context.set(None)

    def test_create_uses_parent_trace_id(self):
        """Verify that create() respects parent_trace_id for distributed tracing."""
        parent_id = str(uuid.uuid4())
        ctx = AuditContext.create(
            workflow_id="test",
            parent_trace_id=parent_id
        )

        assert ctx.trace_id == parent_id
        _current_audit_context.set(None)

    def test_create_sets_workflow_and_tenant(self):
        """Verify that create() sets workflow_id and tenant_id."""
        ctx = AuditContext.create(
            workflow_id="curation",
            tenant_id="county_la",
            use_case="policy_qa"
        )

        assert ctx.workflow_id == "curation"
        assert ctx.tenant_id == "county_la"
        assert ctx.use_case == "policy_qa"
        _current_audit_context.set(None)

    def test_create_sets_current_context(self):
        """Verify that create() sets the context as current."""
        ctx = AuditContext.create(workflow_id="test")
        current = AuditContext.current()

        assert current is ctx
        assert current.trace_id == ctx.trace_id
        _current_audit_context.set(None)


class TestAuditContextCurrent:
    """Tests for AuditContext.current() method."""

    def test_current_creates_default_when_none(self):
        """Verify that current() creates default context when none exists."""
        _current_audit_context.set(None)
        ctx = AuditContext.current()

        assert ctx is not None
        assert ctx.trace_id is not None
        assert ctx.workflow_id == "unknown"
        assert ctx.tenant_id == "default"
        _current_audit_context.set(None)

    def test_current_returns_existing_context(self):
        """Verify that current() returns existing context."""
        ctx = AuditContext.create(workflow_id="existing")
        retrieved = AuditContext.current()

        assert retrieved is ctx
        _current_audit_context.set(None)

    def test_get_current_trace_id_without_context(self):
        """Verify that get_current_trace_id() works without context."""
        _current_audit_context.set(None)
        trace_id = AuditContext.get_current_trace_id()

        assert trace_id is not None
        # Should be valid UUID format
        uuid.UUID(trace_id)

    def test_get_current_trace_id_with_context(self):
        """Verify that get_current_trace_id() returns context trace_id."""
        ctx = AuditContext.create(workflow_id="test")
        trace_id = AuditContext.get_current_trace_id()

        assert trace_id == ctx.trace_id
        _current_audit_context.set(None)


class TestAuditContextManager:
    """Tests for AuditContext as context manager."""

    def test_context_manager_sets_and_clears(self):
        """Verify that context manager sets and clears context."""
        _current_audit_context.set(None)

        with AuditContext.create(workflow_id="test") as ctx:
            current = AuditContext.current()
            assert current is ctx

        # After exit, context should be cleared
        assert _current_audit_context.get() is None

    def test_nested_context_managers(self):
        """Verify that nested context managers work correctly."""
        with AuditContext.create(workflow_id="outer") as outer:
            outer_trace = outer.trace_id

            with AuditContext.create(workflow_id="inner") as inner:
                assert AuditContext.current() is inner
                assert inner.trace_id != outer_trace

            # After inner exits, outer should not be restored (by design)
            # This is intentional - contexts are not nested

        assert _current_audit_context.get() is None


class TestAuditLogging:
    """Tests for AuditContext logging methods."""

    def test_log_llm_call_creates_entry(self):
        """Verify that log_llm_call creates correct audit entry."""
        ctx = AuditContext.create(workflow_id="test")

        ctx.log_llm_call(
            model="gpt-4o-mini",
            latency_ms=150.5,
            tokens=500,
            operation="invoke",
            success=True,
            prompt_length=100,
            response_length=200
        )

        entries = ctx.get_audit_trail()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["type"] == "llm_call"
        assert entry["model"] == "gpt-4o-mini"
        assert entry["latency_ms"] == 150.5
        assert entry["tokens_estimate"] == 500
        assert entry["success"] is True
        assert entry["trace_id"] == ctx.trace_id
        _current_audit_context.set(None)

    def test_log_llm_call_with_error(self):
        """Verify that log_llm_call handles errors."""
        ctx = AuditContext.create(workflow_id="test")

        ctx.log_llm_call(
            model="gpt-4o-mini",
            latency_ms=50,
            tokens=0,
            success=False,
            error="Rate limit exceeded"
        )

        entries = ctx.get_audit_trail()
        assert entries[0]["success"] is False
        assert entries[0]["error"] == "Rate limit exceeded"
        _current_audit_context.set(None)

    def test_log_retrieval_creates_entry(self):
        """Verify that log_retrieval creates correct audit entry."""
        ctx = AuditContext.create(workflow_id="test")

        ctx.log_retrieval(
            query_length=50,
            n_results=5,
            latency_ms=25.3,
            strategy="semantic",
            cache_hit=False
        )

        entries = ctx.get_audit_trail()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["type"] == "retrieval"
        assert entry["query_length"] == 50
        assert entry["n_results"] == 5
        assert entry["strategy"] == "semantic"
        assert entry["cache_hit"] is False
        _current_audit_context.set(None)

    def test_log_workflow_step_creates_entry(self):
        """Verify that log_workflow_step creates correct audit entry."""
        ctx = AuditContext.create(workflow_id="curation")

        ctx.log_workflow_step(
            step_name="evidence_extraction",
            latency_ms=500,
            success=True,
            input_summary="10 chunks",
            output_summary="5 requirements",
            metadata={"chunk_count": 10}
        )

        entries = ctx.get_audit_trail()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["type"] == "workflow_step"
        assert entry["step_name"] == "evidence_extraction"
        assert entry["metadata"]["chunk_count"] == 10
        _current_audit_context.set(None)

    def test_log_api_request_creates_entry(self):
        """Verify that log_api_request creates correct audit entry."""
        ctx = AuditContext.create(workflow_id="test")

        ctx.log_api_request(
            endpoint="/curation/process",
            method="POST",
            status_code=200,
            latency_ms=1500
        )

        entries = ctx.get_audit_trail()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["type"] == "api_request"
        assert entry["endpoint"] == "/curation/process"
        assert entry["status_code"] == 200
        assert entry["success"] is True
        _current_audit_context.set(None)


class TestAuditTraceMetadata:
    """Tests for trace metadata methods."""

    def test_get_trace_metadata(self):
        """Verify that get_trace_metadata returns safe metadata."""
        ctx = AuditContext.create(
            workflow_id="curation",
            tenant_id="county_la"
        )

        metadata = ctx.get_trace_metadata()

        assert "trace_id" in metadata
        assert "request_id" in metadata
        assert "workflow_id" in metadata
        assert metadata["workflow_id"] == "curation"

        # Should NOT include sensitive fields
        assert "tenant_id" not in metadata or metadata.get("tenant_id") is None
        _current_audit_context.set(None)

    def test_get_audit_trail_returns_copy(self):
        """Verify that get_audit_trail returns a copy, not original."""
        ctx = AuditContext.create(workflow_id="test")
        ctx.log_llm_call(model="test", latency_ms=10, tokens=10)

        trail1 = ctx.get_audit_trail()
        trail2 = ctx.get_audit_trail()

        assert trail1 is not trail2
        assert trail1 == trail2
        _current_audit_context.set(None)


class TestAuditPrivacyProtection:
    """Tests for privacy protection in audit logging."""

    def test_prompt_not_logged_by_default(self):
        """Verify that full prompts are not logged by default."""
        config = PlatformConfig()
        config.audit_log_prompts = False

        ctx = AuditContext.create(workflow_id="test")
        ctx._config = config

        ctx.log_llm_call(
            model="test",
            latency_ms=10,
            tokens=10,
            prompt="This is a secret prompt",
            response="This is a secret response"
        )

        entries = ctx.get_audit_trail()
        assert "prompt" not in entries[0]
        assert "response" not in entries[0]
        _current_audit_context.set(None)

    def test_prompt_logged_when_enabled(self):
        """Verify that prompts are logged when explicitly enabled."""
        config = PlatformConfig()
        config.audit_log_prompts = True
        config.audit_log_responses = True

        ctx = AuditContext.create(workflow_id="test")
        ctx._config = config

        ctx.log_llm_call(
            model="test",
            latency_ms=10,
            tokens=10,
            prompt="This is a test prompt",
            response="This is a test response"
        )

        entries = ctx.get_audit_trail()
        assert entries[0].get("prompt") == "This is a test prompt"
        assert entries[0].get("response") == "This is a test response"
        _current_audit_context.set(None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
