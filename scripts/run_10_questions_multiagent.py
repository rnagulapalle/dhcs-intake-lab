"""
Run multi-agent system on 10 questions and capture full outputs
"""
import json
import requests
import time
from pathlib import Path
from datetime import datetime

def run_10_questions():
    """Execute multi-agent on 10 benchmark questions"""

    # Load 10-question sample
    sample_path = Path("/Users/raj/dhcs-intake-lab/benchmark_sample_10.json")
    with open(sample_path) as f:
        sample = json.load(f)

    questions = sample['questions']
    print(f"Running multi-agent on {len(questions)} questions\n")

    # Create output directory
    output_dir = Path("/Users/raj/dhcs-intake-lab/benchmark_results/multiagent_10q")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for i, q in enumerate(questions, 1):
        print(f"{'='*80}")
        print(f"Question {i}/{len(questions)} [ID: {q['index']}]")
        print(f"Score: {q['score']:.0f} | Quartile: {q['score_quartile']}")
        print(f"Question: {q['IP_Question'][:100]}...")
        print(f"{'='*80}")

        payload = {
            "question": q['IP_Question'],
            "topic": q['policy_manual_section'],
            "sub_section": "",
            "category": "Benchmark"
        }

        start_time = time.time()
        try:
            response = requests.post(
                "http://localhost:8000/curation/process",
                json=payload,
                timeout=300
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                result = response.json()

                # Save individual result
                output_file = output_dir / f"q{q['index']}.json"
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)

                print(f"✅ SUCCESS in {elapsed:.1f}s")
                print(f"  Quality Score: {result.get('quality_score', 0):.1f}/10")
                print(f"  Passes Review: {result.get('passes_review', False)}")
                print(f"  Action Items: {len(result.get('action_items', []))}")
                print(f"  Revisions: {result.get('metadata', {}).get('revision_count', 0)}")

                results.append({
                    'question_id': q['index'],
                    'ground_truth_score': q['score'],
                    'quartile': q['score_quartile'],
                    'success': True,
                    'time_seconds': elapsed,
                    'quality_score': result.get('quality_score', 0),
                    'passes_review': result.get('passes_review', False),
                    'action_items_count': len(result.get('action_items', [])),
                    'revisions': result.get('metadata', {}).get('revision_count', 0)
                })
            else:
                print(f"❌ ERROR: HTTP {response.status_code}")
                results.append({
                    'question_id': q['index'],
                    'ground_truth_score': q['score'],
                    'quartile': q['score_quartile'],
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                })

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ EXCEPTION: {str(e)}")
            results.append({
                'question_id': q['index'],
                'ground_truth_score': q['score'],
                'quartile': q['score_quartile'],
                'success': False,
                'error': str(e),
                'time_seconds': elapsed
            })

        print()

    # Save summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_questions': len(questions),
        'successful': sum(r['success'] for r in results),
        'failed': sum(not r['success'] for r in results),
        'avg_quality_score': sum(r.get('quality_score', 0) for r in results if r['success']) / sum(r['success'] for r in results),
        'pass_rate': sum(r.get('passes_review', False) for r in results if r['success']) / sum(r['success'] for r in results),
        'avg_time_seconds': sum(r.get('time_seconds', 0) for r in results if r['success']) / sum(r['success'] for r in results),
        'results': results
    }

    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Success Rate: {summary['successful']}/{summary['total_questions']} ({100*summary['successful']/summary['total_questions']:.0f}%)")
    print(f"Avg Quality Score: {summary['avg_quality_score']:.2f}/10")
    print(f"Pass Rate: {100*summary['pass_rate']:.0f}%")
    print(f"Avg Time: {summary['avg_time_seconds']:.1f}s")
    print(f"\nResults saved to: {output_dir}")

if __name__ == "__main__":
    run_10_questions()
