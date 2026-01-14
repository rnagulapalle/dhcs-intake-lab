"""
Run 10-Question Benchmark with Stratified Sample

Executes multi-agent system on the stratified 10-question sample and saves
results under results/run_<timestamp>/ for traceability.

Usage:
    python3 scripts/run_benchmark_stratified.py
"""
import json
import requests
import time
from pathlib import Path
from datetime import datetime

API_URL = "http://localhost:8000/curation/process"
TIMEOUT = 300  # 5 minutes per question

def load_sample():
    """Load stratified sample"""
    sample_path = Path(__file__).parent.parent / "results" / "sample_10.json"

    if not sample_path.exists():
        print(f"ERROR: Sample file not found: {sample_path}")
        print("Run: python3 scripts/select_sample_10.py")
        exit(1)

    with open(sample_path, 'r') as f:
        sample = json.load(f)

    print(f"Loaded stratified sample: {len(sample['questions'])} questions")
    print(f"Sampling seed: {sample['sampling_metadata']['random_seed']}")
    print(f"Source: {sample['sampling_metadata']['source_file']}")
    return sample

def run_benchmark(sample):
    """Execute benchmark on all questions"""

    # Create timestamped run directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(__file__).parent.parent / "results" / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"BENCHMARK EXECUTION")
    print(f"{'='*80}")
    print(f"Run ID: {timestamp}")
    print(f"Output directory: {run_dir}")
    print(f"Questions: {len(sample['questions'])}")
    print(f"{'='*80}\n")

    results = []
    start_time_total = time.time()

    for i, q_data in enumerate(sample['questions'], 1):
        print(f"{'='*80}")
        print(f"Question {i}/{len(sample['questions'])}")
        print(f"{'='*80}")
        print(f"Section: {q_data['section']}")
        print(f"Sub-section: {q_data['subsection']}")
        print(f"Topic: {q_data['topic']}")
        print(f"Question preview: {q_data['question_preview']}")
        print(f"{'='*80}")

        # Prepare API request
        payload = {
            "question": q_data['full_question'],
            "topic": f"{q_data['section']} - {q_data['subsection']}",
            "sub_section": q_data['subsection'],
            "category": q_data['topic']
        }

        start_time = time.time()
        try:
            response = requests.post(API_URL, json=payload, timeout=TIMEOUT)
            elapsed = time.time() - start_time

            if response.status_code == 200:
                result = response.json()

                # Save individual result
                output_file = run_dir / f"q{i:02d}.json"
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)

                print(f"✅ SUCCESS in {elapsed:.1f}s")
                print(f"  Quality Score: {result.get('quality_score', 0):.1f}/10")
                print(f"  Passes Review: {result.get('passes_review', False)}")
                print(f"  Statute Confidence: {result.get('metadata', {}).get('statute_confidence', 'Unknown')}")
                print(f"  Relevant Statutes: {len(result.get('metadata', {}).get('relevant_statutes', []))}")
                print(f"  Action Items: {len(result.get('action_items', []))}")
                print(f"  Revisions: {result.get('metadata', {}).get('revision_count', 0)}")

                # Store result
                results.append({
                    'question_index': i,
                    'sample_index': q_data['sample_index'],
                    'source_index': q_data['source_index'],
                    'section': q_data['section'],
                    'subsection': q_data['subsection'],
                    'topic': q_data['topic'],
                    'success': True,
                    'time_seconds': elapsed,
                    'quality_score': result.get('quality_score', 0),
                    'passes_review': result.get('passes_review', False),
                    'statute_confidence': result.get('metadata', {}).get('statute_confidence', 'Unknown'),
                    'policy_confidence': result.get('metadata', {}).get('policy_confidence', 'Unknown'),
                    'relevant_statutes_count': len(result.get('metadata', {}).get('relevant_statutes', [])),
                    'action_items_count': len(result.get('action_items', [])),
                    'revisions': result.get('metadata', {}).get('revision_count', 0)
                })
            else:
                print(f"❌ ERROR: HTTP {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                results.append({
                    'question_index': i,
                    'sample_index': q_data['sample_index'],
                    'source_index': q_data['source_index'],
                    'section': q_data['section'],
                    'subsection': q_data['subsection'],
                    'topic': q_data['topic'],
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'time_seconds': elapsed
                })

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ EXCEPTION: {str(e)}")
            results.append({
                'question_index': i,
                'sample_index': q_data['sample_index'],
                'source_index': q_data['source_index'],
                'section': q_data['section'],
                'subsection': q_data['subsection'],
                'topic': q_data['topic'],
                'success': False,
                'error': str(e),
                'time_seconds': elapsed
            })

        print()

    # Calculate summary statistics
    total_time = time.time() - start_time_total
    successful = [r for r in results if r['success']]

    summary = {
        'run_metadata': {
            'timestamp': datetime.now().isoformat(),
            'run_id': timestamp,
            'sample_file': 'results/sample_10.json',
            'api_endpoint': API_URL,
            'timeout_seconds': TIMEOUT
        },
        'execution_stats': {
            'total_questions': len(results),
            'successful': len(successful),
            'failed': len(results) - len(successful),
            'success_rate': len(successful) / len(results) if results else 0,
            'total_time_seconds': total_time,
            'avg_time_per_question': total_time / len(results) if results else 0
        },
        'quality_metrics': {},
        'results': results
    }

    if successful:
        quality_scores = [r['quality_score'] for r in successful]
        passes = [r['passes_review'] for r in successful]
        times = [r['time_seconds'] for r in successful]
        statute_conf = [r['statute_confidence'] for r in successful]
        relevant_statutes = [r['relevant_statutes_count'] for r in successful]
        action_items = [r['action_items_count'] for r in successful]
        revisions = [r['revisions'] for r in successful]

        summary['quality_metrics'] = {
            'avg_quality_score': sum(quality_scores) / len(quality_scores),
            'min_quality_score': min(quality_scores),
            'max_quality_score': max(quality_scores),
            'pass_rate': sum(passes) / len(passes),
            'avg_processing_time': sum(times) / len(times),
            'statute_confidence_distribution': {
                'High': statute_conf.count('High'),
                'Medium': statute_conf.count('Medium'),
                'Low': statute_conf.count('Low')
            },
            'relevant_statutes_identified': sum(1 for count in relevant_statutes if count > 0),
            'avg_action_items': sum(action_items) / len(action_items),
            'revision_rate': sum(1 for r in revisions if r > 0) / len(revisions)
        }

    # Save summary
    summary_file = run_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Copy sample manifest to run directory for traceability
    sample_copy = run_dir / "sample_manifest.json"
    with open(Path(__file__).parent.parent / "results" / "sample_10.json", 'r') as f:
        sample_data = json.load(f)
    with open(sample_copy, 'w') as f:
        json.dump(sample_data, f, indent=2)

    # Print final summary
    print(f"{'='*80}")
    print(f"BENCHMARK COMPLETE")
    print(f"{'='*80}")
    print(f"Run ID: {timestamp}")
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"Success rate: {summary['execution_stats']['successful']}/{summary['execution_stats']['total_questions']} ({100*summary['execution_stats']['success_rate']:.0f}%)")

    if summary['quality_metrics']:
        print(f"\nQuality Metrics:")
        print(f"  Avg quality score: {summary['quality_metrics']['avg_quality_score']:.2f}/10")
        print(f"  Pass rate: {100*summary['quality_metrics']['pass_rate']:.0f}%")
        print(f"  Avg processing time: {summary['quality_metrics']['avg_processing_time']:.1f}s")
        print(f"  Statute confidence: High={summary['quality_metrics']['statute_confidence_distribution']['High']}, Medium={summary['quality_metrics']['statute_confidence_distribution']['Medium']}, Low={summary['quality_metrics']['statute_confidence_distribution']['Low']}")
        print(f"  Relevant statutes identified: {summary['quality_metrics']['relevant_statutes_identified']}/10 questions")
        print(f"  Avg action items: {summary['quality_metrics']['avg_action_items']:.1f}")
        print(f"  Revision rate: {100*summary['quality_metrics']['revision_rate']:.0f}%")

    print(f"\nResults saved to: {run_dir}")
    print(f"  - summary.json (metrics and results)")
    print(f"  - sample_manifest.json (sampling details)")
    print(f"  - q01.json through q10.json (individual results)")
    print(f"{'='*80}")

    return run_dir, summary

def main():
    # Check API health
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("ERROR: API health check failed")
            print("Ensure API is running: docker-compose ps agent-api")
            exit(1)
    except Exception as e:
        print(f"ERROR: Cannot connect to API: {e}")
        print("Ensure API is running: docker-compose up -d agent-api")
        exit(1)

    # Load sample
    sample = load_sample()

    # Run benchmark
    run_dir, summary = run_benchmark(sample)

    print(f"\nBenchmark complete! Results in: {run_dir}")

if __name__ == "__main__":
    main()
