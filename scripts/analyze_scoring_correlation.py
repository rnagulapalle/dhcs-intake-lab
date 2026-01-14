"""
Analyze Correlation Between Internal Quality Score and LLM Judge Score

Extracts per-question scoring data and computes correlations to understand
why internal quality_score (0-10) appears higher than LLM-judge (0-100).

Usage:
    python3 scripts/analyze_scoring_correlation.py
"""
import json
import statistics
from pathlib import Path
from typing import List, Dict, Any

def load_results(results_dir: Path) -> Dict[str, Any]:
    """Load all result files"""

    # Load summary
    summary_file = results_dir / "summary.json"
    if not summary_file.exists():
        print(f"ERROR: summary.json not found in {results_dir}")
        return None

    with open(summary_file) as f:
        summary = json.load(f)

    # Load individual question results (find all q*.json files)
    questions = []
    q_files = sorted(results_dir.glob("q*.json"))

    for q_file in q_files:
        if q_file.name == "summary.json":
            continue
        with open(q_file) as f:
            q_data = json.load(f)
            # Extract question ID from filename
            q_id_str = q_file.stem[1:]  # Remove 'q' prefix
            q_data['_file_id'] = q_id_str
            questions.append(q_data)

    # Load LLM judge evaluation if available
    judge_file = results_dir / "llm_judge_evaluation.json"
    llm_judge_data = None
    if judge_file.exists():
        with open(judge_file) as f:
            llm_judge_data = json.load(f)

    return {
        'summary': summary,
        'questions': questions,
        'llm_judge': llm_judge_data
    }

