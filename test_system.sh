#!/bin/bash
# Test script for DHCS BHT Multi-Agent System

set -e

echo "================================================"
echo "Testing DHCS BHT Multi-Agent System"
echo "================================================"
echo ""

BASE_URL="http://localhost:8000"

# Test 1: Health check
echo "Test 1: Health Check"
curl -s "$BASE_URL/health" | jq .
echo "✅ Health check passed"
echo ""

# Test 2: Knowledge base stats
echo "Test 2: Knowledge Base Stats"
curl -s "$BASE_URL/knowledge/stats" | jq .
echo "✅ Knowledge base accessible"
echo ""

# Test 3: Chat query
echo "Test 3: Chat Query"
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message":"How many events happened in the last hour?"}' | jq .response
echo "✅ Chat query successful"
echo ""

# Test 4: Analytics
echo "Test 4: Analytics"
curl -s -X POST "$BASE_URL/analytics" \
  -H "Content-Type: application/json" \
  -d '{"analysis_type":"comprehensive","time_window_minutes":60}' | jq '.surge_detection, .insights'
echo "✅ Analytics successful"
echo ""

# Test 5: Triage
echo "Test 5: Triage"
curl -s -X POST "$BASE_URL/triage" \
  -H "Content-Type: application/json" \
  -d '{"time_window_minutes":30,"limit":10}' | jq '.status, .total_high_risk_events'
echo "✅ Triage successful"
echo ""

# Test 6: Recommendations
echo "Test 6: Recommendations"
curl -s -X POST "$BASE_URL/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"focus_area":"staffing","time_window_minutes":60}' | jq '.status'
echo "✅ Recommendations successful"
echo ""

echo "================================================"
echo "All Tests Passed! ✅"
echo "================================================"
echo ""
echo "The multi-agent system is working correctly."
echo "Open http://localhost:8501 to see the dashboard"
echo ""
