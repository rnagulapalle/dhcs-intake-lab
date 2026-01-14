"""
Stratified Sampling for 10-Question Benchmark

Selects 10 questions from PreProcessRubric_v0.csv using stratified sampling across:
- IP Sections (major categories)
- Topic Names (content type)
- Score distribution (if available)

Methodology:
1. Major section stratification (ensure coverage of top sections)
2. Within-section diversity (different sub-sections and topics)
3. Deterministic sampling (seeded for reproducibility)

Output: results/sample_10.json with full manifest
"""
import csv
import json
import random
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

# Deterministic seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

def load_rubric(csv_path):
    """Load PreProcessRubric_v0.csv"""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Filter out empty rows
    rows = [r for r in rows if r.get('IP Question') and r.get('IP Section')]

    print(f"Loaded {len(rows)} valid questions from rubric")
    return rows

def analyze_distribution(rows):
    """Analyze section and topic distribution"""
    sections = Counter([r['IP Section'] for r in rows])
    topics = Counter([r['topic_name'] for r in rows])

    print(f"\n=== Distribution Analysis ===")
    print(f"Total questions: {len(rows)}")
    print(f"Unique sections: {len(sections)}")
    print(f"Unique topics: {len(topics)}")

    print(f"\n=== Top 5 Sections ===")
    for section, count in sections.most_common(5):
        pct = 100 * count / len(rows)
        print(f"  {count:3d} ({pct:5.1f}%)  {section[:60]}")

    print(f"\n=== All Topics ===")
    for topic, count in topics.most_common():
        pct = 100 * count / len(rows)
        print(f"  {count:3d} ({pct:5.1f}%)  {topic}")

    return sections, topics

def stratified_sample_10(rows):
    """
    Select 10 questions using stratified sampling.

    Strategy:
    1. Major sections: Allocate slots proportionally to section size
    2. Within section: Diversify by sub-section and topic
    3. Deterministic: Use seeded random sampling

    Target distribution (10 questions):
    - Behavioral Health Services Act/Fund Programs: 4 questions (38% of data)
    - Statewide Behavioral Health Goals: 2 questions (22% of data)
    - County Behavioral Health System Overview: 1 question (9% of data)
    - Plan Approval and Compliance: 1 question (9% of data)
    - Other categories: 2 questions (22% of data)
    """

    # Group by section
    by_section = defaultdict(list)
    for r in rows:
        by_section[r['IP Section']].append(r)

    # Calculate proportional allocation
    total = len(rows)
    section_sizes = {section: len(questions) for section, questions in by_section.items()}

    print(f"\n=== Stratified Allocation ===")

    # Define target allocation (sum = 10)
    allocation = {
        'Behavioral Health Services Act/Fund Programs': 4,
        'Statewide Behavioral Health Goals': 2,
        'County Behavioral Health System Overview': 1,
        'Plan Approval and  Compliance': 1,  # Note: extra space in data
        'Other': 2  # Remaining from smaller sections
    }

    selected = []
    used_subsections = set()

    # Sample from each allocated section
    for section, target_count in allocation.items():
        if section == 'Other':
            # Sample from smaller sections
            small_sections = [s for s in by_section.keys()
                            if s not in allocation or allocation.get(s) == 0]
            for _ in range(target_count):
                # Pick a random small section
                section_name = random.choice(small_sections)
                candidates = by_section[section_name]

                # Filter out questions from already-used sub-sections (for diversity)
                diverse_candidates = [q for q in candidates
                                     if q['IP Sub-Section'] not in used_subsections]

                if diverse_candidates:
                    question = random.choice(diverse_candidates)
                else:
                    question = random.choice(candidates)

                selected.append(question)
                used_subsections.add(question['IP Sub-Section'])
                print(f"  {len(selected):2d}. [{section_name[:40]}...] {question['IP Question'][:60]}...")
        else:
            # Sample from specific section
            candidates = by_section.get(section, [])

            if not candidates:
                print(f"  WARNING: Section '{section}' not found, skipping")
                continue

            # Diversify by sub-section within this section
            subsection_groups = defaultdict(list)
            for q in candidates:
                subsection_groups[q['IP Sub-Section']].append(q)

            # Sample from different sub-sections when possible
            sampled = 0
            available_subsections = list(subsection_groups.keys())
            random.shuffle(available_subsections)

            for subsection in available_subsections:
                if sampled >= target_count:
                    break

                # Skip if we already have a question from this sub-section
                if subsection in used_subsections:
                    continue

                question = random.choice(subsection_groups[subsection])
                selected.append(question)
                used_subsections.add(subsection)
                sampled += 1

                print(f"  {len(selected):2d}. [{section[:40]}] {question['IP Question'][:60]}...")

            # If we didn't get enough diverse questions, fill with any remaining
            while sampled < target_count and candidates:
                remaining = [q for q in candidates
                           if q not in selected]
                if not remaining:
                    break
                question = random.choice(remaining)
                selected.append(question)
                sampled += 1
                print(f"  {len(selected):2d}. [{section[:40]}] (fallback) {question['IP Question'][:60]}...")

    return selected

