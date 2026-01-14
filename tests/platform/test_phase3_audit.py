"""
Phase 3 Audit Tests: Mandatory fields, sink integration, and trace correlation.

Tests:
1. Contract tests: audit entries contain all mandatory fields
2. Sink tests: entries written correctly to stdout/file sinks
3. Integration tests: trace_id links LLM + retrieval + workflow steps
"""
import json
import os
import pytest
import tempfile
from io import StringIO
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from platform.audit_context import (
    AuditContext,
    AuditOperation,
    MANDATORY_AUDIT_FIELDS,
    WorkflowStepTimer,
    _current_audit_context,
)
from platform.audit_sink import (
    AuditSink,
    StdoutAuditSink,
    FileAuditSink,
    NullAuditSink,
    MultiAuditSink,
    validate_audit_entry,
    normalize_audit_entry,
    get_default_audit_sink,
    reset_default_audit_sink,
)


# =============================================================================
# Contract Tests: Mandatory Fields
# =============================================================================

class TestMandatoryFields:
    """Contract tests verifying all audit entries contain mandatory fields."""

    def setup_method(self):
        """Reset audit context before each test."""
        _current_audit_context.set(None)
        reset_default_audit_sink()

    def teardown_method(self):
        """Clean up after each test."""
        _current_audit_context.set(None)
        reset_default_audit_sink()

    def test_llm_call_has_mandatory_fields(self):
        """Verify LLM call audit entries contain all mandatory fields."""
        sink = NullAuditSink()
        ctx = AuditContext.create(workflow_id="test", sink=sink)

        ctx.log_llm_call(
            model="gpt-4o-mini",
            latency_ms=150.5,
            tokens=500,
            success=True
        )

        entries = ctx.get_audit_trail()
        assert len(entries) == 1

        entry = entries[0]
        missing = validate_audit_entry(entry)
        assert len(missing) == 0, f"Missing mandatory fields: {missing}"

        # Verify specific values
        assert entry["operation"] == AuditOperation.LLM_CALL
        assert entry["trace_id"] == ctx.trace_id
        assert entry["request_id"] == ctx.request_id
        assert entry["workflow_id"] == "test"
        assert entry["latency_ms"] == 150.5
        assert entry["success"] is True

    def test_retrieval_has_mandatory_fields(self):
        """Verify retrieval audit entries contain all mandatory fields."""
        sink = NullAuditSink()
        ctx = AuditContext.create(workflow_id="test", sink=sink)

        ctx.log_retrieval(
            query_length=50,
            n_results=5,
            latency_ms=75.0,
            success=True
        )

        entries = ctx.get_audit_trail()
        entry = entries[0]

        missing = validate_audit_entry(entry)
        assert len(missing) == 0, f"Missing mandatory fields: {missing}"
        assert entry["operation"] == AuditOperation.RETRIEVAL

    def test_workflow_step_has_mandatory_fields(self):
        """Verify workflow step audit entries contain all mandatory fields."""
        sink = NullAuditSink()
        ctx = AuditContext.create(workflow_id="test", sink=sink)

        ctx.log_workflow_step(
            step_name="evidence_extraction",
            latency_ms=200.0,
            success=True
        )

        entries = ctx.get_audit_trail()
        entry = entries[0]

        missing = validate_audit_entry(entry)
        assert len(missing) == 0, f"Missing mandatory fields: {missing}"
        assert entry["operation"] == AuditOperation.WORKFLOW_STEP

    def test_api_request_has_mandatory_fields(self):
        """Verify API request audit entries contain all mandatory fields."""
        sink = NullAuditSink()
        ctx = AuditContext.create(workflow_id="test", sink=sink)

        ctx.log_api_request(
            endpoint="/chat",
            method="POST",
            status_code=200,
            latency_ms=500.0
        )

        entries = ctx.get_audit_trail()
        entry = entries[0]

        missing = validate_audit_entry(entry)
        assert len(missing) == 0, f"Missing mandatory fields: {missing}"
        assert entry["operation"] == AuditOperation.API_REQUEST

    def test_error_fields_present_on_failure(self):
        """Verify error fields are present when operation fails."""
        sink = NullAuditSink()
        ctx = AuditContext.create(workflow_id="test", sink=sink)

        ctx.log_llm_call(
            model="gpt-4o-mini",
            latency_ms=5000.0,
            tokens=0,
            success=False,
            error="Request timed out",
            error_type="timeout"
        )

        entry = ctx.get_audit_trail()[0]
        assert entry["success"] is False
        assert entry["error"] == "Request timed out"
        assert entry["error_type"] == "timeout"


# =============================================================================
# Sink Tests
# =============================================================================

