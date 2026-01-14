#!/usr/bin/env bash
# =============================================================================
# BHT Platform - Audit Correlation Smoke Test
#
# Runs the full smoke test using Docker Compose:
# 1. Builds and starts the API service
# 2. Waits for health check
# 3. Sends /chat request via smoke-test container
# 4. Captures and validates audit logs
# 5. Cleans up
#
# Usage:
#   ./scripts/run_smoke_test.sh
#   OPENAI_API_KEY=sk-xxx ./scripts/run_smoke_test.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_step() {
    echo -e "${YELLOW}=== $1 ===${NC}"
}

echo_pass() {
    echo -e "${GREEN}✓ $1${NC}"
}

echo_fail() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo_fail "OPENAI_API_KEY environment variable is required"
    echo "Usage: OPENAI_API_KEY=sk-xxx ./scripts/run_smoke_test.sh"
    exit 1
fi

# Cleanup function
cleanup() {
    echo_step "Cleanup"
    docker compose down --remove-orphans 2>/dev/null || true
}
trap cleanup EXIT

# Step 1: Build the API image
echo_step "Step 1: Building API image"
docker compose build agent-api

# Step 2: Start API service (detached)
echo_step "Step 2: Starting API service"
docker compose up -d agent-api

# Step 3: Wait for health check
echo_step "Step 3: Waiting for API to be healthy"
MAX_WAIT=120
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker compose ps agent-api | grep -q "healthy"; then
        echo_pass "API is healthy"
        break
    fi
    echo "Waiting for API health... ($WAITED/$MAX_WAIT seconds)"
    sleep 5
    WAITED=$((WAITED + 5))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo_fail "API did not become healthy within $MAX_WAIT seconds"
    docker compose logs agent-api
    exit 1
fi

# Step 4: Run smoke test
echo_step "Step 4: Running smoke test"
docker compose --profile test run --rm smoke-test

# Step 5: Extract and validate audit logs
echo_step "Step 5: Extracting audit logs"
AUDIT_LOG=$(docker compose logs agent-api 2>&1)

# Save logs for inspection
echo "$AUDIT_LOG" > /tmp/docker_audit.log

# Extract JSON audit entries
echo "$AUDIT_LOG" | grep '^{' > /tmp/audit_entries.jsonl 2>/dev/null || true

# Count entries
ENTRY_COUNT=$(wc -l < /tmp/audit_entries.jsonl | tr -d ' ')
echo "Total audit entries: $ENTRY_COUNT"

if [ "$ENTRY_COUNT" -lt 2 ]; then
    echo_fail "Expected at least 2 audit entries (api_request + llm_call)"
    echo "Full logs:"
    cat /tmp/docker_audit.log
    exit 1
fi

# Step 6: Validate trace correlation
echo_step "Step 6: Validating trace correlation"

# Get unique trace_ids
echo "Unique trace_ids:"
cat /tmp/audit_entries.jsonl | jq -r '.trace_id' | sort | uniq -c

# Get unique operations
echo ""
echo "Unique operations:"
cat /tmp/audit_entries.jsonl | jq -r '.operation' | sort | uniq

# Find the /chat request trace_id
CHAT_TRACE_ID=$(cat /tmp/audit_entries.jsonl | jq -r 'select(.endpoint == "/chat") | .trace_id' | head -1)

if [ -z "$CHAT_TRACE_ID" ]; then
    echo_fail "Could not find /chat request in audit logs"
    exit 1
fi

echo ""
echo "Trace ID for /chat: $CHAT_TRACE_ID"

# Check if llm_call shares the same trace_id
LLM_CALL_COUNT=$(cat /tmp/audit_entries.jsonl | jq -r "select(.trace_id == \"$CHAT_TRACE_ID\" and .operation == \"llm_call\") | .trace_id" | wc -l | tr -d ' ')
API_REQUEST_COUNT=$(cat /tmp/audit_entries.jsonl | jq -r "select(.trace_id == \"$CHAT_TRACE_ID\" and .operation == \"api_request\") | .trace_id" | wc -l | tr -d ' ')

echo ""
echo "Entries with trace_id $CHAT_TRACE_ID:"
echo "  - api_request: $API_REQUEST_COUNT"
echo "  - llm_call: $LLM_CALL_COUNT"

# Step 7: Final validation
echo_step "Step 7: Final validation"

if [ "$API_REQUEST_COUNT" -ge 1 ] && [ "$LLM_CALL_COUNT" -ge 1 ]; then
    echo_pass "SMOKE TEST PASSED: api_request and llm_call share the same trace_id"
    echo ""
    echo "Correlated entries:"
    cat /tmp/audit_entries.jsonl | jq "select(.trace_id == \"$CHAT_TRACE_ID\")"
    exit 0
else
    echo_fail "SMOKE TEST FAILED: api_request and llm_call do not share the same trace_id"
    echo ""
    echo "All audit entries:"
    cat /tmp/audit_entries.jsonl | jq .
    exit 1
fi
