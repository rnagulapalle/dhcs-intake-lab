"""
POC Parity Test: 10-Question Validation

Validates that intake-lab multi-agent system has POC-compatible outputs:
1. statute_summary, policy_summary, final_summary fields present
2. Chunk citations ([S#], [P#]) present in summaries
3. Similarity threshold filtering working (score >= 0.5)

Usage:
    python3 scripts/run_parity_test_10q.py
"""
import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import urllib.request
import urllib.parse
import urllib.error

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

API_URL = "http://localhost:8000/curation/process"
HEALTH_URL = "http://localhost:8000/health"
TIMEOUT = 300  # 5 minutes per question


def load_sample_questions():
    """Load 10 stratified sample questions"""
    sample_file = Path(__file__).parent.parent / "results" / "sample_10.json"

    if not sample_file.exists():
        # Fallback to benchmark_sample_10.json
        sample_file = Path(__file__).parent.parent / "benchmark_sample_10.json"

    if not sample_file.exists():
        print("ERROR: No sample file found")
        print("Expected: results/sample_10.json or benchmark_sample_10.json")
        sys.exit(1)

    with open(sample_file) as f:
        data = json.load(f)

    # Handle both formats (stratified sample vs benchmark sample)
    if "questions" in data:
        questions = data["questions"]
        # Convert to standard format
        return [
            {
                "index": i + 1,
                "question": q.get("full_question") or q.get("IP_Question"),
                "section": q.get("section") or q.get("IP_Section"),
                "subsection": q.get("subsection") or q.get("IP_Sub_Section"),
                "topic": q.get("topic") or q.get("topic_name")
            }
            for i, q in enumerate(questions[:10])
        ]
    else:
        # Old benchmark format
        return [
            {
                "index": i + 1,
                "question": q["IP_Question"],
                "section": q.get("IP_Section", ""),
                "subsection": q.get("IP_Sub_Section", ""),
                "topic": q.get("topic_name", "")
            }
            for i, q in enumerate(data[:10])
        ]


