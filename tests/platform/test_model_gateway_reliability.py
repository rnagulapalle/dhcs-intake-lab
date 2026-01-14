"""
Unit tests for ModelGateway Phase 1 reliability features.

Tests:
- Retry disabled by default (single attempt)
- Retry enabled with exponential backoff
- Timeout enforcement
- Circuit breaker behavior
- Audit logging with new fields (retries, error_type)
"""
import os
import time
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestRetryDisabledByDefault:
    """Tests verifying retry is disabled by default."""

    def test_retry_disabled_single_attempt(self):
        """Verify single attempt when retry is disabled (default)."""
        with patch.dict(os.environ, {"BHT_MODEL_RETRY_ENABLED": "false"}):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.audit_context import AuditContext, _current_audit_context
            from platform.errors import ModelGatewayError

            reset_default_gateway()

            # Setup mock LLM that fails
            mock_llm = MagicMock()
            mock_llm.model_name = "gpt-4o-mini"
            mock_llm.temperature = 0.7
            mock_llm.invoke.side_effect = Exception("API Error")

            gateway = ModelGateway(llm=mock_llm)
            ctx = AuditContext.create(workflow_id="test")

            # Should fail immediately without retries
            with pytest.raises(ModelGatewayError):
                gateway.invoke("Hello", audit_context=ctx)

            # Verify only one call was made
            assert mock_llm.invoke.call_count == 1

            # Verify audit log shows 0 retries
            entries = ctx.get_audit_trail()
            assert len(entries) == 1
            assert entries[0]["retries"] == 0

            _current_audit_context.set(None)
            config_module._platform_config = None


