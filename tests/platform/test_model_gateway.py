"""
Unit tests for BHT Platform ModelGatewayShim

Tests:
- Shim wraps ChatOpenAI correctly
- Audit logging is performed
- Budget tags are tracked
- Behavior is preserved from original ChatOpenAI usage
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import time

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from platform.model_gateway import (
    ModelGatewayShim,
    ModelInvocationResult,
    BudgetTags,
    create_gateway_from_settings,
    wrap_existing_llm
)
from platform.audit_context import AuditContext, _current_audit_context
from platform.errors import ModelGatewayError


class TestBudgetTags:
    """Tests for BudgetTags dataclass."""

    def test_budget_tags_defaults(self):
        """Verify BudgetTags default values."""
        tags = BudgetTags()
        assert tags.tenant_id == "default"
        assert tags.workflow_id == "unknown"
        assert tags.operation == "invoke"
        assert tags.use_case is None

    def test_budget_tags_to_dict(self):
        """Verify BudgetTags.to_dict() output."""
        tags = BudgetTags(
            tenant_id="county_la",
            workflow_id="curation",
            operation="extract",
            use_case="policy_qa"
        )
        d = tags.to_dict()

        assert d["tenant_id"] == "county_la"
        assert d["workflow_id"] == "curation"
        assert d["operation"] == "extract"
        assert d["use_case"] == "policy_qa"


class TestModelInvocationResult:
    """Tests for ModelInvocationResult dataclass."""

    def test_invocation_result_to_dict(self):
        """Verify ModelInvocationResult.to_dict() output."""
        result = ModelInvocationResult(
            content="Hello, world!",
            model_used="gpt-4o-mini",
            latency_ms=150.5,
            tokens_estimate=50,
            trace_id="abc123",
            success=True
        )
        d = result.to_dict()

        assert d["content"] == "Hello, world!"
        assert d["model_used"] == "gpt-4o-mini"
        assert d["latency_ms"] == 150.5
        assert d["trace_id"] == "abc123"


class TestModelGatewayShimInitialization:
    """Tests for ModelGatewayShim initialization."""

    @patch('platform.model_gateway.ChatOpenAI')
    def test_init_creates_llm(self, mock_chat_openai):
        """Verify that shim creates ChatOpenAI with correct params."""
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm

        with patch('agents.core.config.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.agent_model = "gpt-4o-mini"
            mock_settings.agent_temperature = 0.7

            gateway = ModelGatewayShim(
                model="gpt-4o-mini",
                temperature=0.5,
                openai_api_key="test-key"
            )

            mock_chat_openai.assert_called_once_with(
                model="gpt-4o-mini",
                temperature=0.5,
                openai_api_key="test-key"
            )

    def test_wrap_existing_llm(self):
        """Verify that wrap_existing_llm wraps an LLM instance."""
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7

        gateway = ModelGatewayShim(llm=mock_llm)

        assert gateway.model == "gpt-4o-mini"
        assert gateway.temperature == 0.7
        assert gateway.get_underlying_llm() is mock_llm


class TestModelGatewayShimInvoke:
    """Tests for ModelGatewayShim.invoke() method."""

    def test_invoke_returns_result(self):
        """Verify that invoke returns ModelInvocationResult."""
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response

        gateway = ModelGatewayShim(llm=mock_llm)
        ctx = AuditContext.create(workflow_id="test")

        result = gateway.invoke("Hello", audit_context=ctx)

        assert isinstance(result, ModelInvocationResult)
        assert result.content == "Test response"
        assert result.model_used == "gpt-4o-mini"
        assert result.success is True
        assert result.trace_id == ctx.trace_id

        _current_audit_context.set(None)

    def test_invoke_logs_to_audit_context(self):
        """Verify that invoke logs to audit context."""
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response

        gateway = ModelGatewayShim(llm=mock_llm)
        ctx = AuditContext.create(workflow_id="test")

        gateway.invoke("Hello", audit_context=ctx)

        entries = ctx.get_audit_trail()
        assert len(entries) == 1
        assert entries[0]["type"] == "llm_call"
        assert entries[0]["model"] == "gpt-4o-mini"
        assert entries[0]["success"] is True

        _current_audit_context.set(None)

    def test_invoke_handles_string_input(self):
        """Verify that invoke handles string input."""
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_llm.invoke.return_value = mock_response

        gateway = ModelGatewayShim(llm=mock_llm)

        result = gateway.invoke("Simple string input")

        assert result.content == "Response"
        mock_llm.invoke.assert_called_once()
        # Verify message was converted to HumanMessage
        call_args = mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0].content == "Simple string input"

        _current_audit_context.set(None)

    def test_invoke_handles_dict_messages(self):
        """Verify that invoke handles dict message format."""
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_llm.invoke.return_value = mock_response

        gateway = ModelGatewayShim(llm=mock_llm)

        result = gateway.invoke([
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"}
        ])

        assert result.content == "Response"
        call_args = mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 2

        _current_audit_context.set(None)

    def test_invoke_uses_budget_tags(self):
        """Verify that invoke uses budget tags in audit."""
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_llm.invoke.return_value = mock_response

        gateway = ModelGatewayShim(llm=mock_llm)
        ctx = AuditContext.create(workflow_id="test")

        gateway.invoke(
            "Hello",
            budget_tags=BudgetTags(
                tenant_id="county_la",
                workflow_id="curation",
                operation="synthesis"
            ),
            audit_context=ctx
        )

        entries = ctx.get_audit_trail()
        assert entries[0]["operation"] == "synthesis"

        _current_audit_context.set(None)

    def test_invoke_raises_on_error(self):
        """Verify that invoke raises ModelGatewayError on failure."""
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7
        mock_llm.invoke.side_effect = Exception("API Error")

        gateway = ModelGatewayShim(llm=mock_llm)
        ctx = AuditContext.create(workflow_id="test")

        with pytest.raises(ModelGatewayError) as exc_info:
            gateway.invoke("Hello", audit_context=ctx)

        assert "API Error" in str(exc_info.value)

        # Error should still be logged
        entries = ctx.get_audit_trail()
        assert len(entries) == 1
        assert entries[0]["success"] is False

        _current_audit_context.set(None)


class TestModelGatewayShimInvokeRaw:
    """Tests for ModelGatewayShim.invoke_raw() method."""

    def test_invoke_raw_returns_langchain_response(self):
        """Verify that invoke_raw returns raw LangChain response."""
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response

        gateway = ModelGatewayShim(llm=mock_llm)

        result = gateway.invoke_raw("Hello")

        # Should return the raw mock response, not ModelInvocationResult
        assert result is mock_response

        _current_audit_context.set(None)


class TestModelGatewayShimCompatibility:
    """Tests for backward compatibility features."""

    def test_get_underlying_llm(self):
        """Verify that get_underlying_llm returns the wrapped LLM."""
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7

        gateway = ModelGatewayShim(llm=mock_llm)
        underlying = gateway.get_underlying_llm()

        assert underlying is mock_llm


class TestTokenEstimation:
    """Tests for token estimation."""

    def test_token_estimation(self):
        """Verify token estimation is reasonable."""
        mock_llm = MagicMock()
        mock_llm.model_name = "gpt-4o-mini"
        mock_llm.temperature = 0.7
        mock_response = MagicMock()
        mock_response.content = "A" * 400  # 400 chars ~ 100 tokens
        mock_llm.invoke.return_value = mock_response

        gateway = ModelGatewayShim(llm=mock_llm)

        # Input: 100 chars, Output: 400 chars = 500 chars total
        result = gateway.invoke("A" * 100)

        # 500 chars / 4 = 125 tokens
        assert result.tokens_estimate == 125

        _current_audit_context.set(None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
