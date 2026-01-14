"""
Tests for LangChain Audit Callback Handler.

Verifies that LangChain chains using get_underlying_llm() emit
llm_call audit entries with proper trace correlation.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from platform.langchain_audit_callback import (
    AuditCallbackHandler,
    get_audit_callback,
    reset_audit_callback,
)
from platform.audit_context import AuditContext, _current_audit_context
from platform.audit_sink import NullAuditSink, reset_default_audit_sink


class TestAuditCallbackHandler:
    """Tests for AuditCallbackHandler."""

    def setup_method(self):
        """Reset state before each test."""
        _current_audit_context.set(None)
        reset_default_audit_sink()
        reset_audit_callback()

    def teardown_method(self):
        """Clean up after each test."""
        _current_audit_context.set(None)
        reset_default_audit_sink()
        reset_audit_callback()

    def test_callback_logs_llm_call_on_success(self):
        """Verify callback logs llm_call with mandatory fields on success."""
        sink = NullAuditSink()
        ctx = AuditContext.create(workflow_id="test_chain", sink=sink)

        callback = AuditCallbackHandler()
        run_id = uuid4()

        # Simulate LLM start
        callback.on_llm_start(
            serialized={"kwargs": {"model": "gpt-4o-mini"}},
            prompts=["What is 2+2?"],
            run_id=run_id,
        )

        # Simulate LLM end with mock response
        mock_response = MagicMock()
        mock_response.generations = [[MagicMock(text="4")]]
        mock_response.llm_output = {"token_usage": {"total_tokens": 50}}

        callback.on_llm_end(response=mock_response, run_id=run_id)

        # Verify audit entry
        entries = ctx.get_audit_trail()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["operation"] == "llm_call"
        assert entry["trace_id"] == ctx.trace_id
        assert entry["request_id"] == ctx.request_id
        assert entry["workflow_id"] == "test_chain"
        assert entry["success"] is True
        assert entry["model"] == "gpt-4o-mini"
        assert "latency_ms" in entry
        assert entry["latency_ms"] >= 0

    def test_callback_logs_llm_call_on_error(self):
        """Verify callback logs llm_call with error info on failure."""
        sink = NullAuditSink()
        ctx = AuditContext.create(workflow_id="test_chain", sink=sink)

        callback = AuditCallbackHandler()
        run_id = uuid4()

        # Simulate LLM start
        callback.on_llm_start(
            serialized={"kwargs": {"model": "gpt-4o-mini"}},
            prompts=["What is 2+2?"],
            run_id=run_id,
        )

        # Simulate LLM error
        error = Exception("Connection timeout")
        callback.on_llm_error(error=error, run_id=run_id)

        # Verify audit entry
        entries = ctx.get_audit_trail()
        assert len(entries) == 1

        entry = entries[0]
        assert entry["operation"] == "llm_call"
        assert entry["success"] is False
        assert "Connection timeout" in entry["error"]
        assert entry["error_type"] == "timeout"

    def test_callback_respects_privacy_settings(self):
        """Verify callback does NOT log prompts/responses by default."""
        sink = NullAuditSink()
        ctx = AuditContext.create(workflow_id="test_chain", sink=sink)

        callback = AuditCallbackHandler()
        run_id = uuid4()

        callback.on_llm_start(
            serialized={"kwargs": {"model": "gpt-4o-mini"}},
            prompts=["Secret prompt content"],
            run_id=run_id,
        )

        mock_response = MagicMock()
        mock_response.generations = [[MagicMock(text="Secret response")]]
        mock_response.llm_output = {}

        callback.on_llm_end(response=mock_response, run_id=run_id)

        entry = ctx.get_audit_trail()[0]

        # Prompts and responses should NOT be in entry by default
        assert "prompt" not in entry
        assert "response" not in entry
        # But lengths should be present
        assert "prompt_length" in entry
        assert "response_length" in entry

    def test_callback_shares_trace_id_with_context(self):
        """Verify callback entries share trace_id with AuditContext."""
        sink = NullAuditSink()
        ctx = AuditContext.create(workflow_id="test_chain", sink=sink)

        # Log a workflow step first
        ctx.log_workflow_step(step_name="pre_llm", latency_ms=10.0, success=True)

        # Then simulate LLM call via callback
        callback = AuditCallbackHandler()
        run_id = uuid4()

        callback.on_llm_start(
            serialized={"kwargs": {"model": "gpt-4o-mini"}},
            prompts=["Test"],
            run_id=run_id,
        )

        mock_response = MagicMock()
        mock_response.generations = [[MagicMock(text="Response")]]
        mock_response.llm_output = {}
        callback.on_llm_end(response=mock_response, run_id=run_id)

        # Log another workflow step after
        ctx.log_workflow_step(step_name="post_llm", latency_ms=5.0, success=True)

        entries = ctx.get_audit_trail()
        assert len(entries) == 3

        # All entries should share the same trace_id
        trace_ids = set(e["trace_id"] for e in entries)
        assert len(trace_ids) == 1
        assert ctx.trace_id in trace_ids

        # Verify operation types
        operations = [e["operation"] for e in entries]
        assert "workflow_step" in operations
        assert "llm_call" in operations

    def test_singleton_callback(self):
        """Verify get_audit_callback returns singleton instance."""
        reset_audit_callback()

        callback1 = get_audit_callback()
        callback2 = get_audit_callback()

        assert callback1 is callback2

    def test_multiple_concurrent_llm_calls(self):
        """Verify callback handles multiple concurrent LLM calls correctly."""
        sink = NullAuditSink()
        ctx = AuditContext.create(workflow_id="concurrent_test", sink=sink)

        callback = AuditCallbackHandler()

        # Start two LLM calls
        run_id_1 = uuid4()
        run_id_2 = uuid4()

        callback.on_llm_start(
            serialized={"kwargs": {"model": "gpt-4o-mini"}},
            prompts=["First prompt"],
            run_id=run_id_1,
        )

        callback.on_llm_start(
            serialized={"kwargs": {"model": "gpt-4o"}},
            prompts=["Second prompt"],
            run_id=run_id_2,
        )

        # End them in reverse order
        mock_response_2 = MagicMock()
        mock_response_2.generations = [[MagicMock(text="Response 2")]]
        mock_response_2.llm_output = {}
        callback.on_llm_end(response=mock_response_2, run_id=run_id_2)

        mock_response_1 = MagicMock()
        mock_response_1.generations = [[MagicMock(text="Response 1")]]
        mock_response_1.llm_output = {}
        callback.on_llm_end(response=mock_response_1, run_id=run_id_1)

        entries = ctx.get_audit_trail()
        assert len(entries) == 2

        # Both should be logged with correct models
        models = {e["model"] for e in entries}
        assert "gpt-4o-mini" in models
        assert "gpt-4o" in models


class TestModelGatewayWithCallback:
    """Tests for ModelGateway.get_underlying_llm() with callback."""

    def setup_method(self):
        _current_audit_context.set(None)
        reset_default_audit_sink()
        reset_audit_callback()

    def teardown_method(self):
        _current_audit_context.set(None)
        reset_default_audit_sink()
        reset_audit_callback()

    def test_get_underlying_llm_includes_callback_by_default(self):
        """Verify get_underlying_llm() attaches audit callback by default."""
        with patch("platform.model_gateway.ChatOpenAI") as mock_chat:
            mock_llm = MagicMock()
            mock_llm.with_config = MagicMock(return_value=mock_llm)
            mock_chat.return_value = mock_llm

            from platform.model_gateway import ModelGateway

            gateway = ModelGateway(openai_api_key="test-key")
            llm = gateway.get_underlying_llm()

            # Verify with_config was called with a callback
            mock_llm.with_config.assert_called_once()
            call_args = mock_llm.with_config.call_args
            assert "callbacks" in call_args.kwargs
            callbacks = call_args.kwargs["callbacks"]
            assert len(callbacks) == 1
            assert isinstance(callbacks[0], AuditCallbackHandler)

    def test_get_underlying_llm_without_callback(self):
        """Verify get_underlying_llm(with_audit_callback=False) returns raw LLM."""
        with patch("platform.model_gateway.ChatOpenAI") as mock_chat:
            mock_llm = MagicMock()
            mock_chat.return_value = mock_llm

            from platform.model_gateway import ModelGateway

            gateway = ModelGateway(openai_api_key="test-key")
            llm = gateway.get_underlying_llm(with_audit_callback=False)

            # Should return raw LLM without calling with_config
            assert llm is mock_llm
            mock_llm.with_config.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
