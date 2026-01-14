# Getting Started with Policy Curation - Step-by-Step Guide

**For Engineers Setting Up the Multi-Agent Policy Curation System**

**Last Updated:** January 8, 2026
**System:** dhcs-intake-lab v0.2.0
**Estimated Setup Time:** 15-20 minutes

---

## Table of Contents

1. [Prerequisites Check](#prerequisites-check)
2. [Step 1: Copy Data Files](#step-1-copy-data-files)
3. [Step 2: Verify Environment](#step-2-verify-environment)
4. [Step 3: Run Data Migration](#step-3-run-data-migration)
5. [Step 4: Start Services](#step-4-start-services)
6. [Step 5: Test API Endpoints](#step-5-test-api-endpoints)
7. [Step 6: Process Test Questions](#step-6-process-test-questions)
8. [Step 7: Verify Quality](#step-7-verify-quality)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [What to Do If Something Fails](#what-to-do-if-something-fails)

---

## Prerequisites Check

Before starting, verify you have:

### ✅ Required Access

```bash
# 1. Verify you're in the correct directory
pwd
# Should output: /Users/raj/dhcs-intake-lab

# 2. Check prototype data location exists
ls -la /Users/raj/work/workspace/dhcs/agent-boiler-plate/src/rag_curation/data/
# Should see: BHSA_County_Policy_Manual.md and PreProcessRubric_v0.csv

# 3. Verify OpenAI API key is set
echo $OPENAI_API_KEY | cut -c1-10
# Should output: sk-proj-... or sk-...
# If empty, set it: export OPENAI_API_KEY="your-key-here"
```

### ✅ Required Tools

```bash
# Check Python version (should be 3.11+)
python3 --version
# OR if using venv:
source .venv/bin/activate && python --version

# Check Docker is running
docker ps
# Should list running containers without errors

# Check if API is accessible
curl http://localhost:8000/health 2>/dev/null
# If this works, services are already running
```

### ✅ Expected Directory Structure

Your dhcs-intake-lab should have these new files (created by the migration):

```
dhcs-intake-lab/
├── agents/
│   ├── core/
│   │   ├── retrieval_agent.py              ← NEW
│   │   ├── statute_analyst_agent.py        ← NEW
│   │   ├── policy_analyst_agent.py         ← NEW
│   │   ├── synthesis_agent.py              ← NEW
│   │   ├── quality_reviewer_agent.py       ← NEW
│   │   └── curation_orchestrator.py        ← NEW
│   └── knowledge/
│       └── curation_loader.py              ← NEW
├── api/
│   └── main.py                             ← MODIFIED (3 new endpoints)
├── scripts/
│   └── migrate_curation_data.py            ← NEW
├── data/                                    ← Will create in Step 1
├── CURATION_IMPLEMENTATION_GUIDE.md        ← Technical reference
└── GETTING_STARTED_CURATION.md            ← This file
```

**Verification:**
```bash
# Check new files exist
ls -l agents/core/curation_orchestrator.py
ls -l scripts/migrate_curation_data.py

# If files are missing, the migration wasn't completed
# Contact the engineer who did the migration
```

---

## Step 1: Copy Data Files

**Time:** 2 minutes
**Goal:** Copy policy manual and CSV data from prototype to production

### 1.1 Create Data Directory

```bash
cd /Users/raj/dhcs-intake-lab
mkdir -p data
```

### 1.2 Copy Policy Manual (472KB file)

```bash
cp /Users/raj/work/workspace/dhcs/agent-boiler-plate/src/rag_curation/data/BHSA_County_Policy_Manual.md \
   /Users/raj/dhcs-intake-lab/data/

# Verify copy succeeded
ls -lh data/BHSA_County_Policy_Manual.md
# Should show: -rw-r--r-- ... 472K ... BHSA_County_Policy_Manual.md
```

**✅ SUCCESS CHECK:**
```bash
wc -l data/BHSA_County_Policy_Manual.md
# Should output: 9255 (9,255 lines)
```

**❌ IF THIS FAILS:**
- Check source path exists: `ls /Users/raj/work/workspace/dhcs/agent-boiler-plate/src/rag_curation/data/`
- Check you have read permissions
- Try with sudo if needed: `sudo cp ...`

### 1.3 Copy CSV Questions (Optional - for batch testing)

```bash
cp /Users/raj/work/workspace/dhcs/agent-boiler-plate/src/rag_curation/data/PreProcessRubric_v0.csv \
   /Users/raj/dhcs-intake-lab/data/

# Verify
ls -lh data/PreProcessRubric_v0.csv
# Should show: -rw-r--r-- ... 392 rows
```

### 1.4 Verify Data Files

```bash
# Check both files are present
ls -lh data/
# Should output:
#   BHSA_County_Policy_Manual.md  (472K)
#   PreProcessRubric_v0.csv       (~300K)
```

**✅ STEP 1 COMPLETE** when both files exist in `/Users/raj/dhcs-intake-lab/data/`

---

## Step 2: Verify Environment

**Time:** 1 minute
**Goal:** Ensure Python environment and API key are configured

### 2.1 Check OpenAI API Key

```bash
# Verify API key is set
echo $OPENAI_API_KEY | head -c 20
# Should output: sk-proj-... or sk-...

# If empty, set it now:
export OPENAI_API_KEY="your-openai-api-key-here"

# Verify it's set correctly
echo $OPENAI_API_KEY | head -c 20
```

**❌ IF YOU DON'T HAVE AN API KEY:**
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy the key (starts with `sk-proj-` or `sk-`)
4. Export it: `export OPENAI_API_KEY="sk-..."`

### 2.2 Activate Virtual Environment (if using venv)

```bash
# Check if venv exists
ls -la .venv

# If it exists, activate it:
source .venv/bin/activate

# Verify activation (prompt should change)
which python
# Should output: /Users/raj/dhcs-intake-lab/.venv/bin/python
```

### 2.3 Verify Required Packages

```bash
python -c "import chromadb; print('chromadb:', chromadb.__version__)"
python -c "import langchain; print('langchain:', langchain.__version__)"
python -c "from langchain_openai import ChatOpenAI; print('OpenAI integration: OK')"

# All should succeed without errors
```

**❌ IF IMPORTS FAIL:**
```bash
pip install -r requirements.txt
# OR if in Docker:
docker-compose build agent-api
```

**✅ STEP 2 COMPLETE** when API key is set and imports work

---

## Step 3: Run Data Migration

**Time:** 3-5 minutes
**Goal:** Load policy manual and statutes into ChromaDB vector database

### 3.1 Run Migration Script

```bash
cd /Users/raj/dhcs-intake-lab
python scripts/migrate_curation_data.py
```

### 3.2 Expected Output

You should see this output (abbreviated):

```
================================================================================
POLICY CURATION DATA MIGRATION
================================================================================

================================================================================
STEP 1: Migrating Policy Manual
================================================================================
INFO - Loading policy manual from /Users/raj/dhcs-intake-lab/data/BHSA_County_Policy_Manual.md
INFO - Detected policy manual version: 1.3.0
INFO - Found 51 sections in policy manual
INFO - Created 387 policy document chunks (excluded 7 sections)
INFO - Added 387 chunks from 1 documents
✓ Policy manual migration complete: 387 chunks added

================================================================================
STEP 2: Migrating W&I Code Statutes
================================================================================
WARN - No statute file provided - loading placeholders
WARN - You should replace these with actual statute texts later
INFO - Created 155 statute chunks from 18 statutes
INFO - Added 155 chunks from 18 documents
✓ Statute migration complete: 155 chunks added

================================================================================
STEP 3: Verifying Migration
================================================================================
INFO - Verifying document loading
INFO - Knowledge base initialized with 542 documents
Migration Verification Results:
  Total Documents: 542
  Policy Documents: 387
  Statute Documents: 155
  Collection: dhcs_bht_knowledge

================================================================================
STEP 4: Testing Retrieval
================================================================================
Testing policy retrieval...
INFO - Found 3 results for query: workforce requirements for BHSA providers
✓ Policy retrieval working: Found 3 results
  Top result: Counties must implement cultural competency training...

Testing statute retrieval...
INFO - Found 3 results for query: W&I Code requirements documentation
✓ Statute retrieval working: Found 3 results
  Top result: W&I Code § 5899...

================================================================================
MIGRATION COMPLETE
================================================================================
✓ Policy chunks added: 387
✓ Statute chunks added: 155
✓ Total documents: 542

Next steps:
  1. Start the API: docker-compose up -d
  2. Test curation endpoint: curl http://localhost:8000/curation/stats
  3. Process a test question via API or Streamlit UI
```

### 3.3 Verify Migration Success

```bash
# Check ChromaDB was created
ls -la chroma_data/
# Should see: chroma.sqlite3 and other files

# Check database size (should be > 1MB)
du -sh chroma_data/
# Should output: ~2-3M or larger
```

**✅ SUCCESS INDICATORS:**
- ✅ "Migration COMPLETE" message
- ✅ 542 total documents
- ✅ 387 policy chunks
- ✅ 155 statute chunks
- ✅ Retrieval test passed (found results)

**❌ IF MIGRATION FAILS:**

**Error:** "FileNotFoundError: Policy manual not found"
```bash
# Check file exists
ls -la data/BHSA_County_Policy_Manual.md
# If missing, go back to Step 1
```

**Error:** "No module named 'chromadb'"
```bash
# Install dependencies
pip install -r requirements.txt
```

**Error:** "OpenAI API key not found"
```bash
# Set API key
export OPENAI_API_KEY="your-key-here"
# Re-run migration
python scripts/migrate_curation_data.py
```

**✅ STEP 3 COMPLETE** when you see "MIGRATION COMPLETE" and 542 documents

---

## Step 4: Start Services

**Time:** 1-2 minutes
**Goal:** Start Docker containers with API and all agents

### 4.1 Start Docker Compose

```bash
cd /Users/raj/dhcs-intake-lab
docker-compose up -d
```

**Expected output:**
```
Creating network "dhcs-intake-lab_default" ...
Creating dhcs-intake-lab_zookeeper_1 ... done
Creating dhcs-intake-lab_kafka_1 ... done
Creating dhcs-intake-lab_pinot-controller_1 ... done
Creating dhcs-intake-lab_pinot-broker_1 ... done
Creating dhcs-intake-lab_pinot-server_1 ... done
Creating dhcs-intake-lab_agent-api_1 ... done
Creating dhcs-intake-lab_dashboard_1 ... done
```

### 4.2 Wait for Services to Start

```bash
# Wait 30 seconds for services to initialize
echo "Waiting for services to start..."
sleep 30

# Check service status
docker-compose ps
```

**Expected output:**
```
Name                            State    Ports
-----------------------------------------------------------------
dhcs-intake-lab_agent-api_1     Up      0.0.0.0:8000->8000/tcp
dhcs-intake-lab_dashboard_1     Up      0.0.0.0:8501->8501/tcp
dhcs-intake-lab_kafka_1         Up      9092/tcp, 29092/tcp
dhcs-intake-lab_pinot-broker_1  Up      0.0.0.0:8099->8099/tcp
...
```

All services should show **"Up"** status.

### 4.3 Verify API is Responding

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2026-01-08T...",
#   "service": "DHCS BHT Multi-Agent API"
# }
```

**✅ SUCCESS CHECK:**
```bash
curl -s http://localhost:8000/health | jq .status
# Should output: "healthy"
```

**❌ IF API DOESN'T RESPOND:**

**Error:** "Connection refused"
```bash
# Check if container is running
docker ps | grep agent-api

# If not running, check logs
docker-compose logs agent-api

# Restart if needed
docker-compose restart agent-api
sleep 10
```

**Error:** "Port 8000 already in use"
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Restart
docker-compose up -d agent-api
```

**✅ STEP 4 COMPLETE** when `curl http://localhost:8000/health` returns "healthy"

---

## Step 5: Test API Endpoints

**Time:** 2 minutes
**Goal:** Verify new curation endpoints are working

### 5.1 Test Curation Stats Endpoint

```bash
curl http://localhost:8000/curation/stats | jq .
```

**Expected response:**
```json
{
  "total_documents": 542,
  "policy_documents": 387,
  "statute_documents": 155,
  "collection_name": "dhcs_bht_knowledge",
  "persist_directory": "./chroma_data"
}
```

**✅ SUCCESS CHECK:**
- `total_documents` = 542
- `policy_documents` = 387
- `statute_documents` = 155

**❌ IF DIFFERENT NUMBERS:**
- If total_documents < 542: Re-run migration (Step 3)
- If 0 documents: Check chroma_data/ exists, restart API

### 5.2 Test Existing Endpoints (Sanity Check)

```bash
# Test chat endpoint (existing functionality)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}' | jq .success

# Should output: true
```

**✅ STEP 5 COMPLETE** when stats endpoint returns 542 documents

---

## Step 6: Process Test Questions

**Time:** 1-2 minutes per question
**Goal:** Run end-to-end curation workflow

### 6.1 Simple Test Question (Fast)

**Create test file:**
```bash
cat > /tmp/test_question.json << 'EOF'
{
  "question": "What are the workforce requirements for BHSA providers?",
  "topic": "Workforce Strategy",
  "sub_section": "Provider Network",
  "category": "Staffing"
}
EOF
```

**Run test:**
```bash
echo "Processing test question (this will take 30-40 seconds)..."
time curl -X POST http://localhost:8000/curation/process \
  -H "Content-Type: application/json" \
  -d @/tmp/test_question.json \
  -o /tmp/test_result.json

# View results
cat /tmp/test_result.json | jq .
```

### 6.2 Expected Response Structure

```json
{
  "success": true,
  "final_summary": "## Compliance Summary\n\n### Bottom Line\nCounties must ensure BHSA-funded providers...",
  "final_response": "✅ Good Quality (Score: 7.8/10)\n\n## Compliance Summary...",
  "action_items": [
    "Review current BHSA provider qualification policies",
    "Conduct gap analysis versus Medi-Cal standards",
    "Develop implementation timeline if pursuing alignment"
  ],
  "priority": "High",
  "quality_score": 7.8,
  "passes_review": true,
  "metadata": {
    "statute_confidence": "High",
    "policy_confidence": "High",
    "relevant_statutes": ["W&I Code § 5899", "W&I Code § 14680"],
    "revision_count": 0,
    "statute_chunks_retrieved": 8,
    "policy_chunks_retrieved": 10,
    "quality_issues": [],
    "quality_suggestions": []
  }
}
```

### 6.3 Verify Response Quality

```bash
# Check key fields
cat /tmp/test_result.json | jq '{
  success: .success,
  quality_score: .quality_score,
  passes_review: .passes_review,
  priority: .priority,
  action_items_count: (.action_items | length),
  statute_confidence: .metadata.statute_confidence
}'
```

**✅ SUCCESS INDICATORS:**
- ✅ `success`: true
- ✅ `quality_score`: >= 7.0
- ✅ `passes_review`: true
- ✅ `action_items`: 2-5 items
- ✅ `priority`: "High", "Medium", or "Low"
- ✅ `final_summary`: contains "## Compliance Summary"

**Processing Time:**
- First request: 35-50 seconds (cold start, loading agents)
- Subsequent requests: 25-40 seconds

### 6.4 View Formatted Output

```bash
# Extract and display the final summary
cat /tmp/test_result.json | jq -r .final_summary

# Should display nicely formatted markdown like:
# ## Compliance Summary
#
# ### Bottom Line
# Counties must ensure BHSA-funded providers are qualified...
#
# ### Statutory Basis
# W&I Code § 5899 requires...
#
# ### Policy Guidance
# Policy Manual Section 3.4.2 states...
#
# ### Action Items for County
# 1. Review current policies
# 2. Conduct gap analysis
# 3. Develop timeline
#
# ### Open Questions / Ambiguities
# None identified
```

**✅ STEP 6 COMPLETE** when test question processes successfully with quality_score >= 7.0

---

## Step 7: Verify Quality

**Time:** 5 minutes
**Goal:** Ensure output meets quality standards

### 7.1 Check Agent Execution in Logs

```bash
# View agent execution logs
docker-compose logs agent-api | grep -E "(RetrievalAgent|StatuteAnalystAgent|PolicyAnalystAgent|SynthesisAgent|QualityReviewerAgent)" | tail -20
```

**Expected log entries:**
```
agent-api_1  | INFO - RetrievalAgent - Retrieving documents for topic: Workforce Strategy
agent-api_1  | INFO - RetrievalAgent - Retrieved 8 statute chunks, 10 policy chunks
agent-api_1  | INFO - StatuteAnalystAgent - Analyzing 8 statute chunks for relevance
agent-api_1  | INFO - StatuteAnalystAgent - Statute analysis complete. Confidence: High. Statutes found: 3
agent-api_1  | INFO - PolicyAnalystAgent - Analyzing 10 policy chunks
agent-api_1  | INFO - PolicyAnalystAgent - Policy analysis complete. Confidence: High. Requirements: 5
agent-api_1  | INFO - SynthesisAgent - Synthesizing compliance summary
agent-api_1  | INFO - SynthesisAgent - Synthesis complete. Priority: High. Action items: 4
agent-api_1  | INFO - QualityReviewerAgent - Reviewing compliance summary quality
agent-api_1  | INFO - QualityReviewerAgent - Quality review complete. Score: 7.8/10. Passes: True
agent-api_1  | INFO - CurationOrchestrator - Curation workflow complete
```

**✅ SUCCESS CHECK:** All 5 agents executed in sequence

### 7.2 Run Multiple Test Questions

```bash
# Test with different topics
for topic in "Workforce Strategy" "Exemption Requests" "Quality Metrics"; do
  echo "Testing: $topic"
  curl -s -X POST http://localhost:8000/curation/process \
    -H "Content-Type: application/json" \
    -d "{\"question\":\"What are the requirements for $topic?\",\"topic\":\"$topic\",\"sub_section\":\"\",\"category\":\"\"}" \
    | jq '{success, quality_score, priority}'
  echo "---"
done
```

**Expected:** All 3 requests succeed with quality_score >= 7.0

### 7.3 Test Error Handling

```bash
# Test with empty question (should fail gracefully)
curl -s -X POST http://localhost:8000/curation/process \
  -H "Content-Type: application/json" \
  -d '{"question":"","topic":"Test","sub_section":"","category":""}' \
  | jq .

# Should return error with success: false, not crash
```

**✅ STEP 7 COMPLETE** when:
- All agents execute successfully
- Multiple test questions work
- Error handling is graceful

---

## Step 8: Test Batch Processing (Optional)

**Time:** 5-10 minutes for small batch
**Goal:** Verify batch endpoint works

### 8.1 Create Small Batch Test

```bash
cat > /tmp/batch_test.json << 'EOF'
{
  "questions": [
    {
      "IP Question": "What are the documentation requirements for assessments?",
      "IP Section": "Quality Assurance",
      "IP Sub-Section": "Documentation Standards",
      "topic_name": "Clinical Documentation"
    },
    {
      "IP Question": "What are the staffing ratios for crisis teams?",
      "IP Section": "Workforce Strategy",
      "IP Sub-Section": "Staffing Requirements",
      "topic_name": "Crisis Response"
    },
    {
      "IP Question": "What language access services are required?",
      "IP Section": "Equity and Access",
      "IP Sub-Section": "LEP Services",
      "topic_name": "Language Access"
    }
  ]
}
EOF
```

### 8.2 Run Batch Test

```bash
echo "Processing 3 questions in batch (will take ~2 minutes)..."
time curl -X POST http://localhost:8000/curation/batch \
  -H "Content-Type: application/json" \
  -d @/tmp/batch_test.json \
  -o /tmp/batch_result.json

# View summary
cat /tmp/batch_result.json | jq '{
  success: .success,
  total_questions: .total_questions,
  avg_quality_score: .summary.avg_quality_score,
  passed_review: .summary.passed_review,
  high_priority: .summary.high_priority
}'
```

**Expected output:**
```json
{
  "success": true,
  "total_questions": 3,
  "avg_quality_score": 7.6,
  "passed_review": 3,
  "high_priority": 2
}
```

**✅ BATCH TEST COMPLETE** when all 3 questions process successfully

---

## Troubleshooting Guide

### Issue 1: "Module 'agents.core.curation_orchestrator' not found"

**Symptom:** API fails to start, error in logs about missing module

**Solution:**
```bash
# 1. Check file exists
ls -l /Users/raj/dhcs-intake-lab/agents/core/curation_orchestrator.py

# 2. If missing, check git status
cd /Users/raj/dhcs-intake-lab
git status

# 3. Restart API container to reload code
docker-compose restart agent-api
sleep 10

# 4. Check logs
docker-compose logs agent-api | tail -50
```

### Issue 2: "ChromaDB collection is empty" or "0 documents"

**Symptom:** `/curation/stats` returns `total_documents: 0`

**Solution:**
```bash
# 1. Check if chroma_data exists
ls -la chroma_data/

# 2. If missing or empty, re-run migration
python scripts/migrate_curation_data.py

# 3. Verify migration completed
curl http://localhost:8000/curation/stats | jq .total_documents
# Should output: 542

# 4. If still 0, check data/ directory
ls -la data/
# Should have BHSA_County_Policy_Manual.md
```

### Issue 3: "Quality score always < 7.0"

**Symptom:** Every question fails quality review

**Possible Causes:**
1. Poor retrieval (not enough relevant documents)
2. Incomplete data migration
3. API key issues

**Solution:**
```bash
# 1. Check document count
curl http://localhost:8000/curation/stats | jq .total_documents
# Should be 542, not 0-50

# 2. Test retrieval directly
curl -X POST http://localhost:8000/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query":"workforce requirements","n_results":3}' \
  | jq '.results | length'
# Should return 3

# 3. Check API key is valid
python3 << 'EOF'
import os
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print("API key valid:", client.models.list().data[0].id)
EOF
# Should print a model name, not error

# 4. Re-run migration with verbose logging
python scripts/migrate_curation_data.py 2>&1 | tee migration.log
```

### Issue 4: "Processing takes > 60 seconds"

**Symptom:** Requests timeout or take very long

**Possible Causes:**
1. Cold start (first request after restart)
2. Network issues with OpenAI API
3. Rate limiting

**Solution:**
```bash
# 1. Check if it's cold start
# Make a test request and time it
time curl -s -X POST http://localhost:8000/curation/process \
  -H "Content-Type: application/json" \
  -d '{"question":"Test","topic":"Test","sub_section":"","category":""}' \
  > /dev/null

# First request: 40-60 seconds (cold start)
# Second request: 25-40 seconds (warmed up)

# 2. Check OpenAI API status
curl https://status.openai.com/api/v2/status.json | jq .

# 3. Check for rate limiting in logs
docker-compose logs agent-api | grep -i "rate\|429\|limit"

# 4. If rate limited, wait 60 seconds and retry
```

### Issue 5: "Docker containers keep restarting"

**Symptom:** `docker ps` shows containers with status "Restarting"

**Solution:**
```bash
# 1. Check logs for the failing container
docker-compose logs agent-api | tail -100

# 2. Common issues:
#    - Port conflict: Change port in docker-compose.yml
#    - Memory limit: Increase Docker memory allocation
#    - Missing dependencies: Rebuild image

# 3. Rebuild and restart
docker-compose down
docker-compose build agent-api
docker-compose up -d

# 4. Monitor startup
docker-compose logs -f agent-api
```

### Issue 6: "Import Error: No module named 'langchain_openai'"

**Symptom:** Python import fails

**Solution:**
```bash
# If using venv:
source .venv/bin/activate
pip install -r requirements.txt

# If using Docker:
docker-compose build agent-api
docker-compose up -d agent-api

# Verify installation
docker-compose exec agent-api python -c "from langchain_openai import ChatOpenAI; print('OK')"
```

---

## What to Do If Something Fails

### Decision Tree

```
Is the API responding at all?
├─ NO → Check Docker containers: docker-compose ps
│       └─ Container not running? → Check logs: docker-compose logs agent-api
│           └─ Fix issue and restart: docker-compose up -d
│
└─ YES → Is /curation/stats showing 542 documents?
    ├─ NO → Re-run migration: python scripts/migrate_curation_data.py
    │
    └─ YES → Is quality_score < 7.0?
        ├─ YES → Check retrieval working: test /knowledge/search
        │       └─ Not working? → Check OpenAI API key
        │
        └─ NO → Everything working! ✅
```

### When to Ask for Help

Contact the senior engineer who did the migration if:

1. **Migration script fails completely**
   - Save the error output: `python scripts/migrate_curation_data.py 2>&1 | tee error.log`
   - Share: error.log and output of `ls -la data/`

2. **All test questions fail quality review**
   - Share: Output of `/curation/stats` and a sample failed response
   - Run: `docker-compose logs agent-api | tail -200 > logs.txt` and share logs.txt

3. **Services won't start**
   - Share: `docker-compose ps` and `docker-compose logs agent-api | tail -100`

4. **Unexpected behavior**
   - Document: Exact steps to reproduce
   - Share: Request and response JSON
   - Include: Logs from the time of the issue

---

## Success Verification Checklist

Before considering setup complete, verify:

- [ ] All Docker containers are "Up" (`docker-compose ps`)
- [ ] API health endpoint responds (`curl http://localhost:8000/health`)
- [ ] Curation stats shows 542 documents (`curl http://localhost:8000/curation/stats`)
- [ ] Test question processes successfully (Step 6)
- [ ] Quality score >= 7.0 on test question
- [ ] All 5 agents execute (check logs)
- [ ] Action items are generated (2-5 items)
- [ ] Final summary contains all required sections
- [ ] Response time < 60 seconds (after warm-up)
- [ ] Error handling works gracefully

### Final Verification Command

Run this to check everything at once:

```bash
#!/bin/bash
echo "=== Final Verification ==="
echo ""

echo "1. Docker Status:"
docker-compose ps | grep -E "(Up|Exit)" | wc -l
echo "   (Should be 7+ containers Up)"

echo ""
echo "2. API Health:"
curl -s http://localhost:8000/health | jq -r .status
echo "   (Should be: healthy)"

echo ""
echo "3. Document Count:"
curl -s http://localhost:8000/curation/stats | jq .total_documents
echo "   (Should be: 542)"

echo ""
echo "4. Test Question:"
time curl -s -X POST http://localhost:8000/curation/process \
  -H "Content-Type: application/json" \
  -d '{"question":"What are workforce requirements?","topic":"Workforce Strategy","sub_section":"","category":""}' \
  | jq '{success, quality_score, passes_review, action_items: (.action_items | length)}'
echo "   (Should be: success=true, quality_score>=7.0, passes_review=true, action_items=2-5)"

echo ""
echo "=== Verification Complete ==="
```

Save as `verify_setup.sh`, make executable (`chmod +x verify_setup.sh`), and run: `./verify_setup.sh`

---

## Next Steps After Setup

Once everything is working:

1. **Read Technical Guide**
   - Open `CURATION_IMPLEMENTATION_GUIDE.md`
   - Understand architecture and agent design

2. **Test with Real Data**
   - Use PreProcessRubric_v0.csv
   - Process "Workforce Strategy" category (15 questions)
   - Review quality scores

3. **Optimize for Your Use Case**
   - Adjust temperature settings in agents
   - Modify prompts for your domain
   - Tune quality thresholds

4. **Add Streamlit UI** (Optional)
   - Integrate with existing dashboard
   - Add CSV upload/download
   - Visualize quality scores

5. **Replace Statute Placeholders**
   - Obtain actual W&I Code texts
   - Re-run migration with real statutes
   - Test improved retrieval

---

## Quick Reference Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart API only
docker-compose restart agent-api

# View logs
docker-compose logs -f agent-api

# Check document count
curl http://localhost:8000/curation/stats | jq .total_documents

# Test single question
curl -X POST http://localhost:8000/curation/process \
  -H "Content-Type: application/json" \
  -d '{"question":"Test question","topic":"Test","sub_section":"","category":""}' | jq .

# Re-run migration
python scripts/migrate_curation_data.py

# Verify setup
curl http://localhost:8000/health && \
curl http://localhost:8000/curation/stats | jq . && \
echo "✅ All systems operational"
```

---

## Support and Documentation

- **Technical Reference:** [`CURATION_IMPLEMENTATION_GUIDE.md`](./CURATION_IMPLEMENTATION_GUIDE.md)
- **Architecture Details:** See "Architecture Overview" section in implementation guide
- **API Documentation:** See "API Endpoints" section in implementation guide
- **Agent Design:** Check individual agent files in `agents/core/`

**Estimated Setup Time:** 15-20 minutes (if following this guide)

**Last Updated:** January 8, 2026
**Migration Engineer:** Senior AI Infrastructure Team
**System Version:** dhcs-intake-lab v0.2.0 with Policy Curation
