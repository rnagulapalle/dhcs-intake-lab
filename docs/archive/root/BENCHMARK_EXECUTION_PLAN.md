# Benchmark Execution Plan - POC vs Multi-Agent

**Date**: January 9, 2026
**Status**: IN PROGRESS
**Execution ID**: b4b73e5

---

## A) What Was Executed

### 1. Sample Selection

**Script**: `scripts/select_benchmark_sample.py`

**Method**: Stratified sampling across score quartiles from `nova_micro.xlsx`
- Total questions available: 356
- Sampled: 5 questions (one per quartile Q1-Q4)
- Output: `benchmark_sample_5.json`

**Selected Questions**:

| Index | Score | Quartile | Section |
|-------|-------|----------|---------|
| 44    | 50.0  | Q1       | Behavioral Health Services Act |
| 114   | 70.0  | Q2       | Behavioral Health Services Act |
| 242   | 70.0  | Q2       | Behavioral Health Services Act |
| 40    | 75.0  | Q3       | Behavioral Health Services Act |
| 93    | 85.0  | Q4       | Behavioral Health Services Act |

**Score Distribution**: 50 (low) → 70 (median) → 85 (high)

### 2. POC Runner

**Script**: `scripts/run_poc_single.py`

**Adaptations from original**:
- Loaded `.env` from `dhcs-intake-lab` BEFORE any langchain imports (critical for API key)
- Changed model from `gpt-4.1-mini` (invalid) to `gpt-4o-mini` (valid)
- Added single-question entry point (original was batch-only)
- Preserved original 3-stage pipeline:
  1. Statute analysis
  2. Policy analysis
  3. Synthesis

**Entry Point**:
```bash
cd agent-boiler-plate && source .venv/bin/activate
python3 scripts/run_poc_single.py \
  --question "<text>" \
  --section "<section>" \
  --output <path>
```

**Output Fields**:
- `statute_summary`: Stage 1 output
- `policy_summary`: Stage 2 output
- `final_summary`: Stage 3 output
- `metadata`: Chunk counts

### 3. Multi-Agent Runner

**Script**: `scripts/run_multiagent_single.py`

**Method**: API call to running Docker container

**Entry Point**:
```bash
python3 scripts/run_multiagent_single.py \
  --question "<text>" \
  --section "<section>" \
  --output <path>
```

**Output Fields**:
- Full multi-agent response including:
  - `statute_analysis`
  - `policy_guidance`
  - `bottom_line`
  - `action_items`
  - `quality_score`
  - `passes_review`
  - `metadata` (revisions, confidence, etc.)

### 4. Benchmark Orchestrator

**Script**: `scripts/run_benchmark.py`

**Execution**:
```bash
cd agent-boiler-plate && source .venv/bin/activate
python3 scripts/run_benchmark.py
```

**Process**:
- For each of 5 questions:
  1. Run POC runner → save to `benchmark_results/poc/q{id}.json`
  2. Run multi-agent runner → save to `benchmark_results/multiagent/q{id}.json`
  3. Record timing, success/failure
  4. Save progress after each question

**Timeout**: 300 seconds (5 minutes) per question per system

**Total Expected Runtime**: 5 questions × 2 systems × ~2 min = ~20 minutes

---

## B) Sample Selection Details

### Questions by Score Quartile

**Q1 (Low - Score 50)**:
- Index: 44
- Question: "1. Please describe the county behavioral health system's approach and timeline(s..."

**Q2 (Median - Score 70)** [2 questions]:
- Index: 114 - "1. Does the county's plan include the development of innovative programs or pilo..."
- Index: 242 - "2. Please describe the specific services provided [narrative box]..."

**Q3 (High-Medium - Score 75)**:
- Index: 40 - "For each program or service type that is part of the county's BHSS funded Adult ..."

**Q4 (High - Score 85)**:
- Index: 93 - "What forms of MAT will the county provide utilizing the strategies selected abov..."

### Diversity Achieved
- Score range: 50-85 (35-point spread)
- All from "Behavioral Health Services Act" section (consistent domain)
- Mix of question types: descriptive, planning, service specification, implementation

---

## C) Results Folder Layout

```
benchmark_results/
├── poc/
│   ├── q44.json
│   ├── q114.json
│   ├── q242.json
│   ├── q40.json
│   └── q93.json
├── multiagent/
│   ├── q44.json
│   ├── q114.json
│   ├── q242.json
│   ├── q40.json
│   └── q93.json
├── benchmark_progress.json  (live progress)
└── benchmark_summary.json   (final stats)
```