class TestStdoutAuditSink:
    """Tests for StdoutAuditSink."""

    def test_stdout_sink_writes_json(self, capsys):
        """Verify stdout sink writes valid JSON."""
        sink = StdoutAuditSink(pretty_print=False)

        entry = {
            "trace_id": "test-123",
            "request_id": "req-456",
            "workflow_id": "test",
            "operation": "llm_call",
            "latency_ms": 100.0,
            "success": True,
        }

        sink.write(entry)
        captured = capsys.readouterr()

        # Verify output is valid JSON
        parsed = json.loads(captured.out.strip())
        assert parsed["trace_id"] == "test-123"
        assert parsed["operation"] == "llm_call"

    def test_stdout_sink_normalizes_entry(self, capsys):
        """Verify stdout sink normalizes entries (adds timestamp, etc.)."""
        sink = StdoutAuditSink()

        entry = {
            "trace_id": "test-123",
            "request_id": "req-456",
            "workflow_id": "test",
            "type": "llm_call",  # Legacy field name
            "latency_ms": 100.0,
            "success": True,
        }

        sink.write(entry)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())

        # Should have both 'type' and 'operation'
        assert parsed["operation"] == "llm_call"
        assert "timestamp" in parsed


class TestFileAuditSink:
    """Tests for FileAuditSink."""

    def test_file_sink_writes_jsonl(self):
        """Verify file sink writes JSON lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            file_path = f.name

        try:
            sink = FileAuditSink(file_path)

            for i in range(3):
                sink.write({
                    "trace_id": f"test-{i}",
                    "request_id": f"req-{i}",
                    "workflow_id": "test",
                    "operation": "llm_call",
                    "latency_ms": 100.0 + i,
                    "success": True,
                })

            sink.close()

            # Read and verify
            with open(file_path, 'r') as f:
                lines = f.readlines()

            assert len(lines) == 3
            for i, line in enumerate(lines):
                parsed = json.loads(line)
                assert parsed["trace_id"] == f"test-{i}"

        finally:
            os.unlink(file_path)

    def test_file_sink_appends_by_default(self):
        """Verify file sink appends to existing file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            file_path = f.name
            f.write('{"existing": "entry"}\n')

        try:
            sink = FileAuditSink(file_path, append=True)
            sink.write({
                "trace_id": "new",
                "request_id": "req",
                "workflow_id": "test",
                "operation": "llm_call",
                "latency_ms": 100.0,
                "success": True,
            })
            sink.close()

            with open(file_path, 'r') as f:
                lines = f.readlines()

            assert len(lines) == 2
            assert "existing" in lines[0]
            assert "new" in lines[1]

        finally:
            os.unlink(file_path)


class TestMultiAuditSink:
    """Tests for MultiAuditSink."""

    def test_multi_sink_writes_to_all(self):
        """Verify multi sink writes to all child sinks."""
        entries1 = []
        entries2 = []

        class CaptureSink(AuditSink):
            def __init__(self, storage):
                self.storage = storage
            def write(self, entry):
                self.storage.append(entry)
            def flush(self):
                pass
            def close(self):
                pass

        sink1 = CaptureSink(entries1)
        sink2 = CaptureSink(entries2)

        multi = MultiAuditSink([sink1, sink2])
        multi.write({"trace_id": "test", "operation": "test"})

        assert len(entries1) == 1
        assert len(entries2) == 1
        assert entries1[0]["trace_id"] == "test"


# =============================================================================
# Integration Tests: Trace Correlation
# =============================================================================

class TestTraceCorrelation:
    """Integration tests verifying trace_id links all operations."""

    def setup_method(self):
        _current_audit_context.set(None)
        reset_default_audit_sink()

    def teardown_method(self):
        _current_audit_context.set(None)
        reset_default_audit_sink()

    def test_single_trace_links_all_operations(self):
        """Verify single trace_id links LLM + retrieval + workflow steps."""
        sink = NullAuditSink()

        with AuditContext.create(workflow_id="curation", tenant_id="county_la", sink=sink) as ctx:
            # Simulate workflow step
            ctx.log_workflow_step(
                step_name="intent_classification",
                latency_ms=50.0,
                success=True
            )

            # Simulate retrieval
            ctx.log_retrieval(
                query_length=45,
                n_results=5,
                latency_ms=100.0
            )

            # Simulate LLM call
            ctx.log_llm_call(
                model="gpt-4o-mini",
                latency_ms=200.0,
                tokens=500
            )

            # Verify all entries share same trace_id
            entries = ctx.get_audit_trail()
            assert len(entries) == 3

            trace_ids = set(e["trace_id"] for e in entries)
            assert len(trace_ids) == 1, "All entries should share same trace_id"

            request_ids = set(e["request_id"] for e in entries)
            assert len(request_ids) == 1, "All entries should share same request_id"

            # Verify operation types
            operations = [e["operation"] for e in entries]
            assert AuditOperation.WORKFLOW_STEP in operations
            assert AuditOperation.RETRIEVAL in operations
            assert AuditOperation.LLM_CALL in operations

    def test_workflow_step_timer_logs_with_trace(self):
        """Verify WorkflowStepTimer logs with correct trace_id."""
        sink = NullAuditSink()

        with AuditContext.create(workflow_id="test", sink=sink) as ctx:
            with WorkflowStepTimer("evidence_extraction", audit_context=ctx) as step:
                step.set_metadata({"documents_processed": 5})
                step.set_output_summary("Extracted 5 requirements")

            entries = ctx.get_audit_trail()
            assert len(entries) == 1

            entry = entries[0]
            assert entry["step_name"] == "evidence_extraction"
            assert entry["trace_id"] == ctx.trace_id
            assert entry["step_metadata"]["documents_processed"] == 5

    def test_nested_workflow_steps_share_trace(self):
        """Verify nested workflow steps share the same trace_id."""
        sink = NullAuditSink()

        with AuditContext.create(workflow_id="curation", sink=sink) as ctx:
            with WorkflowStepTimer("outer_step") as outer:
                outer.set_metadata({"level": "outer"})

                with WorkflowStepTimer("inner_step") as inner:
                    inner.set_metadata({"level": "inner"})

            entries = ctx.get_audit_trail()
            assert len(entries) == 2

            # Both should have same trace_id
            assert entries[0]["trace_id"] == entries[1]["trace_id"]
            assert entries[0]["trace_id"] == ctx.trace_id


