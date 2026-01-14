"""
Backward Compatibility Tests for BHT Platform Phase 0

These tests verify that Phase 0 changes are:
1. Behavior-preserving: Core response fields remain unchanged
2. Additive-only: _trace is the only new field (when enabled)
3. Rollback-safe: Platform can be disabled via single flag

Golden Response Tests:
- Capture expected response schemas
- Verify no breaking changes to existing consumers
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestResponseSchemaPreservation:
    """
    Golden response tests to verify backward compatibility.

    These tests capture the expected response structure for critical endpoints
    and verify no breaking changes are introduced.
    """

    @pytest.fixture
    def client_with_platform_disabled(self):
        """Test client with platform fully disabled."""
        with patch.dict(os.environ, {"BHT_PLATFORM_ENABLED": "false"}):
            # Force config reload
            import platform.config as config_module
            config_module._platform_config = None

            from api.main import app
            yield TestClient(app)

            # Reset
            config_module._platform_config = None

    @pytest.fixture
    def client_with_trace_disabled(self):
        """Test client with platform enabled but _trace disabled (default)."""
        with patch.dict(os.environ, {
            "BHT_PLATFORM_ENABLED": "true",
            "BHT_INCLUDE_TRACE_IN_RESPONSE": "false"
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from api.main import app
            yield TestClient(app)

            config_module._platform_config = None

    @pytest.fixture
    def client_with_trace_enabled(self):
        """Test client with _trace enabled."""
        with patch.dict(os.environ, {
            "BHT_PLATFORM_ENABLED": "true",
            "BHT_INCLUDE_TRACE_IN_RESPONSE": "true"
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from api.main import app
            yield TestClient(app)

            config_module._platform_config = None

    # =========================================================================
    # GOLDEN RESPONSE: /health endpoint
    # =========================================================================

    HEALTH_GOLDEN_KEYS = {"status", "timestamp", "service"}

    def test_health_golden_response_platform_disabled(self, client_with_platform_disabled):
        """Verify /health response matches golden schema when platform disabled."""
        response = client_with_platform_disabled.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Must have all golden keys
        assert self.HEALTH_GOLDEN_KEYS.issubset(data.keys())

        # Must NOT have _trace when platform disabled
        assert "_trace" not in data

        # Verify golden values
        assert data["status"] == "healthy"
        assert data["service"] == "DHCS BHT Multi-Agent API"

    def test_health_golden_response_trace_disabled(self, client_with_trace_disabled):
        """Verify /health response matches golden schema when trace disabled."""
        response = client_with_trace_disabled.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Must have all golden keys
        assert self.HEALTH_GOLDEN_KEYS.issubset(data.keys())

        # Must NOT have _trace when trace disabled
        assert "_trace" not in data

        # Headers should still have trace (middleware active)
        assert "X-Trace-Id" in response.headers

    def test_health_golden_response_trace_enabled(self, client_with_trace_enabled):
        """Verify /health response has _trace when enabled."""
        response = client_with_trace_enabled.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Must have all golden keys PLUS _trace
        assert self.HEALTH_GOLDEN_KEYS.issubset(data.keys())
        assert "_trace" in data

        # Verify _trace structure
        trace = data["_trace"]
        assert "trace_id" in trace
        assert "request_id" in trace
        assert "workflow_id" in trace
        assert len(trace["trace_id"]) == 36  # UUID format

    # =========================================================================
    # GOLDEN RESPONSE: Response headers
    # =========================================================================

    def test_headers_absent_when_platform_disabled(self, client_with_platform_disabled):
        """Verify X-Trace-Id headers are absent when platform disabled."""
        response = client_with_platform_disabled.get("/health")

        # Should NOT have trace headers
        assert "X-Trace-Id" not in response.headers
        assert "X-Request-Id" not in response.headers

    def test_headers_present_when_platform_enabled(self, client_with_trace_disabled):
        """Verify X-Trace-Id headers are present when platform enabled."""
        response = client_with_trace_disabled.get("/health")

        # Should have trace headers (even if _trace in body is disabled)
        assert "X-Trace-Id" in response.headers
        assert "X-Request-Id" in response.headers

        # Verify UUID format
        trace_id = response.headers["X-Trace-Id"]
        assert len(trace_id) == 36

    def test_trace_id_propagation_works(self, client_with_trace_enabled):
        """Verify incoming X-Trace-Id is propagated."""
        custom_trace = "12345678-1234-5678-1234-567812345678"

        response = client_with_trace_enabled.get(
            "/health",
            headers={"X-Trace-Id": custom_trace}
        )

        # Header should match
        assert response.headers["X-Trace-Id"] == custom_trace

        # Body _trace should match
        data = response.json()
        assert data["_trace"]["trace_id"] == custom_trace


class TestRollbackSafety:
    """
    Tests to verify single-flag rollback capability.

    Setting BHT_PLATFORM_ENABLED=false must:
    1. Disable middleware (no-op pass-through)
    2. Remove _trace from all responses
    3. Remove X-Trace-Id headers
    4. Preserve all other behavior
    """

    def test_single_flag_disables_all_platform_features(self):
        """Verify BHT_PLATFORM_ENABLED=false disables everything."""
        with patch.dict(os.environ, {"BHT_PLATFORM_ENABLED": "false"}):
            import platform.config as config_module
            config_module._platform_config = None

            from platform.config import get_platform_config
            config = get_platform_config()

            assert config.platform_enabled is False

            config_module._platform_config = None

    def test_middleware_is_noop_when_disabled(self):
        """Verify middleware passes through when platform disabled."""
        with patch.dict(os.environ, {"BHT_PLATFORM_ENABLED": "false"}):
            import platform.config as config_module
            config_module._platform_config = None

            from api.main import app
            client = TestClient(app)

            # Multiple requests should work without trace context
            r1 = client.get("/health")
            r2 = client.get("/health")

            assert r1.status_code == 200
            assert r2.status_code == 200
            assert "_trace" not in r1.json()
            assert "_trace" not in r2.json()

            config_module._platform_config = None


class TestFeatureFlagDefaults:
    """
    Tests to verify default values for feature flags.

    Production-safe defaults:
    - BHT_PLATFORM_ENABLED: true (platform is active)
    - BHT_INCLUDE_TRACE_IN_RESPONSE: false (no response body changes)
    """

    def test_default_platform_enabled(self):
        """Verify platform is enabled by default."""
        # Clear any existing env var
        env = os.environ.copy()
        if "BHT_PLATFORM_ENABLED" in env:
            del env["BHT_PLATFORM_ENABLED"]

        with patch.dict(os.environ, {}, clear=True):
            # Set required env vars but not platform flags
            os.environ.update({k: v for k, v in env.items() if not k.startswith("BHT_")})

            import platform.config as config_module
            config_module._platform_config = None

            from platform.config import get_platform_config
            config = get_platform_config()

            # Default should be enabled
            assert config.platform_enabled is True

            config_module._platform_config = None

    def test_default_trace_in_response_disabled(self):
        """Verify _trace is NOT added to responses by default."""
        env = os.environ.copy()

        with patch.dict(os.environ, {}, clear=True):
            os.environ.update({k: v for k, v in env.items() if not k.startswith("BHT_")})

            import platform.config as config_module
            config_module._platform_config = None

            from platform.config import get_platform_config
            config = get_platform_config()

            # Default should be disabled (backward compatible)
            assert config.include_trace_in_response is False

            config_module._platform_config = None


class TestEndpointConsistency:
    """
    Tests to verify all endpoints behave consistently with flags.
    """

    @pytest.fixture
    def client(self):
        """Standard test client."""
        with patch.dict(os.environ, {
            "BHT_PLATFORM_ENABLED": "true",
            "BHT_INCLUDE_TRACE_IN_RESPONSE": "false"
        }):
            import platform.config as config_module
            config_module._platform_config = None

            from api.main import app
            yield TestClient(app)

            config_module._platform_config = None

    def test_all_endpoints_consistent_no_trace(self, client):
        """Verify no endpoint adds _trace when disabled."""
        endpoints = [
            ("GET", "/health"),
            # POST endpoints would need mocking, tested separately
        ]

        for method, path in endpoints:
            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(path, json={})

            if response.status_code == 200:
                data = response.json()
                assert "_trace" not in data, f"Endpoint {path} should not have _trace"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
