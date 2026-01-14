"""
LLM-as-Judge Scorer for Policy Curation Outputs
Evaluates outputs on 0-100 scale matching nova_micro rubric
"""
import json
import os
from pathlib import Path
from typing import Dict, Any
from openai import OpenAI

# Load API key
from dotenv import load_dotenv
load_dotenv("/Users/raj/dhcs-intake-lab/.env")

JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator for county behavioral health policy curation outputs.

Your task is to score the quality of a policy curation response on a 0-100 scale based on these criteria:

**SCORING RUBRIC (0-100 points):**

**Strong Response (70-100 points):**
- Accurately identifies all relevant statutes and policy requirements
- Provides specific, actionable guidance for county staff
- Includes exact citations (W&I Code sections, policy manual sections)
- Addresses all aspects of the question comprehensively
- Clear, well-organized, and easy to follow
- No hallucinations or incorrect information

**Moderate Response (40-69 points):**
- Identifies some relevant requirements but misses key details
- Provides general guidance but lacks specificity
- Some citations present but incomplete
- Addresses question partially
- Organization could be improved
- Minor inaccuracies

**Weak Response (0-39 points):**
- Misses major requirements
- Vague or generic guidance
- Few or no citations
- Does not adequately address the question
- Poorly organized or confusing
- Contains significant errors or hallucinations

---

**QUESTION:**
{question}

**POLICY MANUAL SECTION:**
{policy_section}

**GROUND TRUTH SCORE (for reference):**
{ground_truth_score}/100 (previous evaluation by human expert)

---

**SYSTEM OUTPUT TO EVALUATE:**

{output_text}

---

**YOUR EVALUATION:**

Please provide:
1. **Score (0-100):** [integer]
2. **Justification (2-3 sentences):** Why this score?
3. **Strengths (bullet list):** What did the output do well?
4. **Weaknesses (bullet list):** What could be improved?
5. **Alignment with Ground Truth:** Does your score align with the {ground_truth_score}/100 reference score? If not, why?

Format your response as JSON:
{{
  "score": <integer 0-100>,
  "justification": "<text>",
  "strengths": ["<item 1>", "<item 2>", ...],
  "weaknesses": ["<item 1>", "<item 2>", ...],
  "alignment_analysis": "<text>"
}}
"""

def score_output_with_llm_judge(
    question: str,
    policy_section: str,
    output_text: str,
    ground_truth_score: float
) -> Dict[str, Any]:
    """
    Use OpenAI GPT-4 as LLM judge to score output
    """

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        question=question,
        policy_section=policy_section,
        output_text=output_text,
        ground_truth_score=int(ground_truth_score)
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.choices[0].message.content

        # Try to extract JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "{" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_text = response_text[json_start:json_end]
        else:
            json_text = response_text

        evaluation = json.loads(json_text)
        return evaluation

    except Exception as e:
        return {
            "score": 0,
            "justification": f"LLM judge error: {str(e)}",
            "strengths": [],
            "weaknesses": ["Judge evaluation failed"],
            "alignment_analysis": "N/A",
            "error": str(e)
        }

def evaluate_multiagent_outputs(results_dir: Path, sample_file: Path) -> Dict[str, Any]:
    """
    Evaluate all multi-agent outputs using LLM judge
    """

    # Load sample questions
    with open(sample_file) as f:
        sample = json.load(f)

    questions_map = {q['index']: q for q in sample['questions']}

    # Evaluate each output
    evaluations = []

    for q_id, q_data in questions_map.items():
        output_file = results_dir / f"q{q_id}.json"

        if not output_file.exists():
            print(f"⚠️  Skipping Q{q_id}: output file not found")
            continue

        with open(output_file) as f:
            output_data = json.load(f)

        # Extract output text for judging
        final_summary = output_data.get('final_summary', '')
        if not final_summary:
            final_response = output_data.get('final_response', '')
            final_summary = final_response

        print(f"Evaluating Q{q_id} (GT Score: {q_data['score']:.0f})...")

        evaluation = score_output_with_llm_judge(
            question=q_data['IP_Question'],
            policy_section=q_data['policy_manual_section'],
            output_text=final_summary,
            ground_truth_score=q_data['score']
        )

        evaluations.append({
            'question_id': q_id,
            'ground_truth_score': q_data['score'],
            'system_quality_score': output_data.get('quality_score', 0),
            'llm_judge_score': evaluation.get('score', 0),
            'llm_judge_justification': evaluation.get('justification', ''),
            'strengths': evaluation.get('strengths', []),
            'weaknesses': evaluation.get('weaknesses', []),
            'alignment_analysis': evaluation.get('alignment_analysis', '')
        })

        print(f"  LLM Judge Score: {evaluation.get('score', 0)}/100")
        print(f"  System Quality: {output_data.get('quality_score', 0):.1f}/10")
        print()

    # Summary statistics
    summary = {
        'total_evaluated': len(evaluations),
        'avg_llm_judge_score': sum(e['llm_judge_score'] for e in evaluations) / len(evaluations),
        'avg_system_quality_score': sum(e['system_quality_score'] for e in evaluations) / len(evaluations),
        'avg_ground_truth_score': sum(e['ground_truth_score'] for e in evaluations) / len(evaluations),
        'evaluations': evaluations
    }

    return summary

if __name__ == "__main__":
    results_dir = Path("/Users/raj/dhcs-intake-lab/benchmark_results/multiagent_10q")
    sample_file = Path("/Users/raj/dhcs-intake-lab/benchmark_sample_10.json")

    print("LLM-as-Judge Evaluation Starting...\n")

    summary = evaluate_multiagent_outputs(results_dir, sample_file)

    # Save results
    output_file = results_dir / "llm_judge_evaluation.json"
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print("="*80)
    print("LLM JUDGE SUMMARY")
    print("="*80)
    print(f"Questions Evaluated: {summary['total_evaluated']}")
    print(f"Avg LLM Judge Score: {summary['avg_llm_judge_score']:.1f}/100")
    print(f"Avg System Quality Score: {summary['avg_system_quality_score']:.1f}/10 ({summary['avg_system_quality_score']*10:.1f}/100 scaled)")
    print(f"Avg Ground Truth Score: {summary['avg_ground_truth_score']:.1f}/100")
    print(f"\nResults saved to: {output_file}")
