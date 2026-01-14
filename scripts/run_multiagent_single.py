"""
Single-question runner for Multi-Agent system
Uses API endpoint
"""
import requests
import json
import argparse

def run_multiagent_question(question: str, topic: str = "", section: str = "") -> dict:
    """Run multi-agent system via API"""

    payload = {
        "question": question,
        "topic": topic if topic else section,
        "sub_section": section if section else "",
        "category": "Benchmark"
    }

    print(f"Calling multi-agent API...")
    response = requests.post(
        "http://localhost:8000/curation/process",
        json=payload,
        timeout=300  # 5 minutes
    )

    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")

    result = response.json()
    print(f"  Quality score: {result.get('quality_score', 0):.1f}/10")
    print(f"  Passes review: {result.get('passes_review', False)}")
    print(f"  Revisions: {result.get('metadata', {}).get('revision_count', 0)}")

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--topic", default="")
    parser.add_argument("--section", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = run_multiagent_question(args.question, args.topic, args.section)

    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nSaved to: {args.output}")
