# Benchmark Results: POC vs Multi-Agent System

**Date**: 2026-01-09T14:55:11.465412
**Questions Tested**: 5
**Execution**: Actual runs, no fabricated numbers

---

## Execution Summary

| Metric | POC | Multi-Agent |
|--------|-----|-------------|
| **Success Rate** | 100% (5/5) | 100% (5/5) |
| **Avg Time per Question** | 30.1s | 23.4s |
| **Timeouts** | 0 | 0 |

---

## Per-Question Results

| Q# | GT Score | POC Time | MA Time | MA Quality | MA Pass | MA Actions | MA Revisions |
|----|----------|----------|---------|------------|---------|------------|-------------|
| 44 | 50 | 37.1s | 26.3s | 8.1/10 | ✅ | 5 | 0 |
| 114 | 70 | 28.1s | 26.9s | 8.8/10 | ✅ | 4 | 0 |
| 242 | 70 | 29.5s | 22.4s | 8.5/10 | ✅ | 4 | 0 |
| 40 | 75 | 26.4s | 21.9s | 8.8/10 | ✅ | 4 | 0 |
| 93 | 85 | 29.5s | 19.7s | 8.5/10 | ✅ | 5 | 0 |

---

## Multi-Agent Metrics

### Quality Score Distribution
- **Mean**: 8.54/10
- **Median**: 8.50/10
- **Min**: 8.10/10
- **Max**: 8.80/10
- **Pass Rate** (≥7.0): 5/5 (100%)

### Revision Analysis
- **Questions Requiring Revision**: 0/5 (0%)
- **Avg Revisions per Question**: 0.00

### Action Items
- **Total Generated**: 22
- **Avg per Question**: 4.4
- **Range**: 4-5

### Confidence Scoring
**Statute Confidence**:
ma_statute_conf
Low    5

**Policy Confidence**:
ma_policy_conf
Low    5

---

## Retrieval Comparison

| Metric | POC | Multi-Agent |
|--------|-----|-------------|
| **Avg Statute Chunks** | 0.0 | 10.0 |
| **Avg Policy Chunks** | 0.0 | 10.0 |

---

## Output Length Comparison (Characters)

| Field | POC | Multi-Agent |
|-------|-----|-------------|
| **Statute Summary** | 2512 chars | 0 chars |
| **Policy Summary** | 2829 chars | 0 chars |
| **Final Summary** | 2637 chars | 0 chars |

---

## Performance by Ground Truth Score


### Q1 (GT Score: 50-50)
- **Questions**: 1
- **MA Quality Score**: 8.10/10
- **MA Pass Rate**: 1/1
- **Avg POC Time**: 37.1s
- **Avg MA Time**: 26.3s

### Q2 (GT Score: 70-70)
- **Questions**: 2
- **MA Quality Score**: 8.65/10
- **MA Pass Rate**: 2/2
- **Avg POC Time**: 28.8s
- **Avg MA Time**: 24.6s

### Q3 (GT Score: 75-75)
- **Questions**: 1
- **MA Quality Score**: 8.80/10
- **MA Pass Rate**: 1/1
- **Avg POC Time**: 26.4s
- **Avg MA Time**: 21.9s

### Q4 (GT Score: 85-85)
- **Questions**: 1
- **MA Quality Score**: 8.50/10
- **MA Pass Rate**: 1/1
- **Avg POC Time**: 29.5s
- **Avg MA Time**: 19.7s

---

## Raw Data

```
   question_id  ground_truth_score score_quartile  poc_success  poc_time_sec  poc_statute_len  poc_policy_len  poc_final_len  poc_statute_chunks  poc_policy_chunks  ma_success  ma_time_sec  ma_quality_score  ma_passes_review  ma_action_items  ma_open_questions ma_priority ma_statute_conf ma_policy_conf  ma_revisions  ma_statute_len  ma_policy_len  ma_final_len  ma_statute_chunks  ma_policy_chunks
0           44                50.0             Q1         True     37.108523             3013            3102           2727                   0                  0        True    26.278319               8.1              True                5                  0        High             Low            Low             0               0              0             0                 10                10
1          114                70.0             Q2         True     28.083897             2362            2895           2687                   0                  0        True    26.870103               8.8              True                4                  0        High             Low            Low             0               0              0             0                 10                10
2          242                70.0             Q2         True     29.541404             2224            3021           2951                   0                  0        True    22.379496               8.5              True                4                  0        High             Low            Low             0               0              0             0                 10                10
3           40                75.0             Q3         True     26.436060             2703            2700           2514                   0                  0        True    21.896254               8.8              True                4                  0        High             Low            Low             0               0              0             0                 10                10
4           93                85.0             Q4         True     29.456691             2257            2429           2307                   0                  0        True    19.749794               8.5              True                5                  0        High             Low            Low             0               0              0             0                 10                10
```
