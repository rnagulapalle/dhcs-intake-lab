"""
Select 10 diverse questions from nova_micro.xlsx for benchmark
"""
import pandas as pd
import json
from pathlib import Path

def select_benchmark_sample(excel_path: str, output_path: str, n: int = 10):
    """
    Select n diverse questions across sections and score ranges
    """
    df = pd.read_excel(excel_path)

    print(f"Total questions: {len(df)}")
    print(f"Score distribution:\n{df['score'].describe()}")

    # Check if policy_manual_section exists as proxy for section
    section_col = 'policy_manual_section' if 'policy_manual_section' in df.columns else None
    if section_col:
        print(f"\nSections (policy_manual_section):\n{df[section_col].value_counts().head(10)}")

    # Strategy: Sample across score quartiles
    df['score_quartile'] = pd.qcut(df['score'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'], duplicates='drop')

    # Get diverse sample
    selected = []

    # Try to get 2-3 questions per quartile
    for quartile in ['Q1', 'Q2', 'Q3', 'Q4']:
        q_df = df[df['score_quartile'] == quartile]
        # Sample up to 3 from this quartile
        if len(q_df) > 0:
            sample_size = min(3, len(q_df), n - len(selected))
            if sample_size > 0:
                # Try to diversify by section if available
                if section_col and section_col in q_df.columns:
                    sampled = q_df.groupby(section_col, group_keys=False).apply(
                        lambda x: x.sample(min(1, len(x)))
                    ).head(sample_size)
                else:
                    sampled = q_df.sample(sample_size)
                selected.extend(sampled.index.tolist())

    # If we didn't get enough, randomly sample remaining
    if len(selected) < n:
        remaining = df[~df.index.isin(selected)]
        extra = remaining.sample(n - len(selected))
        selected.extend(extra.index.tolist())

    selected = selected[:n]

    # Extract selected questions
    sample_df = df.loc[selected].copy()

    # Create output records
    records = []
    for idx, row in sample_df.iterrows():
        records.append({
            'index': int(idx),
            'QuestionId': int(row['QuestionId']) if pd.notna(row['QuestionId']) else None,
            'score': float(row['score']),
            'score_quartile': str(row['score_quartile']),
            'IP_Question': str(row['IP Question']),
            'policy_manual_section': str(row['policy_manual_section']) if pd.notna(row['policy_manual_section']) else ''
        })

    # Save to JSON
    output = {
        'total_questions': len(df),
        'sample_size': len(records),
        'selection_strategy': 'stratified by score quartile and section diversity',
        'questions': records
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nSelected {len(records)} questions:")
    for r in records:
        print(f"  [{r['index']}] Score: {r['score']:.0f} | Q{r['score_quartile']} | {r['policy_manual_section'][:30] if r['policy_manual_section'] else 'N/A'}")
        print(f"      Question: {r['IP_Question'][:80]}...")

    print(f"\nSaved to: {output_path}")
    return records

if __name__ == "__main__":
    excel_path = "/Users/raj/dhcs-intake-lab/docs/archive/policy_context_batch_nova_micro.xlsx"
    output_path = "/Users/raj/dhcs-intake-lab/benchmark_sample_10.json"

    select_benchmark_sample(excel_path, output_path, n=10)