class TestRetryEnabled:
    """Tests verifying retry behavior when enabled."""

    def test_retry_enabled_retries_on_transient_error(self):
        """Verify retries happen on transient errors when enabled."""
        with patch.dict(os.environ, {
            "BHT_MODEL_RETRY_ENABLED": "true",
            "BHT_MAX_RETRIES": "2",
            "BHT_RETRY_BASE_DELAY": "0.01",  # Fast for testing
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.audit_context import AuditContext, _current_audit_context
            from platform.errors import ModelRetryExhaustedError

            reset_default_gateway()

            mock_llm = MagicMock()
            mock_llm.model_name = "gpt-4o-mini"
            mock_llm.temperature = 0.7
            # Fail with rate limit error (retryable)
            mock_llm.invoke.side_effect = Exception("Rate limit exceeded")

            gateway = ModelGateway(llm=mock_llm)
            ctx = AuditContext.create(workflow_id="test")

            with pytest.raises(ModelRetryExhaustedError) as exc_info:
                gateway.invoke("Hello", audit_context=ctx)

            # Should have made 3 attempts (1 initial + 2 retries)
            assert mock_llm.invoke.call_count == 3
            assert "3 attempts" in str(exc_info.value)

            # Verify audit log shows retries
            entries = ctx.get_audit_trail()
            assert len(entries) == 1
            assert entries[0]["retries"] == 2

            _current_audit_context.set(None)
            config_module._platform_config = None

    def test_retry_succeeds_on_second_attempt(self):
        """Verify retry can succeed on later attempt."""
        with patch.dict(os.environ, {
            "BHT_MODEL_RETRY_ENABLED": "true",
            "BHT_MAX_RETRIES": "3",
            "BHT_RETRY_BASE_DELAY": "0.01",
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.audit_context import AuditContext, _current_audit_context

            reset_default_gateway()

            mock_llm = MagicMock()
            mock_llm.model_name = "gpt-4o-mini"
            mock_llm.temperature = 0.7

            # Fail first, succeed second
            mock_response = MagicMock()
            mock_response.content = "Success!"
            mock_llm.invoke.side_effect = [
                Exception("Rate limit exceeded"),
                mock_response,
            ]

            gateway = ModelGateway(llm=mock_llm)
            ctx = AuditContext.create(workflow_id="test")

            result = gateway.invoke("Hello", audit_context=ctx)

            assert result.success is True
            assert result.content == "Success!"
            assert result.retries == 1
            assert mock_llm.invoke.call_count == 2

            _current_audit_context.set(None)
            config_module._platform_config = None

    def test_retry_not_on_auth_error(self):
        """Verify no retry on non-retryable errors (auth)."""
        with patch.dict(os.environ, {
            "BHT_MODEL_RETRY_ENABLED": "true",
            "BHT_MAX_RETRIES": "3",
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.audit_context import AuditContext, _current_audit_context
            from platform.errors import ModelGatewayError

            reset_default_gateway()

            mock_llm = MagicMock()
            mock_llm.model_name = "gpt-4o-mini"
            mock_llm.temperature = 0.7
            mock_llm.invoke.side_effect = Exception("Invalid API key")

            gateway = ModelGateway(llm=mock_llm)
            ctx = AuditContext.create(workflow_id="test")

            with pytest.raises(ModelGatewayError):
                gateway.invoke("Hello", audit_context=ctx)

            # Should only have one attempt (no retry on auth error)
            assert mock_llm.invoke.call_count == 1

            _current_audit_context.set(None)
            config_module._platform_config = None


class TestTimeoutEnabled:
    """Tests verifying timeout enforcement when enabled."""

    def test_timeout_disabled_by_default(self):
        """Verify timeout is not enforced by default."""
        with patch.dict(os.environ, {"BHT_MODEL_TIMEOUT_ENABLED": "false"}):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.config import get_platform_config

            reset_default_gateway()
            config = get_platform_config()

            assert config.model_timeout_enabled is False

            config_module._platform_config = None

    def test_timeout_enabled_enforces_limit(self):
        """Verify timeout is enforced when enabled."""
        with patch.dict(os.environ, {
            "BHT_MODEL_TIMEOUT_ENABLED": "true",
            "BHT_DEFAULT_TIMEOUT": "0.1",  # 100ms for testing
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.audit_context import AuditContext, _current_audit_context
            from platform.errors import ModelTimeoutError

            reset_default_gateway()

            mock_llm = MagicMock()
            mock_llm.model_name = "gpt-4o-mini"
            mock_llm.temperature = 0.7

            # Simulate slow response
            def slow_invoke(*args, **kwargs):
                time.sleep(0.5)  # 500ms, longer than 100ms timeout
                return MagicMock(content="Response")

            mock_llm.invoke.side_effect = slow_invoke

            gateway = ModelGateway(llm=mock_llm)
            ctx = AuditContext.create(workflow_id="test")

            with pytest.raises(ModelTimeoutError):
                gateway.invoke("Hello", audit_context=ctx, timeout=0.1)

            # Verify audit log shows timeout error
            entries = ctx.get_audit_trail()
            assert len(entries) == 1
            assert entries[0]["success"] is False
            assert entries[0].get("error_type") == "timeout"

            _current_audit_context.set(None)
            config_module._platform_config = None


class TestCircuitBreaker:
    """Tests for circuit breaker behavior."""

    def test_circuit_breaker_disabled_by_default(self):
        """Verify circuit breaker is disabled by default."""
        with patch.dict(os.environ, {"BHT_CIRCUIT_BREAKER_ENABLED": "false"}):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.config import get_platform_config

            config = get_platform_config()
            assert config.circuit_breaker_enabled is False

            config_module._platform_config = None

    def test_circuit_breaker_opens_after_threshold(self):
        """Verify circuit breaker opens after failure threshold."""
        with patch.dict(os.environ, {
            "BHT_CIRCUIT_BREAKER_ENABLED": "true",
            "BHT_CB_THRESHOLD": "3",
            "BHT_CB_RECOVERY": "60",
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, CircuitState, reset_default_gateway
            from platform.audit_context import AuditContext, _current_audit_context
            from platform.errors import ModelGatewayError, CircuitBreakerOpenError

            reset_default_gateway()

            mock_llm = MagicMock()
            mock_llm.model_name = "gpt-4o-mini"
            mock_llm.temperature = 0.7
            mock_llm.invoke.side_effect = Exception("API Error")

            gateway = ModelGateway(llm=mock_llm)

            # Fail 3 times to open circuit
            for i in range(3):
                ctx = AuditContext.create(workflow_id=f"test_{i}")
                try:
                    gateway.invoke("Hello", audit_context=ctx)
                except ModelGatewayError:
                    pass
                _current_audit_context.set(None)

            # Circuit should now be open
            assert gateway._circuit_breaker.state == CircuitState.OPEN

            # Next call should fail immediately with CircuitBreakerOpenError
            ctx = AuditContext.create(workflow_id="test_blocked")
            with pytest.raises(CircuitBreakerOpenError):
                gateway.invoke("Hello", audit_context=ctx)

            # LLM should not have been called for the blocked request
            # (3 failures + 0 for blocked = 3 total)
            assert mock_llm.invoke.call_count == 3

            _current_audit_context.set(None)
            config_module._platform_config = None

    def test_circuit_breaker_recovers(self):
        """Verify circuit breaker recovers after timeout."""
        with patch.dict(os.environ, {
            "BHT_CIRCUIT_BREAKER_ENABLED": "true",
            "BHT_CB_THRESHOLD": "2",
            "BHT_CB_RECOVERY": "0.1",  # 100ms for testing
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, CircuitState, reset_default_gateway
            from platform.audit_context import AuditContext, _current_audit_context
            from platform.errors import ModelGatewayError

            reset_default_gateway()

            mock_llm = MagicMock()
            mock_llm.model_name = "gpt-4o-mini"
            mock_llm.temperature = 0.7

            # First 2 calls fail, then succeed
            mock_response = MagicMock()
            mock_response.content = "Recovered!"
            mock_llm.invoke.side_effect = [
                Exception("API Error"),
                Exception("API Error"),
                mock_response,
            ]

            gateway = ModelGateway(llm=mock_llm)

            # Fail 2 times to open circuit
            for i in range(2):
                ctx = AuditContext.create(workflow_id=f"test_{i}")
                try:
                    gateway.invoke("Hello", audit_context=ctx)
                except ModelGatewayError:
                    pass
                _current_audit_context.set(None)

            assert gateway._circuit_breaker.state == CircuitState.OPEN

            # Wait for recovery timeout
            time.sleep(0.15)

            # Circuit should now be half-open
            assert gateway._circuit_breaker.state == CircuitState.HALF_OPEN

            # Next call should succeed and close circuit
            ctx = AuditContext.create(workflow_id="test_recovery")
            result = gateway.invoke("Hello", audit_context=ctx)

            assert result.success is True
            assert result.content == "Recovered!"
            assert gateway._circuit_breaker.state == CircuitState.CLOSED

            _current_audit_context.set(None)
            config_module._platform_config = None


class TestAuditLogging:
    """Tests for audit logging with Phase 1 fields."""

    def test_audit_logs_retries(self):
        """Verify audit logs include retry count."""
        with patch.dict(os.environ, {
            "BHT_MODEL_RETRY_ENABLED": "true",
            "BHT_MAX_RETRIES": "2",
            "BHT_RETRY_BASE_DELAY": "0.01",
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.audit_context import AuditContext, _current_audit_context

            reset_default_gateway()

            mock_llm = MagicMock()
            mock_llm.model_name = "gpt-4o-mini"
            mock_llm.temperature = 0.7

            mock_response = MagicMock()
            mock_response.content = "Success"
            mock_llm.invoke.side_effect = [
                Exception("Rate limit"),
                Exception("Rate limit"),
                mock_response,
            ]

            gateway = ModelGateway(llm=mock_llm)
            ctx = AuditContext.create(workflow_id="test")

            result = gateway.invoke("Hello", audit_context=ctx)

            entries = ctx.get_audit_trail()
            assert len(entries) == 1
            assert entries[0]["retries"] == 2
            assert entries[0]["success"] is True

            _current_audit_context.set(None)
            config_module._platform_config = None

    def test_audit_logs_error_type(self):
        """Verify audit logs include error type classification."""
        with patch.dict(os.environ, {"BHT_MODEL_RETRY_ENABLED": "false"}):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.model_gateway import ModelGateway, reset_default_gateway
            from platform.audit_context import AuditContext, _current_audit_context
            from platform.errors import ModelGatewayError

            reset_default_gateway()

            mock_llm = MagicMock()
            mock_llm.model_name = "gpt-4o-mini"
            mock_llm.temperature = 0.7
            mock_llm.invoke.side_effect = Exception("Connection refused")

            gateway = ModelGateway(llm=mock_llm)
            ctx = AuditContext.create(workflow_id="test")

            with pytest.raises(ModelGatewayError):
                gateway.invoke("Hello", audit_context=ctx)

            entries = ctx.get_audit_trail()
            assert len(entries) == 1
            assert entries[0]["error_type"] == "connection_error"
            assert entries[0]["success"] is False

            _current_audit_context.set(None)
            config_module._platform_config = None


class TestDefaultBehaviorPreserved:
    """Tests verifying Phase 0 behavior is preserved by default."""

    def test_default_flags_disabled(self):
        """Verify all reliability features are disabled by default."""
        # Clear any existing config
        import platform.config as config_module
        config_module._platform_config = None

        # Remove any env vars that might enable features
        env_clean = {k: v for k, v in os.environ.items()
                     if not k.startswith("BHT_MODEL_") and not k.startswith("BHT_CIRCUIT")}

        with patch.dict(os.environ, env_clean, clear=True):
            config_module._platform_config = None

            from platform.config import get_platform_config

            config = get_platform_config()

            # All should be disabled by default
            assert config.model_timeout_enabled is False
            assert config.model_retry_enabled is False
            assert config.circuit_breaker_enabled is False

            config_module._platform_config = None

    def test_gateway_works_with_all_disabled(self):
        """Verify gateway works normally with all features disabled."""
        with patch.dict(os.environ, {
            "BHT_MODEL_TIMEOUT_ENABLED": "false",
            "BHT_MODEL_RETRY_ENABLED": "false",
            "BHT_CIRCUIT_BREAKER_ENABLED": "false",
        }):
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
            ctx = AuditContext.create(workflow_id="test")

            result = gateway.invoke("Hello", audit_context=ctx)

            assert result.success is True
            assert result.content == "Hello!"
            assert result.retries == 0
            assert mock_llm.invoke.call_count == 1

            _current_audit_context.set(None)
            config_module._platform_config = None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