def generate_manifest(selected, total_questions):
    """Generate sampling manifest"""

    # Analyze selected sample
    sections = Counter([q['IP Section'] for q in selected])
    topics = Counter([q['topic_name'] for q in selected])
    subsections = Counter([q['IP Sub-Section'] for q in selected])

    manifest = {
        "sampling_metadata": {
            "timestamp": datetime.now().isoformat(),
            "source_file": "data/PreProcessRubric_v0.csv",
            "total_questions_in_source": total_questions,
            "sample_size": len(selected),
            "random_seed": RANDOM_SEED,
            "sampling_method": "stratified_by_section_and_diversity"
        },
        "stratification_strategy": {
            "description": "Proportional allocation to major sections, with within-section diversification by sub-section and topic",
            "target_allocation": {
                "Behavioral Health Services Act/Fund Programs": "4 questions (38% of source data)",
                "Statewide Behavioral Health Goals": "2 questions (22% of source data)",
                "County Behavioral Health System Overview": "1 question (9% of source data)",
                "Plan Approval and Compliance": "1 question (9% of source data)",
                "Other smaller sections": "2 questions (22% of source data)"
            },
            "diversification": "Within each section, selected from different sub-sections to maximize coverage"
        },
        "sample_distribution": {
            "by_section": dict(sections),
            "by_topic": dict(topics),
            "unique_subsections": len(subsections)
        },
        "questions": []
    }

    # Add question details
    for i, q in enumerate(selected, 1):
        manifest["questions"].append({
            "sample_index": i,
            "source_index": int(q['']) if q.get('') else None,  # CSV row index
            "question_id": q.get('Sorting Column to Mirror Order in Portal', ''),
            "section": q['IP Section'],
            "subsection": q['IP Sub-Section'],
            "topic": q['topic_name'],
            "question_preview": q['IP Question'][:100] + "..." if len(q['IP Question']) > 100 else q['IP Question'],
            "full_question": q['IP Question']
        })

    return manifest

def main():
    print("="*80)
    print("STRATIFIED 10-QUESTION SAMPLE SELECTION")
    print("="*80)

    # Load data
    csv_path = Path(__file__).parent.parent / "data" / "PreProcessRubric_v0.csv"
    rows = load_rubric(csv_path)

    # Analyze distribution
    sections, topics = analyze_distribution(rows)

    # Perform stratified sampling
    print(f"\n=== Selecting 10 Questions ===")
    selected = stratified_sample_10(rows)

    print(f"\n=== Sample Selected: {len(selected)} questions ===")

    # Generate manifest
    manifest = generate_manifest(selected, len(rows))

    # Save to results/sample_10.json
    output_dir = Path(__file__).parent.parent / "results"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "sample_10.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n=== Output ===")
    print(f"Saved to: {output_file}")
    print(f"\nManifest includes:")
    print(f"  - Sampling methodology and seed (SEED={RANDOM_SEED})")
    print(f"  - Stratification strategy")
    print(f"  - Distribution analysis")
    print(f"  - Full question details")

    # Print summary
    print(f"\n=== Sample Summary ===")
    print(f"Sections represented: {len(manifest['sample_distribution']['by_section'])}")
    print(f"Topics represented: {len(manifest['sample_distribution']['by_topic'])}")
    print(f"Unique sub-sections: {manifest['sample_distribution']['unique_subsections']}")

    print(f"\n=== Section Distribution ===")
    for section, count in manifest['sample_distribution']['by_section'].items():
        print(f"  {count} - {section[:60]}")

    print(f"\n=== Topic Distribution ===")
    for topic, count in manifest['sample_distribution']['by_topic'].items():
        print(f"  {count} - {topic}")

    print(f"\n{'='*80}")
    print("COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
