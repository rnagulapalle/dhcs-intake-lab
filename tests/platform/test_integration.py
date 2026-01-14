"""
Integration tests for BHT Platform

Tests end-to-end behavior:
- trace_id propagation through middleware
- Response headers include trace_id
- Audit logging works across components
- Feature flag behavior
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestAuditContextMiddleware:
    """Integration tests for AuditContextMiddleware."""

    @pytest.fixture
    def client(self):
        """Create test client with middleware and trace enabled."""
        with patch.dict(os.environ, {
            "BHT_PLATFORM_ENABLED": "true",
            "BHT_INCLUDE_TRACE_IN_RESPONSE": "true"
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from api.main import app
            yield TestClient(app)

            config_module._platform_config = None

    def test_health_endpoint_returns_trace_id(self, client):
        """Verify health endpoint includes trace_id in response when enabled."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Check trace metadata in response body (enabled for this test)
        assert "_trace" in data
        assert "trace_id" in data["_trace"]
        assert "request_id" in data["_trace"]

        # Verify trace_id is valid UUID format
        trace_id = data["_trace"]["trace_id"]
        assert len(trace_id) == 36  # UUID format

    def test_response_headers_include_trace_id(self, client):
        """Verify response headers include X-Trace-Id."""
        response = client.get("/health")

        assert "X-Trace-Id" in response.headers
        assert "X-Request-Id" in response.headers

        # Headers should match body
        body_trace_id = response.json()["_trace"]["trace_id"]
        header_trace_id = response.headers["X-Trace-Id"]
        assert body_trace_id == header_trace_id

    def test_trace_id_propagation_from_header(self, client):
        """Verify trace_id is propagated from X-Trace-Id header."""
        custom_trace_id = "12345678-1234-5678-1234-567812345678"

        response = client.get(
            "/health",
            headers={"X-Trace-Id": custom_trace_id}
        )

        assert response.status_code == 200

        # Response should use the provided trace_id
        data = response.json()
        assert data["_trace"]["trace_id"] == custom_trace_id

    def test_each_request_gets_unique_trace_id(self, client):
        """Verify each request gets a unique trace_id."""
        response1 = client.get("/health")
        response2 = client.get("/health")

        trace1 = response1.json()["_trace"]["trace_id"]
        trace2 = response2.json()["_trace"]["trace_id"]

        assert trace1 != trace2

    def test_workflow_id_extracted_from_path(self, client):
        """Verify workflow_id is extracted from request path."""
        response = client.get("/health")

        data = response.json()
        assert data["_trace"]["workflow_id"] == "health_check"


class TestModelGatewayShimIntegration:
    """Integration tests for ModelGatewayShim with agents."""

    def test_base_agent_with_gateway(self):
        """Verify BaseAgent works with injected gateway."""
        from platform.model_gateway import ModelGatewayShim
        from platform.audit_context import AuditContext, _current_audit_context

        # Create mock LLM
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7

        # Create gateway with mock
        gateway = ModelGatewayShim(llm=mock_llm)

        # Create audit context
        ctx = AuditContext.create(workflow_id="test")

        # Import BaseAgent
        from agents.core.base_agent import BaseAgent

        # Create agent with gateway
        agent = BaseAgent(
            name="TestAgent",
            role="Test",
            goal="Testing",
            gateway=gateway
        )

        # Verify agent has gateway
        assert agent.has_gateway() is True
        assert agent.gateway is gateway

        # Verify llm property returns underlying LLM (for chain compatibility)
        assert agent.llm is mock_llm

        _current_audit_context.set(None)

    def test_base_agent_without_gateway_preserves_behavior(self):
        """Verify BaseAgent works without gateway (backward compatibility)."""
        from agents.core.base_agent import BaseAgent

        # Create agent without gateway (existing behavior)
        with patch('agents.core.base_agent.ChatOpenAI') as mock_chat:
            mock_llm = MagicMock()
            mock_chat.return_value = mock_llm

            agent = BaseAgent(
                name="TestAgent",
                role="Test",
                goal="Testing"
            )

            # Verify no gateway
            assert agent.has_gateway() is False
            assert agent.gateway is None

            # Verify direct LLM instantiation
            mock_chat.assert_called_once()


class TestAuditLoggingIntegration:
    """Integration tests for audit logging across components."""

    def test_gateway_logs_to_audit_context(self):
        """Verify gateway logs are captured in audit context."""
        from platform.model_gateway import ModelGatewayShim, BudgetTags
        from platform.audit_context import AuditContext, _current_audit_context

        # Setup
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response

        gateway = ModelGatewayShim(llm=mock_llm)

        # Create context and invoke
        with AuditContext.create(workflow_id="curation") as ctx:
            gateway.invoke(
                "Hello",
                budget_tags=BudgetTags(operation="test_invoke")
            )

            # Verify audit entry
            entries = ctx.get_audit_trail()
            assert len(entries) == 1
            assert entries[0]["type"] == "llm_call"
            assert entries[0]["operation"] == "test_invoke"
            assert entries[0]["workflow_id"] == "curation"

    def test_retrieval_logs_to_audit_context(self):
        """Verify retrieval logs are captured in audit context."""
        from platform.retrieval_service import RetrievalServiceShim
        from platform.audit_context import AuditContext

        # Setup
        mock_kb = MagicMock()
        mock_kb.search.return_value = [{"content": "test"}]

        service = RetrievalServiceShim(knowledge_base=mock_kb)

        # Create context and search
        with AuditContext.create(workflow_id="knowledge_search") as ctx:
            service.search("test query", n_results=5)

            # Verify audit entry
            entries = ctx.get_audit_trail()
            assert len(entries) == 1
            assert entries[0]["type"] == "retrieval"
            assert entries[0]["workflow_id"] == "knowledge_search"

    def test_combined_operations_logged(self):
        """Verify multiple operations are logged in order."""
        from platform.model_gateway import ModelGatewayShim
        from platform.retrieval_service import RetrievalServiceShim
        from platform.audit_context import AuditContext

        # Setup mocks
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_llm.invoke.return_value = mock_response

        mock_kb = MagicMock()
        mock_kb.search.return_value = []

        gateway = ModelGatewayShim(llm=mock_llm)
        retrieval = RetrievalServiceShim(knowledge_base=mock_kb)

        # Execute multiple operations
        with AuditContext.create(workflow_id="combined") as ctx:
            retrieval.search("query")
            gateway.invoke("Hello")
            retrieval.search("another query")

            entries = ctx.get_audit_trail()
            assert len(entries) == 3
            assert entries[0]["type"] == "retrieval"
            assert entries[1]["type"] == "llm_call"
            assert entries[2]["type"] == "retrieval"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
