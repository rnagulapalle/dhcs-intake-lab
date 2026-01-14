"""
Integration tests for ModelGateway audit logging.

Verifies that all LLM calls through the gateway produce audit log entries.
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI response."""
    mock_response = Mock()
    mock_response.content = "Test response"
    return mock_response


@pytest.fixture
def enable_centralized_gateway():
    """Enable centralized gateway for test."""
    original = os.environ.get("BHT_USE_CENTRALIZED_GATEWAY")
    os.environ["BHT_USE_CENTRALIZED_GATEWAY"] = "true"

    # Reset config singleton
    from platform import config as platform_config
    platform_config._platform_config = None

    yield

    # Restore
    if original:
        os.environ["BHT_USE_CENTRALIZED_GATEWAY"] = original
    else:
        os.environ.pop("BHT_USE_CENTRALIZED_GATEWAY", None)

    # Reset singleton and default gateway
    platform_config._platform_config = None
    from platform import model_gateway
    model_gateway.reset_default_gateway()


@pytest.fixture
def captured_audit_entries() -> List[Dict[str, Any]]:
    """Capture audit entries logged during test."""
    entries = []
    return entries


class TestGatewayAuditLogging:
    """Test that ModelGateway logs audit entries correctly."""

    def test_gateway_logs_llm_call_on_invoke(self, enable_centralized_gateway, mock_openai_response):
        """
        Verify that gateway.invoke() logs an LLM call audit entry.
        """
        with patch("langchain_openai.ChatOpenAI") as MockChatOpenAI:
            # Setup mock
            mock_llm = Mock()
            mock_llm.invoke.return_value = mock_openai_response
            MockChatOpenAI.return_value = mock_llm

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.audit_context import AuditContext

            reset_default_gateway()

            # Create gateway and audit context
            gateway = ModelGateway()

            with AuditContext.create(workflow_id="test_workflow") as ctx:
                # Invoke gateway
                messages = [{"role": "user", "content": "Hello"}]
                response = gateway.invoke(messages, audit_context=ctx)

                # Check audit entries
                entries = ctx.get_audit_trail()

                # Should have at least one llm_call entry
                llm_calls = [e for e in entries if e.get("type") == "llm_call"]

                assert len(llm_calls) >= 1, "Gateway should log at least one llm_call entry"

                # Verify entry contents
                entry = llm_calls[0]
                assert entry["workflow_id"] == "test_workflow"
                assert entry["model"] == gateway._model  # Should match gateway model
                assert "latency_ms" in entry
                assert "tokens_estimate" in entry
                assert entry["success"] is True

    def test_gateway_logs_error_on_failure(self, enable_centralized_gateway):
        """
        Verify that gateway logs error information when LLM call fails.
        """
        with patch("langchain_openai.ChatOpenAI") as MockChatOpenAI:
            # Setup mock to raise exception
            mock_llm = Mock()
            mock_llm.invoke.side_effect = Exception("API Error")
            MockChatOpenAI.return_value = mock_llm

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.audit_context import AuditContext

            reset_default_gateway()

            # Create gateway (with retry disabled to get immediate failure)
            os.environ["BHT_MODEL_RETRY_ENABLED"] = "false"
            gateway = ModelGateway()

            with AuditContext.create(workflow_id="test_failure") as ctx:
                messages = [{"role": "user", "content": "Hello"}]

                # Should raise but also log
                try:
                    gateway.invoke(messages, audit_context=ctx)
                except Exception:
                    pass

                # Check audit entries
                entries = ctx.get_audit_trail()

                # Should have an llm_call entry with error
                llm_calls = [e for e in entries if e.get("type") == "llm_call"]

                assert len(llm_calls) >= 1, "Gateway should log llm_call even on failure"

                # Find the failed entry
                failed_entries = [e for e in llm_calls if not e.get("success", True)]
                assert len(failed_entries) >= 1, "Should have at least one failed entry"

                entry = failed_entries[0]
                assert entry["success"] is False
                assert "error" in entry or "error_type" in entry

    def test_audit_context_propagates_trace_id(self, enable_centralized_gateway, mock_openai_response):
        """
        Verify that trace_id is propagated through audit context.
        """
        with patch("langchain_openai.ChatOpenAI") as MockChatOpenAI:
            mock_llm = Mock()
            mock_llm.invoke.return_value = mock_openai_response
            MockChatOpenAI.return_value = mock_llm

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.audit_context import AuditContext

            reset_default_gateway()

            gateway = ModelGateway()

            # Create context with specific trace_id
            custom_trace_id = "test-trace-123"
            with AuditContext.create(
                workflow_id="trace_test",
                parent_trace_id=custom_trace_id
            ) as ctx:
                messages = [{"role": "user", "content": "Hello"}]
                gateway.invoke(messages, audit_context=ctx)

                # All entries should have this trace_id
                entries = ctx.get_audit_trail()
                for entry in entries:
                    assert entry["trace_id"] == custom_trace_id, (
                        f"Entry should have trace_id={custom_trace_id}, got {entry.get('trace_id')}"
                    )


