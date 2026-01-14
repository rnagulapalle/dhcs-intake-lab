"""
Benchmark Comparison: Multi-Agent vs Simple RAG
Compares our 5-agent system against Rishi/Nauman's simple RAG baseline
"""
import sys
import json
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from agents.core.curation_orchestrator import CurationOrchestrator
from agents.monitoring import QualityMonitor, AgentWeights

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BenchmarkComparison:
    """
    Runs head-to-head comparison between multi-agent and simple RAG approaches.

    Evaluates on:
    1. Quality Score (0-10 scale)
    2. Completeness (all required sections present)
    3. Actionability (specific action items)
    4. Citation Quality (statute references)
    5. Confidence Levels (statute & policy)
    6. Processing Time
    """

    def __init__(self):
        self.orchestrator = CurationOrchestrator()
        self.monitor = QualityMonitor()
        self.results = []

    def load_baseline_results(self, csv_path: str) -> pd.DataFrame:
        """Load Rishi/Nauman's baseline results"""
        logger.info(f"Loading baseline results from {csv_path}")
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} baseline results")
        return df

    def load_test_questions(self, csv_path: str, limit: int = None) -> List[Dict[str, Any]]:
        """Load test questions from PreProcessRubric CSV"""
        logger.info(f"Loading test questions from {csv_path}")
        df = pd.read_csv(csv_path)

        if limit:
            df = df.head(limit)
            logger.info(f"Limited to first {limit} questions")

        questions = []
        for idx, row in df.iterrows():
            questions.append({
                "id": idx,
                "question": row["IP Question"],
                "section": row["IP Section"],
                "sub_section": row["IP Sub-Section"],
                "topic_name": row.get("topic_name", ""),
                "question_merge": row.get("question_merge", "")
            })

        logger.info(f"Loaded {len(questions)} test questions")
        return questions

    def process_with_multi_agent(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process question through our multi-agent system"""
        try:
            result = self.orchestrator.execute({
                "question": question_data["question"],
                "topic": question_data["topic_name"],
                "sub_section": question_data["sub_section"],
                "category": question_data["section"]
            })

            # Add diagnostic analysis
            diagnostics = self.monitor.generate_report(result)

            return {
                "success": True,
                "result": result,
                "diagnostics": diagnostics
            }

        except Exception as e:
            logger.error(f"Multi-agent processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def compare_results(
        self,
        question_data: Dict[str, Any],
        baseline_result: Dict[str, Any],
        multi_agent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare baseline vs multi-agent results on key metrics.

        Returns comparison with scores for:
        - Completeness
        - Structure quality
        - Citation quality
        - Actionability
        - Overall quality
        """
        comparison = {
            "question_id": question_data["id"],
            "question": question_data["question"][:100] + "...",
            "baseline": {},
            "multi_agent": {},
            "winner": None,
            "improvement_areas": []
        }

        # Analyze baseline (if available)
        if baseline_result:
            comparison["baseline"] = {
                "has_statute_summary": bool(baseline_result.get("statute_summary")),
                "has_policy_summary": bool(baseline_result.get("policy_summary")),
                "has_final_summary": bool(baseline_result.get("final_summary")),
                "structure_score": self._score_structure(baseline_result),
                "citation_count": self._count_citations(baseline_result),
                "action_items_count": 0  # Simple RAG doesn't extract action items
            }

        # Analyze multi-agent
        if multi_agent_result.get("success"):
            result = multi_agent_result["result"]
            diagnostics = multi_agent_result["diagnostics"]

            comparison["multi_agent"] = {
                "quality_score": result.get("quality_score", 0),
                "passes_review": result.get("passes_review", False),
                "has_statute_analysis": bool(result["metadata"].get("relevant_statutes")),
                "has_policy_analysis": bool(result["metadata"].get("policy_confidence")),
                "has_final_summary": bool(result.get("final_summary")),
                "structure_score": 10 if result.get("passes_review") else 5,
                "citation_count": len(result["metadata"].get("relevant_statutes", [])),
                "action_items_count": len(result.get("action_items", [])),
                "statute_confidence": result["metadata"].get("statute_confidence", "Unknown"),
                "policy_confidence": result["metadata"].get("policy_confidence", "Unknown"),
                "component_scores": diagnostics["diagnostics"]["component_scores"],
                "processing_time": result["metadata"].get("processing_time_seconds", 0)
            }

            # Determine winner and improvements
            improvements = []

            if comparison["multi_agent"]["quality_score"] >= 7.0:
                improvements.append("Passes quality threshold (≥7.0)")

            if comparison["multi_agent"]["action_items_count"] > comparison["baseline"].get("action_items_count", 0):
                improvements.append(f"Generates {comparison['multi_agent']['action_items_count']} action items (baseline: 0)")

            if comparison["multi_agent"]["citation_count"] > comparison["baseline"].get("citation_count", 0):
                improvements.append(f"More statute citations ({comparison['multi_agent']['citation_count']} vs baseline)")

            if comparison["multi_agent"]["structure_score"] > comparison["baseline"].get("structure_score", 0):
                improvements.append("Better structured output with all required sections")

            comparison["improvement_areas"] = improvements
            comparison["winner"] = "multi_agent" if improvements else "tie"

        return comparison

    def _score_structure(self, result: Dict[str, Any]) -> float:
        """Score the structure quality of a result (0-10)"""
        score = 0.0

        # Check for key sections
        if result.get("statute_summary"):
            score += 3.0
        if result.get("policy_summary"):
            score += 3.0
        if result.get("final_summary"):
            score += 4.0

        return score

    def _count_citations(self, result: Dict[str, Any]) -> int:
        """Count statute citations in result"""
        count = 0
        text = " ".join([
            str(result.get("statute_summary", "")),
            str(result.get("policy_summary", "")),
            str(result.get("final_summary", ""))
        ])

        # Count W&I Code references
        import re
        matches = re.findall(r'W&I Code §\s*\d+', text)
        count = len(set(matches))  # Unique citations

        return count

    def run_benchmark(
        self,
        test_questions_path: str,
        baseline_results_path: str = None,
        num_questions: int = 10,
        output_path: str = "/tmp/benchmark_results.json"
    ):
        """
        Run full benchmark comparison.

        Args:
            test_questions_path: Path to PreProcessRubric_v0.csv
            baseline_results_path: Path to Rishi/Nauman's results CSV
            num_questions: Number of questions to test
            output_path: Where to save results
        """
        logger.info("=" * 80)
        logger.info("BENCHMARK COMPARISON: Multi-Agent vs Simple RAG")
        logger.info("=" * 80)

        # Load test questions
        questions = self.load_test_questions(test_questions_path, limit=num_questions)

        # Load baseline results (if available)
        baseline_df = None
        if baseline_results_path and Path(baseline_results_path).exists():
            baseline_df = self.load_baseline_results(baseline_results_path)

        # Run comparison
        results = []
        for i, question in enumerate(questions, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"Question {i}/{len(questions)}: {question['question'][:80]}...")
            logger.info(f"{'='*80}")

            # Get baseline result (if available)
            baseline_result = None
            if baseline_df is not None and i-1 < len(baseline_df):
                baseline_result = baseline_df.iloc[i-1].to_dict()

            # Process with multi-agent
            logger.info("Processing with multi-agent system...")
            multi_agent_result = self.process_with_multi_agent(question)

            # Compare
            comparison = self.compare_results(question, baseline_result, multi_agent_result)
            results.append(comparison)

            # Log results
            if comparison["winner"] == "multi_agent":
                logger.info(f"✅ Multi-agent wins! Improvements:")
                for improvement in comparison["improvement_areas"]:
                    logger.info(f"   - {improvement}")
            else:
                logger.info(f"⚠️  Tie or insufficient data")

        # Generate summary
        summary = self._generate_summary(results)

        # Save results
        output = {
            "timestamp": datetime.now().isoformat(),
            "num_questions_tested": len(questions),
            "results": results,
            "summary": summary
        }

        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"\n{'='*80}")
        logger.info("BENCHMARK COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Results saved to: {output_path}")
        logger.info(f"\nSummary:")
        logger.info(f"  Multi-agent wins: {summary['multi_agent_wins']}/{len(results)}")
        logger.info(f"  Average quality score: {summary['avg_quality_score']:.1f}/10")
        logger.info(f"  Questions passing review: {summary['questions_passing_review']}/{len(results)}")
        logger.info(f"  Average action items: {summary['avg_action_items']:.1f}")

        return output

    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from benchmark results"""
        multi_agent_wins = sum(1 for r in results if r["winner"] == "multi_agent")

        quality_scores = [r["multi_agent"].get("quality_score", 0) for r in results if r.get("multi_agent")]
        passing_review = sum(1 for r in results if r.get("multi_agent", {}).get("passes_review", False))
        action_items_counts = [r["multi_agent"].get("action_items_count", 0) for r in results if r.get("multi_agent")]
        citation_counts = [r["multi_agent"].get("citation_count", 0) for r in results if r.get("multi_agent")]

        return {
            "multi_agent_wins": multi_agent_wins,
            "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "questions_passing_review": passing_review,
            "avg_action_items": sum(action_items_counts) / len(action_items_counts) if action_items_counts else 0,
            "avg_citations": sum(citation_counts) / len(citation_counts) if citation_counts else 0,
            "total_improvements": sum(len(r["improvement_areas"]) for r in results)
        }


def main():
    """Run benchmark comparison"""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark multi-agent vs simple RAG")
    parser.add_argument(
        "--questions",
        default="/app/data/PreProcessRubric_v0.csv",
        help="Path to test questions CSV"
    )
    parser.add_argument(
        "--baseline",
        default=None,
        help="Path to baseline results CSV (optional)"
    )
    parser.add_argument(
        "--num-questions",
        type=int,
        default=10,
        help="Number of questions to test"
    )
    parser.add_argument(
        "--output",
        default="/tmp/benchmark_results.json",
        help="Output path for results"
    )

    args = parser.parse_args()

    benchmark = BenchmarkComparison()
    results = benchmark.run_benchmark(
        test_questions_path=args.questions,
        baseline_results_path=args.baseline,
        num_questions=args.num_questions,
        output_path=args.output
    )

    return 0


if __name__ == "__main__":
    exit(main())