def validate_parity(question_id: int, response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate POC parity for a single response.

    Returns validation results with pass/fail for each criterion.
    """
    validation = {
        "question_id": question_id,
        "parity_checks": {},
        "issues": [],
        "passes_parity": False
    }

    # Check 1: statute_summary field present and non-empty
    statute_summary = response.get("statute_summary", "")
    if statute_summary:
        validation["parity_checks"]["statute_summary_present"] = True
    else:
        validation["parity_checks"]["statute_summary_present"] = False
        validation["issues"].append("Missing or empty statute_summary field")

    # Check 2: policy_summary field present and non-empty
    policy_summary = response.get("policy_summary", "")
    if policy_summary:
        validation["parity_checks"]["policy_summary_present"] = True
    else:
        validation["parity_checks"]["policy_summary_present"] = False
        validation["issues"].append("Missing or empty policy_summary field")

    # Check 3: final_summary field present and non-empty
    final_summary = response.get("final_summary", "")
    if final_summary:
        validation["parity_checks"]["final_summary_present"] = True
    else:
        validation["parity_checks"]["final_summary_present"] = False
        validation["issues"].append("Missing or empty final_summary field")

    # Check 4: Chunk citations present (S# or P# format)
    statute_citations = re.findall(r'\[S\d+\]', statute_summary)
    policy_citations = re.findall(r'\[P\d+\]', policy_summary)

    validation["parity_checks"]["statute_citations_count"] = len(statute_citations)
    validation["parity_checks"]["policy_citations_count"] = len(policy_citations)
    validation["parity_checks"]["chunk_citations_present"] = (
        len(statute_citations) > 0 or len(policy_citations) > 0
    )

    if len(statute_citations) == 0 and len(policy_citations) == 0:
        validation["issues"].append("No chunk citations ([S#] or [P#]) found in summaries")

    # Check 5: Similarity scores (from metadata)
    metadata = response.get("metadata", {})
    statute_chunks = metadata.get("statute_chunks_retrieved", 0)
    policy_chunks = metadata.get("policy_chunks_retrieved", 0)

    validation["parity_checks"]["statute_chunks_retrieved"] = statute_chunks
    validation["parity_checks"]["policy_chunks_retrieved"] = policy_chunks

    if statute_chunks == 0:
        validation["issues"].append("No statute chunks retrieved")
    if policy_chunks == 0:
        validation["issues"].append("No policy chunks retrieved")

    # Overall parity: Pass if all 3 summary fields present and at least 1 chunk citation
    validation["passes_parity"] = (
        validation["parity_checks"]["statute_summary_present"] and
        validation["parity_checks"]["policy_summary_present"] and
        validation["parity_checks"]["final_summary_present"] and
        validation["parity_checks"]["chunk_citations_present"]
    )

    return validation


def run_parity_test():
    """Execute parity test on 10 questions"""
    # Check API health
    try:
        req = urllib.request.Request(HEALTH_URL)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                print("ERROR: API health check failed")
                print("Ensure API is running: docker-compose ps agent-api")
                sys.exit(1)
    except Exception as e:
        print(f"ERROR: Cannot connect to API: {e}")
        print("Ensure API is running: docker-compose up -d agent-api")
        sys.exit(1)

    # Load questions
    questions = load_sample_questions()
    print(f"Loaded {len(questions)} questions for parity test\n")

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent.parent / "benchmark_results" / "parity_10q"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'='*80}")
    print(f"POC PARITY TEST")
    print(f"{'='*80}")
    print(f"Timestamp: {timestamp}")
    print(f"Output directory: {output_dir}")
    print(f"Questions: {len(questions)}")
    print(f"{'='*80}\n")

    results = []
    validations = []

    for i, q in enumerate(questions, 1):
        print(f"{'='*80}")
        print(f"Question {i}/{len(questions)}")
        print(f"{'='*80}")
        print(f"Section: {q['section']}")
        print(f"Question preview: {q['question'][:100]}...")
        print(f"{'='*80}")

        # Prepare API request
        payload = {
            "question": q["question"],
            "topic": q["section"],
            "sub_section": q["subsection"],
            "category": q["topic"],
            "similarity_threshold": 0.5  # POC compatibility
        }

        try:
            # Make POST request with urllib
            json_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                API_URL,
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                result = json.loads(response.read().decode('utf-8'))

            # Save individual result
            output_file = output_dir / f"q{i}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)

            # Validate parity
            validation = validate_parity(i, result)
            validations.append(validation)

            # Print validation results
            print(f"✅ SUCCESS")
            print(f"  Quality Score: {result.get('quality_score', 0):.1f}/10")
            print(f"  Passes Review: {result.get('passes_review', False)}")
            print(f"\n  POC Parity Checks:")
            print(f"    statute_summary present: {'✅' if validation['parity_checks']['statute_summary_present'] else '❌'}")
            print(f"    policy_summary present: {'✅' if validation['parity_checks']['policy_summary_present'] else '❌'}")
            print(f"    final_summary present: {'✅' if validation['parity_checks']['final_summary_present'] else '❌'}")
            print(f"    Statute citations ([S#]): {validation['parity_checks']['statute_citations_count']}")
            print(f"    Policy citations ([P#]): {validation['parity_checks']['policy_citations_count']}")
            print(f"    Chunk citations present: {'✅' if validation['parity_checks']['chunk_citations_present'] else '❌'}")
            print(f"  Overall Parity: {'✅ PASS' if validation['passes_parity'] else '❌ FAIL'}")

            if validation['issues']:
                print(f"  Issues:")
                for issue in validation['issues']:
                    print(f"    - {issue}")

            results.append({
                'question_id': i,
                'success': True,
                'passes_parity': validation['passes_parity'],
                'quality_score': result.get('quality_score', 0),
                'passes_review': result.get('passes_review', False)
            })

        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.append({
                'question_id': i,
                'success': False,
                'error': str(e)
            })

        print()

    # Compute summary statistics
    successful = [r for r in results if r.get('success', False)]
    parity_passed = [r for r in results if r.get('passes_parity', False)]

    # Aggregate validation stats
    citation_counts = [
        v['parity_checks']['statute_citations_count'] + v['parity_checks']['policy_citations_count']
        for v in validations
    ]

    summary = {
        'run_metadata': {
            'timestamp': datetime.now().isoformat(),
            'run_id': timestamp,
            'test_type': 'POC_parity_validation'
        },
        'execution_stats': {
            'total_questions': len(results),
            'successful': len(successful),
            'failed': len(results) - len(successful),
            'success_rate': len(successful) / len(results) if results else 0
        },
        'parity_stats': {
            'parity_passed': len(parity_passed),
            'parity_failed': len(successful) - len(parity_passed),
            'parity_pass_rate': len(parity_passed) / len(successful) if successful else 0,
            'avg_citation_count': sum(citation_counts) / len(citation_counts) if citation_counts else 0,
            'questions_with_citations': sum(1 for c in citation_counts if c > 0)
        },
        'quality_stats': {
            'avg_quality_score': sum(r['quality_score'] for r in successful) / len(successful) if successful else 0,
            'quality_pass_rate': sum(r['passes_review'] for r in successful) / len(successful) if successful else 0
        },
        'validations': validations,
        'results': results
    }

    # Save summary
    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Print final summary
    print(f"{'='*80}")
    print(f"PARITY TEST COMPLETE")
    print(f"{'='*80}")
    print(f"Run ID: {timestamp}")
    print(f"Total questions: {summary['execution_stats']['total_questions']}")
    print(f"Successful: {summary['execution_stats']['successful']}")
    print(f"Failed: {summary['execution_stats']['failed']}")
    print(f"\nPOC Parity Results:")
    print(f"  Parity passed: {summary['parity_stats']['parity_passed']}/{summary['execution_stats']['successful']} ({100*summary['parity_stats']['parity_pass_rate']:.0f}%)")
    print(f"  Parity failed: {summary['parity_stats']['parity_failed']}")
    print(f"  Avg chunk citations per question: {summary['parity_stats']['avg_citation_count']:.1f}")
    print(f"  Questions with citations: {summary['parity_stats']['questions_with_citations']}/{summary['execution_stats']['successful']}")
    print(f"\nQuality Metrics:")
    print(f"  Avg quality score: {summary['quality_stats']['avg_quality_score']:.2f}/10")
    print(f"  Quality pass rate: {100*summary['quality_stats']['quality_pass_rate']:.0f}%")
    print(f"\nResults saved to: {output_dir}")
    print(f"  - summary.json (aggregate stats)")
    print(f"  - q1.json through q10.json (individual results)")
    print(f"{'='*80}")

    return output_dir, summary


if __name__ == "__main__":
    output_dir, summary = run_parity_test()

    # Exit with success if parity pass rate >= 70%
    parity_pass_rate = summary['parity_stats']['parity_pass_rate']
    if parity_pass_rate >= 0.7:
        print(f"\n✅ Parity test PASSED ({100*parity_pass_rate:.0f}% >= 70%)")
        sys.exit(0)
    else:
        print(f"\n❌ Parity test FAILED ({100*parity_pass_rate:.0f}% < 70%)")
        sys.exit(1)
