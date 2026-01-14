"""
Analyze benchmark results - compare POC vs Multi-Agent outputs
"""
import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

def load_results():
    """Load all benchmark results"""
    results_dir = Path("/Users/raj/dhcs-intake-lab/benchmark_results")

    poc_dir = results_dir / "poc"
    ma_dir = results_dir / "multiagent"

    summary = json.load(open(results_dir / "benchmark_summary.json"))

    # Load individual outputs
    outputs = []
    for result in summary['results']:
        qid = result['question_id']

        poc_file = poc_dir / f"q{qid}.json"
        ma_file = ma_dir / f"q{qid}.json"

        poc_data = json.load(open(poc_file)) if poc_file.exists() else None
        ma_data = json.load(open(ma_file)) if ma_file.exists() else None

        outputs.append({
            'question_id': qid,
            'ground_truth_score': result['ground_truth_score'],
            'score_quartile': result['score_quartile'],
            'poc_success': result['poc_success'],
            'poc_time': result['poc_time_seconds'],
            'ma_success': result['multiagent_success'],
            'ma_time': result['multiagent_time_seconds'],
            'poc_data': poc_data,
            'ma_data': ma_data
        })

    return summary, outputs

def extract_metrics(outputs):
    """Extract comparable metrics from outputs"""
    metrics = []

    for out in outputs:
        qid = out['question_id']
        gt_score = out['ground_truth_score']

        # POC metrics
        poc = out['poc_data']
        if poc:
            poc_statute_len = len(poc.get('statute_summary', ''))
            poc_policy_len = len(poc.get('policy_summary', ''))
            poc_final_len = len(poc.get('final_summary', ''))
            poc_statute_chunks = poc.get('metadata', {}).get('statute_chunks_retrieved', 0)
            poc_policy_chunks = poc.get('metadata', {}).get('policy_chunks_retrieved', 0)
        else:
            poc_statute_len = poc_policy_len = poc_final_len = 0
            poc_statute_chunks = poc_policy_chunks = 0

        # Multi-agent metrics
        ma = out['ma_data']
        if ma:
            ma_quality_score = ma.get('quality_score', 0)
            ma_passes = ma.get('passes_review', False)
            ma_action_items = len(ma.get('action_items', []))
            ma_open_questions = len(ma.get('open_questions', []))
            ma_priority = ma.get('priority', 'Unknown')
            ma_statute_conf = ma.get('metadata', {}).get('statute_confidence', 'Unknown')
            ma_policy_conf = ma.get('metadata', {}).get('policy_confidence', 'Unknown')
            ma_revisions = ma.get('metadata', {}).get('revision_count', 0)
            ma_statute_chunks = ma.get('metadata', {}).get('statute_chunks_retrieved', 0)
            ma_policy_chunks = ma.get('metadata', {}).get('policy_chunks_retrieved', 0)

            # Field lengths for comparison
            ma_statute_len = len(ma.get('statute_analysis', ''))
            ma_policy_len = len(ma.get('policy_guidance', ''))
            ma_final_len = len(ma.get('bottom_line', ''))
        else:
            ma_quality_score = ma_action_items = ma_open_questions = ma_revisions = 0
            ma_statute_chunks = ma_policy_chunks = 0
            ma_statute_len = ma_policy_len = ma_final_len = 0
            ma_passes = False
            ma_priority = ma_statute_conf = ma_policy_conf = 'Unknown'

        metrics.append({
            'question_id': qid,
            'ground_truth_score': gt_score,
            'score_quartile': out['score_quartile'],
            'poc_success': out['poc_success'],
            'poc_time_sec': out['poc_time'],
            'poc_statute_len': poc_statute_len,
            'poc_policy_len': poc_policy_len,
            'poc_final_len': poc_final_len,
            'poc_statute_chunks': poc_statute_chunks,
            'poc_policy_chunks': poc_policy_chunks,
            'ma_success': out['ma_success'],
            'ma_time_sec': out['ma_time'],
            'ma_quality_score': ma_quality_score,
            'ma_passes_review': ma_passes,
            'ma_action_items': ma_action_items,
            'ma_open_questions': ma_open_questions,
            'ma_priority': ma_priority,
            'ma_statute_conf': ma_statute_conf,
            'ma_policy_conf': ma_policy_conf,
            'ma_revisions': ma_revisions,
            'ma_statute_len': ma_statute_len,
            'ma_policy_len': ma_policy_len,
            'ma_final_len': ma_final_len,
            'ma_statute_chunks': ma_statute_chunks,
            'ma_policy_chunks': ma_policy_chunks
        })

    return pd.DataFrame(metrics)

