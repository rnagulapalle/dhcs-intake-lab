"""
Integration tests for centralized ModelGateway usage.

Tests:
- All agent LLM invocations flow through ModelGateway when enabled
- Audit logs are created for all LLM calls
- BaseAgent uses centralized gateway when BHT_USE_CENTRALIZED_GATEWAY=true
- Direct ChatOpenAI usage bypassed when gateway is active
"""
import os
import pytest
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCentralizedGatewayIntegration:
    """Integration tests for centralized gateway behavior."""

    def test_base_agent_uses_centralized_gateway_when_enabled(self):
        """Verify BaseAgent uses singleton gateway when flag is enabled."""
        with patch.dict(os.environ, {
            "BHT_USE_CENTRALIZED_GATEWAY": "true",
            "BHT_PLATFORM_ENABLED": "true",
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import reset_default_gateway, get_default_gateway
            reset_default_gateway()

            # Mock the gateway creation
            with patch('platform.model_gateway.ChatOpenAI') as mock_chat:
                mock_llm = MagicMock()
                mock_llm.model_name = "gpt-4o-mini"
                mock_llm.temperature = 0.7
                mock_chat.return_value = mock_llm

                from agents.core.base_agent import BaseAgent

                agent = BaseAgent(
                    name="TestAgent",
                    role="Test",
                    goal="Testing"
                )

                # Agent should have a gateway
                assert agent.has_gateway() is True
                assert agent.gateway is not None

                # Gateway should be the singleton
                singleton_gateway = get_default_gateway()
                assert agent.gateway is singleton_gateway

            config_module._platform_config = None
            reset_default_gateway()

    def test_base_agent_uses_direct_llm_when_disabled(self):
        """Verify BaseAgent uses direct ChatOpenAI when flag is disabled."""
        with patch.dict(os.environ, {
            "BHT_USE_CENTRALIZED_GATEWAY": "false",
            "BHT_PLATFORM_ENABLED": "true",
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import reset_default_gateway
            reset_default_gateway()

            with patch('agents.core.base_agent.ChatOpenAI') as mock_chat:
                mock_llm = MagicMock()
                mock_chat.return_value = mock_llm

                from agents.core.base_agent import BaseAgent

                agent = BaseAgent(
                    name="TestAgent",
                    role="Test",
                    goal="Testing"
                )

                # Agent should NOT have a gateway
                assert agent.has_gateway() is False
                assert agent.gateway is None

                # Should have created ChatOpenAI directly
                mock_chat.assert_called_once()

            config_module._platform_config = None

    def test_explicit_gateway_overrides_centralized(self):
        """Verify explicitly provided gateway takes priority."""
        with patch.dict(os.environ, {
            "BHT_USE_CENTRALIZED_GATEWAY": "true",
            "BHT_PLATFORM_ENABLED": "true",
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, reset_default_gateway, get_default_gateway
            reset_default_gateway()

            # Create explicit gateway
            mock_llm = MagicMock()
            mock_llm.model_name = "gpt-4o-mini"
            mock_llm.temperature = 0.7
            explicit_gateway = ModelGateway(llm=mock_llm)

            from agents.core.base_agent import BaseAgent

            agent = BaseAgent(
                name="TestAgent",
                role="Test",
                goal="Testing",
                gateway=explicit_gateway
            )

            # Agent should use explicit gateway, not singleton
            assert agent.has_gateway() is True
            assert agent.gateway is explicit_gateway
            assert agent.gateway is not get_default_gateway()

            config_module._platform_config = None
            reset_default_gateway()


class TestAuditLoggingIntegration:
    """Tests verifying audit logs are created for all LLM calls."""

    def test_gateway_creates_audit_entry(self):
        """Verify gateway creates audit log entry for each call."""
        with patch.dict(os.environ, {"BHT_PLATFORM_ENABLED": "true"}):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.audit_context import AuditContext, _current_audit_context
            reset_default_gateway()

            mock_llm = MagicMock()
            mock_llm.model_name = "gpt-4o-mini"
            mock_llm.temperature = 0.7
            mock_response = MagicMock()
            mock_response.content = "Hello!"
            mock_llm.invoke.return_value = mock_response

            gateway = ModelGateway(llm=mock_llm)
            ctx = AuditContext.create(workflow_id="test_workflow")

            gateway.invoke("Test prompt", audit_context=ctx)

            entries = ctx.get_audit_trail()
            assert len(entries) == 1
            assert entries[0]["type"] == "llm_call"
            assert entries[0]["model"] == "gpt-4o-mini"
            assert entries[0]["workflow_id"] == "test_workflow"
            assert entries[0]["trace_id"] == ctx.trace_id
            assert entries[0]["success"] is True

            _current_audit_context.set(None)
            config_module._platform_config = None

    def test_multiple_calls_logged(self):
        """Verify multiple LLM calls are all logged."""
        with patch.dict(os.environ, {"BHT_PLATFORM_ENABLED": "true"}):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.audit_context import AuditContext, _current_audit_context
            reset_default_gateway()

            mock_llm = MagicMock()
            mock_llm.model_name = "gpt-4o-mini"
            mock_llm.temperature = 0.7
            mock_response = MagicMock()
            mock_response.content = "Response"
            mock_llm.invoke.return_value = mock_response

            gateway = ModelGateway(llm=mock_llm)
            ctx = AuditContext.create(workflow_id="multi_call_test")

            # Make 3 calls
            gateway.invoke("First", audit_context=ctx)
            gateway.invoke("Second", audit_context=ctx)
            gateway.invoke("Third", audit_context=ctx)

            entries = ctx.get_audit_trail()
            assert len(entries) == 3

            for entry in entries:
                assert entry["type"] == "llm_call"
                assert entry["trace_id"] == ctx.trace_id
                assert entry["workflow_id"] == "multi_call_test"

            _current_audit_context.set(None)
            config_module._platform_config = None


class TestNoDirectChatOpenAI:
    """Tests verifying direct ChatOpenAI usage is bypassed when gateway active."""

    def test_gateway_wraps_all_calls(self):
        """Verify all calls go through gateway, not direct LLM."""
        with patch.dict(os.environ, {
            "BHT_USE_CENTRALIZED_GATEWAY": "true",
            "BHT_PLATFORM_ENABLED": "true",
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import reset_default_gateway

            # Track if gateway's invoke is called vs direct LLM
            invoke_tracker = {"gateway_invoke": 0, "direct_llm": 0}

            original_invoke = None

            def track_invoke(self, *args, **kwargs):
                invoke_tracker["gateway_invoke"] += 1
                return original_invoke(self, *args, **kwargs)

            with patch('platform.model_gateway.ChatOpenAI') as mock_chat:
                mock_llm = MagicMock()
                mock_llm.model_name = "gpt-4o-mini"
                mock_llm.temperature = 0.7
                mock_response = MagicMock()
                mock_response.content = "Response"
                mock_llm.invoke.return_value = mock_response
                mock_chat.return_value = mock_llm

                reset_default_gateway()

                from platform.model_gateway import ModelGateway, get_default_gateway
                from platform.audit_context import AuditContext, _current_audit_context

                gateway = get_default_gateway()
                ctx = AuditContext.create(workflow_id="test")

                # Call via gateway
                gateway.invoke("Test", audit_context=ctx)

                # Underlying LLM should have been called once
                assert mock_llm.invoke.call_count == 1

                # Audit should have entry
                entries = ctx.get_audit_trail()
                assert len(entries) == 1

                _current_audit_context.set(None)

            config_module._platform_config = None
            reset_default_gateway()


class TestDefaultFlagsProduction:
    """Verify production-safe defaults."""

    def test_centralized_gateway_disabled_by_default(self):
        """Verify centralized gateway is disabled by default (production safe)."""
        # Clear all BHT env vars
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("BHT_")}

        with patch.dict(os.environ, clean_env, clear=True):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.config import get_platform_config

            config = get_platform_config()

            # Should be disabled by default
            assert config.use_centralized_gateway is False

            config_module._platform_config = None

    def test_all_reliability_features_disabled_by_default(self):
        """Verify all reliability features are off by default."""
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("BHT_")}

        with patch.dict(os.environ, clean_env, clear=True):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.config import get_platform_config

            config = get_platform_config()

            assert config.model_timeout_enabled is False
            assert config.model_retry_enabled is False
            assert config.circuit_breaker_enabled is False
            assert config.use_centralized_gateway is False

            config_module._platform_config = None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