**Output Format**:

Each POC result JSON:
```json
{
  "statute_summary": "...",
  "policy_summary": "...",
  "final_summary": "...",
  "metadata": {
    "statute_chunks_retrieved": 123,
    "policy_chunks_retrieved": 456
  }
}
```

Each multi-agent result JSON:
```json
{
  "bottom_line": "...",
  "statute_analysis": "...",
  "policy_guidance": "...",
  "action_items": [...],
  "open_questions": [...],
  "priority": "High|Medium|Low",
  "quality_score": 8.6,
  "passes_review": true,
  "metadata": {
    "revision_count": 0,
    "statute_confidence": "High",
    "policy_confidence": "Medium",
    "statute_chunks_retrieved": 10,
    "policy_chunks_retrieved": 10,
    "processing_time_seconds": 107.2
  }
}
```

---

## D) Comparison Methodology

### Metrics to Extract (After Execution)

#### 1. Success Rates
- POC completion rate (%)
- Multi-agent completion rate (%)
- Timeout/error analysis

#### 2. Processing Time
- Mean time per question (POC vs multi-agent)
- Time by score quartile (do harder questions take longer?)

#### 3. Output Structure
**POC**:
- Has statute_summary: Y/N
- Has policy_summary: Y/N
- Has final_summary: Y/N
- Length of each field

**Multi-agent**:
- Has all required sections: Y/N
- Passes quality review: Y/N
- Number of action items generated
- Number of open questions identified
- Priority assigned

#### 4. Retrieval Metrics
- Statute chunks retrieved (POC vs multi-agent)
- Policy chunks retrieved (POC vs multi-agent)

#### 5. Content Quality (Manual Inspection)
For each question, compare:
- **Statute coverage**: Are same W&I Code sections referenced?
- **Policy accuracy**: Do both cite same policy manual sections?
- **Requirement completeness**: Does output include exact requirements from Jira criteria?
- **Actionability**: Does output provide specific guidance?

#### 6. Multi-Agent Specific Metrics
- Quality score distribution (0-10)
- Pass rate (% with quality_score ≥ 7.0)
- Revision rate (% requiring revisions)
- Confidence scoring (statute + policy)

### Comparison Table Template

| Question ID | GT Score | POC Success | MA Success | POC Time (s) | MA Time (s) | POC Statute Refs | MA Statute Refs | MA Quality Score | MA Passes |
|-------------|----------|-------------|------------|--------------|-------------|------------------|-----------------|------------------|-----------|
| 44          | 50       | ?           | ?          | ?            | ?           | ?                | ?               | ?                | ?         |
| 114         | 70       | ?           | ?          | ?            | ?           | ?                | ?               | ?                | ?         |
| ...         | ...      | ...         | ...        | ...          | ...         | ...              | ...             | ...              | ...       |

---

## E) Observed Issues (To Be Filled After Execution)

**POC Issues**:
- TBD after execution

**Multi-Agent Issues**:
- TBD after execution

---

## F) Improvements (To Be Filled After Execution)

**Evidence-Based Improvements**:
- TBD after execution

**Regressions**:
- TBD after execution

---

## G) Next Steps to Scale 10 → 356

### Prerequisites
1. Validate 5-question results show meaningful signal
2. Estimate full runtime: 356 questions × 2 systems × ~2 min = ~24 hours
3. Confirm infrastructure can handle extended run

### Scaling Strategy
1. **Batch Processing**: Run in batches of 50 with checkpointing
2. **Parallel Execution**: Consider running POC and multi-agent concurrently
3. **Error Handling**: Implement retry logic for transient failures
4. **Resource Management**: Monitor API rate limits, memory usage
5. **Progress Tracking**: Real-time dashboard showing completion status

### Optimization Options
1. **Reduce Timeout**: If systems reliably complete <2 min, reduce from 300s to 180s
2. **Skip Failing Questions**: If one system consistently times out on certain questions, skip for fairness
3. **Cache Retrieval**: If retrieval is slow, cache vector search results

---

**Execution Status**: Running in background (Task ID: b4b73e5)
**Expected Completion**: ~20 minutes from start
**Next Action**: Monitor progress, analyze results when complete
