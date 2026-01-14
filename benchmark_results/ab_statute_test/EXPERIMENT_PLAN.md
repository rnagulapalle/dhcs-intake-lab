# A/B Experiment: Impact of Real Statute Texts on Multi-Agent Quality

**Date**: January 9, 2026
**Hypothesis**: Replacing placeholder statute texts with real W&I Code content will improve quality scores and statute confidence
**Method**: Before/after comparison on same 10-question benchmark

---

## Baseline (Before)

**System State**:
- ChromaDB contains placeholder statutes (confirmed via code inspection)
- 18 statute sections loaded as placeholders per [curation_loader.py:268-306](../../agents/knowledge/curation_loader.py#L268-L306)
- Placeholder format: `[Placeholder - Replace with actual statute text]`

**Baseline Results** (existing run):
- File: [benchmark_results/multiagent_10q/summary.json](../multiagent_10q/summary.json)
- Run date: 2026-01-09 16:01:54
- Total questions: 10
- Success rate: 10/10 (100%)
- Average quality score: 8.61/10
- Pass rate: 10/10 (100%)
- Average processing time: 28.21 seconds
- Statute confidence: "Low" (10/10 questions)
- Relevant statutes identified: 0 (empty array on all questions)

**Evidence**: All 10 result files show:
```json
"metadata": {
  "statute_confidence": "Low",
  "relevant_statutes": [],
  ...
}
```

---

## Intervention

**Change**: Replace placeholder statutes with real W&I Code texts

**Implementation**:
1. Created [data/statutes.md](../../data/statutes.md) with:
   - 3 sections fully extracted (§5899, §14184, §14124) - 645 lines total
   - 15 sections as placeholders pending full extraction
2. Re-run migration script to reload ChromaDB:
   ```bash
   docker-compose exec agent-api python /app/scripts/migrate_curation_data.py
   ```

**Scope**: Partial implementation (3/18 statutes = 16.7% real content)

**Rationale for partial implementation**:
- WebFetch limitations prevented batch extraction of all 18 statutes
- 3 real statutes provide sufficient signal to test hypothesis
- Documents honest methodology vs. overstating data completeness

---

## Test (After)

**Execution Plan**:
1. Clear existing ChromaDB in container
2. Re-run migration with new statutes.md
3. Verify statute content loaded (check one statute via API)
4. Run same 10-question benchmark:
   ```bash
   python3 scripts/run_10_questions_multiagent.py
   ```
5. Save results to: `benchmark_results/ab_statute_test/after/`

**Same test conditions**:
- Same 10 questions (IDs: 44, 325, 119, 114, 242, 197, 40, 10, 233, 93)
- Same API endpoint: `POST /curation/process`
- Same timeout: 300 seconds
- Same quality threshold: 7.0/10

---

## Metrics to Compare

### Primary Metrics
1. **Average quality score** (before: 8.61/10)
2. **Statute confidence distribution** (before: 10/10 "Low")
3. **Relevant statutes identified** (before: 0/10 non-empty)

### Secondary Metrics
4. **Pass rate** (before: 100%)
5. **Average processing time** (before: 28.21s)
6. **LLM-judge score** (before: 72.0/100) - optional re-run
7. **Action items count** (before: 4.4 avg)
8. **Revision rate** (before: 0%)

### Qualitative Analysis
9. **Statute citations in outputs** - do real statutes get cited?
10. **Quality issue patterns** - do issues change?

---

## Expected Outcomes

### Hypothesis 1: Quality Score Improves
**Prediction**: 8.61 → 8.8-9.0 (+0.2 to +0.4 points)
**Reasoning**: Statute analyst agent can extract real requirements instead of placeholder text

### Hypothesis 2: Statute Confidence Increases
**Prediction**: "Low" → "Medium" or "High" on subset of questions
**Reasoning**: Real statute texts enable confidence assessment

### Hypothesis 3: Relevant Statutes Identified
**Prediction**: 0/10 → 3-5/10 questions show non-empty `relevant_statutes` array
**Reasoning**: Only 3/18 statutes are real, so partial improvement expected

### Null Hypothesis: No Significant Change
**Alternative**: Quality remains 8.5-8.7, confidence stays "Low"
**Implications**: Other factors (policy quality, retrieval relevance) dominate system performance

---

## Confounds to Control

1. **API rate limits**: Run sequentially with delays to avoid throttling
2. **Model variability**: Same model (gpt-4o-mini), same temperature (0.3)
3. **Time-of-day effects**: Run immediately after setup, within same hour
4. **ChromaDB state**: Verify document count before/after migration

---

## Rollback Plan

If after-test fails or shows regression:

```bash
# Rollback to placeholder statutes
rm data/statutes.md
docker-compose exec agent-api python /app/scripts/migrate_curation_data.py

# Verify baseline restored
curl http://localhost:8000/curation/stats
```

---

## Deliverables

1. **before/** directory (symlink to existing `multiagent_10q/`)
2. **after/** directory with new 10-question run
3. **delta_report.md** with:
   - Side-by-side metric comparison table
   - Statistical significance (if applicable)
   - Qualitative analysis of output changes
   - Auditor-friendly summary paragraph
4. **EXPERIMENT_LOG.md** documenting exact commands run

---

**Experiment Status**: Ready to execute
**Next Step**: Clear ChromaDB and re-migrate with real statutes
