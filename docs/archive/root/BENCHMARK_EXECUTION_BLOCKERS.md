# Benchmark Execution - Blocker Analysis

**Date**: January 9, 2026
**Status**: BLOCKED - Cannot execute valid benchmark
**Prepared By**: Senior AI/ML Architect

---

## Objective

Execute apples-to-apples benchmark between:
1. Rishi's POC implementation (`agent-boiler-plate/src/rag_curation`)
2. Current multi-agent system (`dhcs-intake-lab`)

Using:
- Same 356 questions from `nova_micro.xlsx`
- Same 0-100 scoring rubric
- Comparable output fields

---

## Feasibility Assessment

### ✅ What We Have

1. **Ground Truth Data**: `nova_micro.xlsx`
   - 356 questions with reference scores
   - 0-100 scoring with justification
   - Contains: `statute_summary`, `policy_summary`, `policy_manual_context_per_LLM`
   - 99.7% question match rate with PreProcessRubric_v0.csv (300/301 matched)

2. **POC Implementation**: `agent-boiler-plate/src/rag_curation`
   - Complete codebase
   - Entry point: `main.py`
   - Data: PreProcessRubric_v0.csv, BHSA_County_Policy_Manual.md
   - ChromaDB vector store: `data/chroma_v0/`
   - Dependencies: `requirements.txt`

3. **Multi-Agent System**: `dhcs-intake-lab`
   - Running in Docker containers
   - API endpoint: `POST /curation/process`
   - ChromaDB with 656 documents loaded
   - Quality reviewer operational (8.4/10 avg score on 5 test questions)

### ❌ Critical Blockers

#### Blocker 1: Missing OpenAI API Key for POC

**Issue**: POC requires `OPENAI_API_KEY` environment variable
- Code line: `os.getenv("OPENAI_API_KEY","")`
- Model: `gpt-4.1-mini` (hardcoded)
- No API key currently set in environment
- Cannot run POC without valid key

**Impact**: Cannot execute POC system to generate comparison outputs

**Resolution Options**:
1. User provides OpenAI API key
2. Use existing POC outputs from `policy_context_batch2/3.csv` (only 91 questions, not 356)
3. Skip POC execution, compare only against nova_micro ground truth scores

#### Blocker 2: POC Model Unavailable

**Issue**: POC uses `gpt-4.1-mini` which may not exist
- OpenAI's current models: `gpt-4-turbo`, `gpt-4`, `gpt-3.5-turbo`
- No public model named `gpt-4.1-mini`
- May be typo for `gpt-4-mini` or custom model

**Impact**: Even with API key, POC may fail to run

**Resolution Options**:
1. Update POC code to use valid model (requires code modification)
2. User clarifies correct model name
3. Use existing POC outputs only

#### Blocker 3: POC Batch Processing Limitation

**Issue**: POC main.py is hardcoded for batch processing
- Line 75: `category='Workforce Strategy'` (hardcoded)
- Line 98-101: Batch processing with sleep(60) between batches
- Not configured for on-demand single-question processing
- Would require code refactoring to run 356 questions programmatically

**Impact**: Cannot easily run all 356 questions through POC

**Resolution Options**:
1. Refactor POC to accept question list and process all 356
2. Use existing POC outputs (91 questions)
3. Run subset manually

#### Blocker 4: Scoring Rubric Not Automated

**Issue**: No automated scorer exists for 0-100 rubric
- `nova_micro.xlsx` contains human scores
- Scoring criteria: "strong/moderate/weak sentiment" (subjective)
- No code to reproduce scoring automatically
- Would require human evaluation or LLM-as-judge

**Impact**: Cannot score new outputs on 0-100 scale

**Resolution Options**:
1. Build LLM-as-judge scorer using nova_micro examples
2. Use human evaluation (expensive, slow)
3. Use proxy metrics (BLEU, ROUGE, semantic similarity)
4. Compare only against existing scores in nova_micro

#### Blocker 5: Multi-Agent System Uses Different Data

**Issue**: Systems use different ChromaDB instances
- POC: `agent-boiler-plate/src/rag_curation/data/chroma_v0/`
- Multi-agent: Docker volume with 656 documents (vs POC unknown count)
- Different chunking parameters likely
- Different statute data (POC may not have placeholders)

**Impact**: Retrieval quality differs, not apples-to-apples

**Resolution Options**:
1. Use same ChromaDB for both systems (requires migration)
2. Acknowledge retrieval as confounding variable
3. Report results with caveat

---

## Viable Benchmark Options

Given blockers, here are executable approaches:

### Option A: Compare Multi-Agent vs Nova Micro Ground Truth (FEASIBLE)

**What**: Run multi-agent system on 356 questions, compare scores against nova_micro

**Pros**:
- No POC execution needed
- Can execute immediately
- Shows how multi-agent performs vs Nauman's baseline

**Cons**:
- Not comparing two systems directly
- Nova_micro used AWS Bedrock Nova Micro (different model)
- Not testing POC vs multi-agent

**Execution**:
```bash
# For each question in nova_micro.xlsx:
curl -X POST http://localhost:8000/curation/process \
  -H "Content-Type: application/json" \
  -d '{"question": "...", "topic": "...", ...}'

# Compare outputs:
# - Our statute_summary vs nova statute_summary
# - Our policy_summary vs nova policy_summary
# - Our final_summary vs nova policy_manual_context_per_LLM
# - Our quality_score vs nova score (different scales: 0-10 vs 0-100)
```