def extract_scoring_table(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract per-question scoring table"""

    questions = data['questions']
    llm_judge = data.get('llm_judge')

    table = []

    for i, q in enumerate(questions, 1):
        row = {
            'question_index': i,
            'quality_score': q.get('quality_score', 0),
            'passes_review': q.get('passes_review', False),
        }

        # Extract criteria scores if available
        metadata = q.get('metadata', {})

        # Get sub-criteria from quality reviewer
        if 'quality_reviewer_result' in metadata:
            criteria = metadata['quality_reviewer_result'].get('criteria_scores', {})
            row.update({
                'completeness': criteria.get('completeness', 0),
                'accuracy': criteria.get('accuracy', 0),
                'actionability': criteria.get('actionability', 0),
                'clarity': criteria.get('clarity', 0),
                'consistency': criteria.get('consistency', 0),
                'citations': criteria.get('citations', 0)
            })

        # Add LLM judge score if available
        if llm_judge:
            evaluations = llm_judge.get('evaluations', [])
            # Find matching evaluation by question_id from file
            file_id = int(q.get('_file_id', 0))
            for eval_data in evaluations:
                if eval_data.get('question_id') == file_id:
                    row['llm_judge_score'] = eval_data.get('llm_judge_score', 0)
                    row['ground_truth_score'] = eval_data.get('ground_truth_score', 0)
                    break

        table.append(row)

    return table

def compute_correlation(x: List[float], y: List[float]) -> Dict[str, float]:
    """Compute Pearson correlation and basic stats"""

    if len(x) != len(y) or len(x) < 2:
        return {'correlation': 0, 'error': 'Insufficient data'}

    # Remove any None values
    pairs = [(xi, yi) for xi, yi in zip(x, y) if xi is not None and yi is not None]
    if len(pairs) < 2:
        return {'correlation': 0, 'error': 'Insufficient valid pairs'}

    x_clean, y_clean = zip(*pairs)

    # Pearson correlation
    mean_x = statistics.mean(x_clean)
    mean_y = statistics.mean(y_clean)

    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x_clean, y_clean))

    std_x = statistics.stdev(x_clean) if len(x_clean) > 1 else 0
    std_y = statistics.stdev(y_clean) if len(y_clean) > 1 else 0

    denominator = std_x * std_y * len(x_clean)

    correlation = numerator / denominator if denominator != 0 else 0

    return {
        'correlation': round(correlation, 3),
        'n': len(pairs),
        'mean_x': round(mean_x, 2),
        'mean_y': round(mean_y, 2),
        'std_x': round(std_x, 2),
        'std_y': round(std_y, 2)
    }

def analyze_score_distributions(table: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze score distributions and identify calibration issues"""

    quality_scores = [row['quality_score'] for row in table]
    llm_judge_scores = [row.get('llm_judge_score') for row in table if row.get('llm_judge_score') is not None]
    ground_truth_scores = [row.get('ground_truth_score') for row in table if row.get('ground_truth_score') is not None]

    # Scale quality_score to 0-100 for comparison
    quality_scores_scaled = [s * 10 for s in quality_scores]

    analysis = {
        'quality_score_0_10': {
            'min': min(quality_scores) if quality_scores else 0,
            'max': max(quality_scores) if quality_scores else 0,
            'mean': statistics.mean(quality_scores) if quality_scores else 0,
            'median': statistics.median(quality_scores) if quality_scores else 0,
            'stdev': statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0
        },
        'quality_score_scaled_0_100': {
            'min': min(quality_scores_scaled) if quality_scores_scaled else 0,
            'max': max(quality_scores_scaled) if quality_scores_scaled else 0,
            'mean': statistics.mean(quality_scores_scaled) if quality_scores_scaled else 0,
            'median': statistics.median(quality_scores_scaled) if quality_scores_scaled else 0,
            'stdev': statistics.stdev(quality_scores_scaled) if len(quality_scores_scaled) > 1 else 0
        }
    }

    if llm_judge_scores:
        analysis['llm_judge_score_0_100'] = {
            'min': min(llm_judge_scores),
            'max': max(llm_judge_scores),
            'mean': statistics.mean(llm_judge_scores),
            'median': statistics.median(llm_judge_scores),
            'stdev': statistics.stdev(llm_judge_scores) if len(llm_judge_scores) > 1 else 0
        }

    if ground_truth_scores:
        analysis['ground_truth_score_0_100'] = {
            'min': min(ground_truth_scores),
            'max': max(ground_truth_scores),
            'mean': statistics.mean(ground_truth_scores),
            'median': statistics.median(ground_truth_scores),
            'stdev': statistics.stdev(ground_truth_scores) if len(ground_truth_scores) > 1 else 0
        }

    # Calibration gap analysis
    if llm_judge_scores and quality_scores_scaled:
        gaps = [qs - ljs for qs, ljs in zip(quality_scores_scaled, llm_judge_scores)]
        analysis['calibration_gap'] = {
            'mean_gap': statistics.mean(gaps),
            'median_gap': statistics.median(gaps),
            'interpretation': 'Positive = internal score higher than judge'
        }

    return analysis

def main():
    print("="*80)
    print("SCORING CORRELATION ANALYSIS")
    print("="*80)
    print()

    # Find results directory
    results_dir = Path(__file__).parent.parent / "benchmark_results" / "multiagent_10q"

    if not results_dir.exists():
        print(f"ERROR: Results directory not found: {results_dir}")
        return

    print(f"Loading results from: {results_dir}")

    # Load all data
    data = load_results(results_dir)
    if not data:
        return

    print(f"Loaded: {len(data['questions'])} question results")
    print(f"LLM Judge data: {'✅ Available' if data['llm_judge'] else '❌ Not available'}")
    print()

    # Extract scoring table
    table = extract_scoring_table(data)

    # Print per-question table
    print("="*80)
    print("PER-QUESTION SCORING TABLE")
    print("="*80)

    # Header
    header = "Q# | Quality | Pass | Completeness | Accuracy | Actionability | Clarity | Consistency | Citations | LLM Judge | Ground Truth"
    print(header)
    print("-" * len(header))

    for row in table:
        q_num = row['question_index']
        quality = row['quality_score']
        passes = '✅' if row['passes_review'] else '❌'

        # Criteria scores (may be missing)
        completeness = row.get('completeness', '-')
        accuracy = row.get('accuracy', '-')
        actionability = row.get('actionability', '-')
        clarity = row.get('clarity', '-')
        consistency = row.get('consistency', '-')
        citations = row.get('citations', '-')

        llm_judge = row.get('llm_judge_score', '-')
        ground_truth = row.get('ground_truth_score', '-')

        print(f"{q_num:2d} | {quality:7.1f} | {passes:^4s} | "
              f"{completeness:^12} | {accuracy:^8} | {actionability:^13} | "
              f"{clarity:^7} | {consistency:^11} | {citations:^9} | "
              f"{llm_judge:^9} | {ground_truth:^12}")

    print()

    # Score distribution analysis
    print("="*80)
    print("SCORE DISTRIBUTIONS")
    print("="*80)

    dist_analysis = analyze_score_distributions(table)

    for score_type, stats in dist_analysis.items():
        if isinstance(stats, dict) and 'mean' in stats:
            print(f"\n{score_type}:")
            print(f"  Range: {stats['min']:.1f} - {stats['max']:.1f}")
            print(f"  Mean: {stats['mean']:.1f}")
            print(f"  Median: {stats['median']:.1f}")
            print(f"  Std Dev: {stats['stdev']:.1f}")

    if 'calibration_gap' in dist_analysis:
        gap = dist_analysis['calibration_gap']
        print(f"\nCalibration Gap (Internal - LLM Judge):")
        print(f"  Mean gap: {gap['mean_gap']:.1f} points")
        print(f"  Median gap: {gap['median_gap']:.1f} points")
        print(f"  {gap['interpretation']}")

    print()

    # Correlation analysis
    print("="*80)
    print("CORRELATION ANALYSIS")
    print("="*80)

    # Extract scores for correlation
    quality_scores_scaled = [row['quality_score'] * 10 for row in table]
    llm_judge_scores = [row.get('llm_judge_score') for row in table if row.get('llm_judge_score') is not None]
    ground_truth_scores = [row.get('ground_truth_score') for row in table if row.get('ground_truth_score') is not None]

    # Correlation 1: Quality Score vs LLM Judge
    if llm_judge_scores:
        corr_1 = compute_correlation(quality_scores_scaled, llm_judge_scores)
        print(f"\nQuality Score (scaled 0-100) vs LLM Judge Score:")
        print(f"  Correlation (Pearson r): {corr_1.get('correlation', 'N/A')}")
        print(f"  Sample size: {corr_1.get('n', 0)}")
        print(f"  Mean Quality (scaled): {corr_1.get('mean_x', 0):.1f}")
        print(f"  Mean LLM Judge: {corr_1.get('mean_y', 0):.1f}")

    # Correlation 2: LLM Judge vs Ground Truth
    if llm_judge_scores and ground_truth_scores and len(llm_judge_scores) == len(ground_truth_scores):
        corr_2 = compute_correlation(llm_judge_scores, ground_truth_scores)
        print(f"\nLLM Judge Score vs Ground Truth Score:")
        print(f"  Correlation (Pearson r): {corr_2.get('correlation', 'N/A')}")
        print(f"  Sample size: {corr_2.get('n', 0)}")
        print(f"  Mean LLM Judge: {corr_2.get('mean_x', 0):.1f}")
        print(f"  Mean Ground Truth: {corr_2.get('mean_y', 0):.1f}")

    # Correlation 3: Quality Score vs Ground Truth (if available)
    if ground_truth_scores and len(quality_scores_scaled) == len(ground_truth_scores):
        corr_3 = compute_correlation(quality_scores_scaled, ground_truth_scores)
        print(f"\nQuality Score (scaled 0-100) vs Ground Truth Score:")
        print(f"  Correlation (Pearson r): {corr_3.get('correlation', 'N/A')}")
        print(f"  Sample size: {corr_3.get('n', 0)}")
        print(f"  Mean Quality (scaled): {corr_3.get('mean_x', 0):.1f}")
        print(f"  Mean Ground Truth: {corr_3.get('mean_y', 0):.1f}")

    print()

    # Save detailed analysis
    output_dir = Path(__file__).parent.parent / "results"
    output_dir.mkdir(exist_ok=True)

    analysis_output = {
        'scoring_table': table,
        'distributions': dist_analysis,
        'correlations': {
            'quality_vs_llm_judge': corr_1 if llm_judge_scores else None,
            'llm_judge_vs_ground_truth': corr_2 if (llm_judge_scores and ground_truth_scores) else None,
            'quality_vs_ground_truth': corr_3 if ground_truth_scores else None
        }
    }

    output_file = output_dir / "scoring_correlation_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(analysis_output, f, indent=2)

    print("="*80)
    print(f"Analysis saved to: {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()