class TestAgentAuditIntegration:
    """Test that agents using centralized gateway produce audit logs."""

    def test_base_agent_produces_audit_logs(self, enable_centralized_gateway, mock_openai_response):
        """
        Verify BaseAgent with centralized gateway produces audit logs.
        """
        with patch("langchain_openai.ChatOpenAI") as MockChatOpenAI:
            mock_llm = Mock()
            mock_llm.invoke.return_value = mock_openai_response
            MockChatOpenAI.return_value = mock_llm

            from platform.model_gateway import reset_default_gateway
            from platform.audit_context import AuditContext
            from agents.core.base_agent import BaseAgent

            reset_default_gateway()

            # Create agent (should use centralized gateway)
            agent = BaseAgent(
                name="TestAgent",
                role="tester",
                goal="test audit logging"
            )

            assert agent.has_gateway(), "Agent should use gateway when centralized gateway enabled"

            # Use the agent's LLM within audit context
            with AuditContext.create(workflow_id="agent_test") as ctx:
                # Agent's LLM is the gateway's underlying LLM
                # When called through gateway.invoke, audit is logged
                gateway = agent.gateway
                messages = [{"role": "user", "content": "Test"}]
                gateway.invoke(messages, audit_context=ctx)

                entries = ctx.get_audit_trail()
                llm_calls = [e for e in entries if e.get("type") == "llm_call"]

                assert len(llm_calls) >= 1, "Agent should produce audit logs through gateway"


class TestAuditContextCurrentPropagation:
    """Test AuditContext.current() propagation."""

    def test_current_context_accessible_in_call_stack(self, enable_centralized_gateway):
        """
        Verify AuditContext.current() returns the context set by parent.
        """
        from platform.audit_context import AuditContext

        # Create context
        with AuditContext.create(
            workflow_id="parent_workflow",
            tenant_id="test_tenant"
        ) as parent_ctx:
            # Nested function should see the same context
            current = AuditContext.current()

            assert current.trace_id == parent_ctx.trace_id
            assert current.workflow_id == "parent_workflow"
            assert current.tenant_id == "test_tenant"

    def test_nested_contexts_maintain_trace_lineage(self, enable_centralized_gateway):
        """
        Verify nested audit contexts can be traced.
        """
        from platform.audit_context import AuditContext

        with AuditContext.create(workflow_id="outer") as outer_ctx:
            outer_trace = outer_ctx.trace_id

            # Create nested context with parent trace
            with AuditContext.create(
                workflow_id="inner",
                parent_trace_id=outer_trace
            ) as inner_ctx:
                # Inner should have same trace_id as we passed parent_trace_id
                assert inner_ctx.trace_id == outer_trace


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