**Estimated Time**: 356 questions × 1:47 minutes = ~10 hours runtime

### Option B: Compare Small Subset with Manual POC Execution (FEASIBLE)

**What**: Run 10-20 questions through both systems manually

**Pros**:
- True apples-to-apples comparison
- Can manually inspect quality differences
- Manageable scope

**Cons**:
- Not statistically representative (20/356 = 5.6%)
- Still requires API key
- Labor intensive

**Execution**:
1. User provides OpenAI API key
2. Fix model name in POC code
3. Create wrapper script for single-question processing
4. Run 20 questions through both systems
5. Human evaluation of outputs

**Estimated Time**: 1 day setup + 1 day execution

### Option C: Use Existing POC Outputs (LIMITED)

**What**: Compare multi-agent on same 91 questions from batch2/3.csv

**Pros**:
- No POC execution needed
- Direct output comparison possible
- Can execute today

**Cons**:
- Only 91 questions (25.6% coverage)
- No nova_micro scores for these questions
- Different categories (Workforce Strategy, Exemption Requests)

**Execution**:
```python
# Load batch outputs
batch2 = pd.read_csv('policy_context_batch2(in).csv')  # 15 questions
batch3 = pd.read_csv('policy_context_batch3(in).csv')  # 76 questions

# Run multi-agent on same questions
for question in questions:
    our_result = call_multi_agent_api(question)
    poc_result = batch_df[batch_df['IP Question'] == question]

    # Compare:
    # - statute_summary
    # - policy_summary
    # - final_summary
```

**Estimated Time**: 91 questions × 1:47 minutes = ~2.7 hours runtime

### Option D: Build LLM-as-Judge Scorer (TIME INTENSIVE)

**What**: Create automated 0-100 scorer using nova_micro as training data

**Pros**:
- Can score new outputs automatically
- Reproducible evaluation
- Scales to full 356 questions

**Cons**:
- Requires building new evaluation system
- May not match human judgment
- Adds evaluation uncertainty

**Execution**:
1. Extract scoring patterns from nova_micro justifications
2. Build prompt template for LLM judge
3. Validate scorer against known scores (80/20 split)
4. Run on multi-agent outputs

**Estimated Time**: 2-3 days development + validation

---

## Recommended Path Forward

### Recommended: Option A + Option C (Parallel Execution)

**Phase 1**: Multi-Agent vs Nova Micro Ground Truth (Option A)
- Execute multi-agent on all 356 questions
- Compare outputs qualitatively
- Report metrics:
  - Our quality_score distribution
  - Pass rate
  - Revision rate
  - Processing time
- No POC execution required

**Phase 2**: Direct Comparison on 91 Questions (Option C)
- Run multi-agent on same 91 questions from POC batches
- Direct output comparison:
  - Statute coverage
  - Policy accuracy
  - Requirement completeness
- Human evaluation of quality differences

**Combined Output**:
- Multi-agent performance on full 356-question dataset
- Direct POC vs multi-agent comparison on 91 questions (25.6% sample)
- Qualitative assessment of differences

**Timeline**:
- Phase 1: ~12 hours (10 hours runtime + 2 hours analysis)
- Phase 2: ~4 hours (2.7 hours runtime + 1.3 hours analysis)
- **Total: ~2 days**

---

## What We CANNOT Deliver Without Resolving Blockers

1. ❌ POC execution on full 356 questions (needs API key + code refactoring)
2. ❌ Automated 0-100 scoring of new outputs (needs scorer development)
3. ❌ Direct apples-to-apples comparison on all 356 questions (needs POC execution)
4. ❌ Statistical significance testing (needs full dataset comparison)

---

## What We CAN Deliver Now

1. ✅ Multi-agent system performance on 356 questions (vs nova_micro reference)
2. ✅ Direct comparison on 91 questions (using existing POC outputs)
3. ✅ Qualitative output analysis (statute/policy/final summary comparison)
4. ✅ Multi-agent system diagnostic metrics (quality scores, revisions, confidence)
5. ✅ Root cause analysis of multi-agent bottlenecks

---

## Decision Required

**Question for User**: Which execution option should I proceed with?

**Option A**: Multi-agent on 356 questions vs nova_micro ground truth (10 hours runtime)
**Option B**: Small subset (20 questions) with manual POC execution (requires API key)
**Option C**: Multi-agent on 91 questions with POC batch outputs (2.7 hours runtime)
**Option A + C**: Both in parallel (12 hours total)

**Alternative**: If user can provide OpenAI API key and confirm correct model name, I can attempt Option B or refactor POC for full 356-question execution.

---

## Blocker Summary Table

| Blocker | Severity | Resolution | ETA |
|---------|----------|------------|-----|
| No OpenAI API key | CRITICAL | User provides key | Immediate |
| Invalid model name | HIGH | User confirms model or update code | 30 minutes |
| POC batch processing | MEDIUM | Refactor for single-question API | 2-4 hours |
| No automated 0-100 scorer | MEDIUM | Build LLM-as-judge | 2-3 days |
| Different ChromaDB data | LOW | Document as confounding variable | N/A |

---

**Status**: AWAITING USER DECISION ON EXECUTION PATH
**Recommendation**: Proceed with Option A + C (deliverable in 2 days, no blockers)