# =============================================================================
# API Request + Full Workflow Integration
# =============================================================================

class TestFullRequestFlow:
    """Integration test simulating a complete /chat request."""

    def setup_method(self):
        _current_audit_context.set(None)
        reset_default_audit_sink()

    def teardown_method(self):
        _current_audit_context.set(None)
        reset_default_audit_sink()

    def test_chat_request_produces_expected_logs(self):
        """
        Simulate /chat request and verify:
        - At least one workflow_step log
        - At least one retrieval log (if retrieval used)
        - At least one llm_call log
        - All sharing the same trace_id
        """
        sink = NullAuditSink()

        with AuditContext.create(workflow_id="chat", tenant_id="demo", sink=sink) as ctx:
            # API request start
            import time
            start_time = time.time()

            # Step 1: Intent classification (workflow step + LLM)
            ctx.log_workflow_step(
                step_name="intent_classification",
                latency_ms=100.0,
                success=True,
                output_summary="intent=policy_question"
            )
            ctx.log_llm_call(
                model="gpt-4o-mini",
                latency_ms=100.0,
                tokens=200,
                operation="classify"
            )

            # Step 2: Retrieval
            ctx.log_retrieval(
                query_length=50,
                n_results=5,
                latency_ms=150.0
            )

            # Step 3: Response generation (workflow step + LLM)
            ctx.log_workflow_step(
                step_name="response_generation",
                latency_ms=300.0,
                success=True
            )
            ctx.log_llm_call(
                model="gpt-4o-mini",
                latency_ms=300.0,
                tokens=800
            )

            # API request end
            total_latency = (time.time() - start_time) * 1000
            ctx.log_api_request(
                endpoint="/chat",
                method="POST",
                status_code=200,
                latency_ms=total_latency
            )

            # Verify expectations
            entries = ctx.get_audit_trail()

            # At least one of each type
            operations = [e["operation"] for e in entries]
            assert operations.count(AuditOperation.WORKFLOW_STEP) >= 1
            assert operations.count(AuditOperation.RETRIEVAL) >= 1
            assert operations.count(AuditOperation.LLM_CALL) >= 1
            assert operations.count(AuditOperation.API_REQUEST) == 1

            # All share same trace_id
            trace_ids = set(e["trace_id"] for e in entries)
            assert len(trace_ids) == 1

            # All entries have mandatory fields
            for entry in entries:
                missing = validate_audit_entry(entry)
                assert len(missing) == 0, f"Entry missing fields: {missing}"


# =============================================================================
# Configuration Tests
# =============================================================================

class TestAuditConfiguration:
    """Tests for audit configuration flags."""

    def setup_method(self):
        _current_audit_context.set(None)
        reset_default_audit_sink()

    def teardown_method(self):
        _current_audit_context.set(None)
        reset_default_audit_sink()
        # Clean up env vars
        for key in ["BHT_AUDIT_SINK", "BHT_AUDIT_PRETTY_PRINT"]:
            os.environ.pop(key, None)

    def test_default_sink_is_stdout(self):
        """Verify default sink type is stdout."""
        os.environ.pop("BHT_AUDIT_SINK", None)
        reset_default_audit_sink()

        sink = get_default_audit_sink()
        assert isinstance(sink, StdoutAuditSink)

    def test_null_sink_configuration(self):
        """Verify null sink can be configured."""
        os.environ["BHT_AUDIT_SINK"] = "null"
        reset_default_audit_sink()

        sink = get_default_audit_sink()
        assert isinstance(sink, NullAuditSink)

    def test_prompt_logging_disabled_by_default(self):
        """Verify prompt/response logging is disabled by default."""
        sink = NullAuditSink()
        ctx = AuditContext.create(workflow_id="test", sink=sink)

        ctx.log_llm_call(
            model="gpt-4o-mini",
            latency_ms=100.0,
            tokens=500,
            prompt="Secret prompt",
            response="Secret response"
        )

        entry = ctx.get_audit_trail()[0]

        # Prompts should NOT be logged by default
        assert "prompt" not in entry
        assert "response" not in entry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