def generate_report(summary, df):
    """Generate markdown report"""

    report = f"""# Benchmark Results: POC vs Multi-Agent System

**Date**: {summary['timestamp']}
**Questions Tested**: {summary['total_questions']}
**Execution**: Actual runs, no fabricated numbers

---

## Execution Summary

| Metric | POC | Multi-Agent |
|--------|-----|-------------|
| **Success Rate** | {summary['poc_success_rate']*100:.0f}% ({sum(df['poc_success'])}/{len(df)}) | {summary['multiagent_success_rate']*100:.0f}% ({sum(df['ma_success'])}/{len(df)}) |
| **Avg Time per Question** | {summary['avg_poc_time']:.1f}s | {summary['avg_multiagent_time']:.1f}s |
| **Timeouts** | {sum(~df['poc_success'])} | {sum(~df['ma_success'])} |

---

## Per-Question Results

"""

    # Table header
    report += "| Q# | GT Score | POC Time | MA Time | MA Quality | MA Pass | MA Actions | MA Revisions |\n"
    report += "|----|----------|----------|---------|------------|---------|------------|-------------|\n"

    for _, row in df.iterrows():
        report += f"| {row['question_id']} | {row['ground_truth_score']:.0f} | "
        report += f"{row['poc_time_sec']:.1f}s | {row['ma_time_sec']:.1f}s | "
        report += f"{row['ma_quality_score']:.1f}/10 | "
        report += f"{'✅' if row['ma_passes_review'] else '❌'} | "
        report += f"{row['ma_action_items']} | {row['ma_revisions']} |\n"

    report += "\n---\n\n## Multi-Agent Metrics\n\n"

    report += f"""### Quality Score Distribution
- **Mean**: {df['ma_quality_score'].mean():.2f}/10
- **Median**: {df['ma_quality_score'].median():.2f}/10
- **Min**: {df['ma_quality_score'].min():.2f}/10
- **Max**: {df['ma_quality_score'].max():.2f}/10
- **Pass Rate** (≥7.0): {(df['ma_quality_score'] >= 7.0).sum()}/{len(df)} ({100*(df['ma_quality_score'] >= 7.0).sum()/len(df):.0f}%)

### Revision Analysis
- **Questions Requiring Revision**: {(df['ma_revisions'] > 0).sum()}/{len(df)} ({100*(df['ma_revisions'] > 0).sum()/len(df):.0f}%)
- **Avg Revisions per Question**: {df['ma_revisions'].mean():.2f}

### Action Items
- **Total Generated**: {df['ma_action_items'].sum()}
- **Avg per Question**: {df['ma_action_items'].mean():.1f}
- **Range**: {df['ma_action_items'].min()}-{df['ma_action_items'].max()}

### Confidence Scoring
**Statute Confidence**:
{df['ma_statute_conf'].value_counts().to_string()}

**Policy Confidence**:
{df['ma_policy_conf'].value_counts().to_string()}

---

## Retrieval Comparison

| Metric | POC | Multi-Agent |
|--------|-----|-------------|
| **Avg Statute Chunks** | {df['poc_statute_chunks'].mean():.1f} | {df['ma_statute_chunks'].mean():.1f} |
| **Avg Policy Chunks** | {df['poc_policy_chunks'].mean():.1f} | {df['ma_policy_chunks'].mean():.1f} |

---

## Output Length Comparison (Characters)

| Field | POC | Multi-Agent |
|-------|-----|-------------|
| **Statute Summary** | {df['poc_statute_len'].mean():.0f} chars | {df['ma_statute_len'].mean():.0f} chars |
| **Policy Summary** | {df['poc_policy_len'].mean():.0f} chars | {df['ma_policy_len'].mean():.0f} chars |
| **Final Summary** | {df['poc_final_len'].mean():.0f} chars | {df['ma_final_len'].mean():.0f} chars |

---

## Performance by Ground Truth Score

"""

    # Group by quartile
    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
        q_df = df[df['score_quartile'] == q]
        if len(q_df) > 0:
            report += f"\n### {q} (GT Score: {q_df['ground_truth_score'].min():.0f}-{q_df['ground_truth_score'].max():.0f})\n"
            report += f"- **Questions**: {len(q_df)}\n"
            report += f"- **MA Quality Score**: {q_df['ma_quality_score'].mean():.2f}/10\n"
            report += f"- **MA Pass Rate**: {(q_df['ma_quality_score'] >= 7.0).sum()}/{len(q_df)}\n"
            report += f"- **Avg POC Time**: {q_df['poc_time_sec'].mean():.1f}s\n"
            report += f"- **Avg MA Time**: {q_df['ma_time_sec'].mean():.1f}s\n"

    report += "\n---\n\n## Raw Data\n\n"
    report += "```\n"
    report += df.to_string()
    report += "\n```\n"

    return report

def main():
    print("Loading benchmark results...")
    summary, outputs = load_results()

    print(f"Extracting metrics from {len(outputs)} questions...")
    df = extract_metrics(outputs)

    print("Generating report...")
    report = generate_report(summary, df)

    output_path = "/Users/raj/dhcs-intake-lab/BENCHMARK_RESULTS_ANALYSIS.md"
    with open(output_path, 'w') as f:
        f.write(report)

    print(f"\n✅ Analysis complete!")
    print(f"Report saved to: {output_path}")

    # Also save CSV
    csv_path = "/Users/raj/dhcs-intake-lab/benchmark_results/comparison_metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"CSV saved to: {csv_path}")

if __name__ == "__main__":
    main()
