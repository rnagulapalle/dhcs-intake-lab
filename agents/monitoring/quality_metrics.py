"""
Quality Metrics and Monitoring System
Provides precision, recall, confidence intervals, and diagnostic capabilities
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval quality (Precision/Recall)"""
    total_retrieved: int
    relevant_count: int  # How many retrieved docs were actually relevant
    total_relevant_available: int  # How many relevant docs exist in DB

    @property
    def precision(self) -> float:
        """Precision = Relevant Retrieved / Total Retrieved"""
        if self.total_retrieved == 0:
            return 0.0
        return self.relevant_count / self.total_retrieved

    @property
    def recall(self) -> float:
        """Recall = Relevant Retrieved / Total Relevant Available"""
        if self.total_relevant_available == 0:
            return 0.0
        return self.relevant_count / self.total_relevant_available

    @property
    def f1_score(self) -> float:
        """F1 = 2 * (Precision * Recall) / (Precision + Recall)"""
        p, r = self.precision, self.recall
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with computed metrics"""
        return {
            **asdict(self),
            "precision": round(self.precision, 3),
            "recall": round(self.recall, 3),
            "f1_score": round(self.f1_score, 3)
        }


@dataclass
class QualityScore:
    """Quality score with confidence interval"""
    score: float
    criteria_scores: Dict[str, float]
    sample_size: int = 1

    @property
    def mean(self) -> float:
        """Mean score"""
        return self.score

    @property
    def confidence_interval_95(self) -> tuple[float, float]:
        """95% confidence interval using t-distribution approximation"""
        if self.sample_size < 2:
            return (self.score, self.score)

        # Simple approximation: score ± 1.96 * std_dev / sqrt(n)
        # For now, use criteria score variance as proxy
        scores = list(self.criteria_scores.values())
        if len(scores) < 2:
            return (self.score, self.score)

        std_dev = statistics.stdev(scores)
        margin = 1.96 * std_dev / (self.sample_size ** 0.5)
        return (
            max(0.0, self.score - margin),
            min(10.0, self.score + margin)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with confidence interval"""
        ci_low, ci_high = self.confidence_interval_95
        return {
            "score": round(self.score, 2),
            "criteria_scores": {k: round(v, 2) for k, v in self.criteria_scores.items()},
            "confidence_interval_95": {
                "lower": round(ci_low, 2),
                "upper": round(ci_high, 2),
                "margin": round((ci_high - ci_low) / 2, 2)
            },
            "sample_size": self.sample_size
        }


@dataclass
class AgentWeights:
    """Configurable weights for different components"""
    retrieval_weight: float = 0.25  # How much retrieval quality matters
    statute_analysis_weight: float = 0.25  # Statute analysis importance
    policy_analysis_weight: float = 0.25  # Policy analysis importance
    synthesis_weight: float = 0.15  # Synthesis quality importance
    quality_review_weight: float = 0.10  # Quality review strictness

    def validate(self) -> bool:
        """Ensure weights sum to 1.0"""
        total = (
            self.retrieval_weight +
            self.statute_analysis_weight +
            self.policy_analysis_weight +
            self.synthesis_weight +
            self.quality_review_weight
        )
        return abs(total - 1.0) < 0.01

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return asdict(self)


class RootCauseAnalyzer:
    """
    Diagnoses root causes of low quality scores.

    Identifies which component is the bottleneck:
    - Poor retrieval (low precision/recall)
    - Weak statute analysis (placeholders, low confidence)
    - Weak policy analysis (missing sections, low confidence)
    - Poor synthesis (lacks clarity, missing action items)
    - Strict quality review (high threshold, many issues)
    """

    def __init__(self):
        self.weights = AgentWeights()

    def diagnose(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze workflow result and identify bottlenecks.

        Args:
            workflow_result: Complete workflow output with all agent results

        Returns:
            Diagnostic report with:
            - root_cause: Primary issue
            - component_scores: Breakdown by component
            - recommendations: Specific improvement actions
            - severity: critical/high/medium/low
        """
        issues = []
        component_scores = {}

        # 1. Analyze Retrieval Quality
        retrieval_meta = workflow_result.get("metadata", {})
        statute_chunks = retrieval_meta.get("statute_chunks_retrieved", 0)
        policy_chunks = retrieval_meta.get("policy_chunks_retrieved", 0)

        if statute_chunks == 0:
            issues.append({
                "component": "retrieval",
                "severity": "critical",
                "issue": "No statute chunks retrieved",
                "recommendation": "Check statute loading, verify ChromaDB contains statutes"
            })
            component_scores["retrieval"] = 0.0
        elif statute_chunks < 5:
            issues.append({
                "component": "retrieval",
                "severity": "high",
                "issue": f"Only {statute_chunks} statute chunks retrieved (expected 5-10)",
                "recommendation": "Improve query formulation or increase top_k parameter"
            })
            component_scores["retrieval"] = 0.5
        else:
            component_scores["retrieval"] = 0.8

        if policy_chunks == 0:
            issues.append({
                "component": "retrieval",
                "severity": "critical",
                "issue": "No policy chunks retrieved",
                "recommendation": "Check policy manual loading, verify metadata filters"
            })
            component_scores["retrieval"] = min(component_scores.get("retrieval", 0.0), 0.0)
        elif policy_chunks < 5:
            issues.append({
                "component": "retrieval",
                "severity": "medium",
                "issue": f"Only {policy_chunks} policy chunks retrieved (expected 5-10)",
                "recommendation": "Review policy manual sections, improve chunking strategy"
            })
            component_scores["retrieval"] = min(component_scores.get("retrieval", 0.5), 0.6)

        # 2. Analyze Statute Analysis Quality
        statute_confidence = retrieval_meta.get("statute_confidence", "Unknown")
        relevant_statutes = retrieval_meta.get("relevant_statutes", [])

        if statute_confidence == "Low":
            issues.append({
                "component": "statute_analysis",
                "severity": "critical",
                "issue": "Statute analysis confidence is Low",
                "recommendation": "Replace placeholder statutes with actual W&I Code texts"
            })
            component_scores["statute_analysis"] = 0.2
        elif statute_confidence == "Medium":
            component_scores["statute_analysis"] = 0.6
        else:  # High
            component_scores["statute_analysis"] = 0.9

        if len(relevant_statutes) == 0:
            issues.append({
                "component": "statute_analysis",
                "severity": "high",
                "issue": "No relevant statutes identified",
                "recommendation": "Improve statute retrieval or statute catalog quality"
            })
            component_scores["statute_analysis"] = 0.0

        # 3. Analyze Policy Analysis Quality
        policy_confidence = retrieval_meta.get("policy_confidence", "Unknown")

        if policy_confidence == "Low":
            issues.append({
                "component": "policy_analysis",
                "severity": "high",
                "issue": "Policy analysis confidence is Low",
                "recommendation": "Review policy manual completeness, improve chunking/metadata"
            })
            component_scores["policy_analysis"] = 0.3
        elif policy_confidence == "Medium":
            component_scores["policy_analysis"] = 0.7
        else:  # High
            component_scores["policy_analysis"] = 0.9

        # 4. Analyze Synthesis Quality
        action_items = workflow_result.get("action_items", [])
        priority = workflow_result.get("priority", "Unknown")

        if len(action_items) == 0:
            issues.append({
                "component": "synthesis",
                "severity": "high",
                "issue": "No action items generated",
                "recommendation": "Review synthesis prompt, ensure action item extraction works"
            })
            component_scores["synthesis"] = 0.2
        elif len(action_items) < 2:
            issues.append({
                "component": "synthesis",
                "severity": "medium",
                "issue": f"Only {len(action_items)} action item generated (expected 2-5)",
                "recommendation": "Improve synthesis prompt to generate more specific actions"
            })
            component_scores["synthesis"] = 0.5
        else:
            component_scores["synthesis"] = 0.8

        if priority == "Unknown" or not priority:
            issues.append({
                "component": "synthesis",
                "severity": "medium",
                "issue": "Priority not assigned",
                "recommendation": "Ensure synthesis agent sets priority based on compliance risk"
            })
            component_scores["synthesis"] = min(component_scores.get("synthesis", 0.5), 0.6)

        # 5. Analyze Quality Review
        quality_score = workflow_result.get("quality_score", 0.0)
        passes_review = workflow_result.get("passes_review", False)
        revision_count = retrieval_meta.get("revision_count", 0)
        quality_issues = retrieval_meta.get("quality_issues", [])

        if quality_score == 0.0 and len(quality_issues) == 0:
            issues.append({
                "component": "quality_review",
                "severity": "critical",
                "issue": "Quality review returning 0.0 with no issues (likely crashing)",
                "recommendation": "Check quality_reviewer_agent logs for exceptions, verify prompt template"
            })
            component_scores["quality_review"] = 0.0
        elif not passes_review and revision_count >= 2:
            issues.append({
                "component": "quality_review",
                "severity": "high",
                "issue": f"Quality review failed after {revision_count} revisions",
                "recommendation": "Lower quality threshold or improve upstream components"
            })
            component_scores["quality_review"] = 0.4
        else:
            component_scores["quality_review"] = 0.8

        # Determine root cause (lowest scoring component)
        if component_scores:
            root_cause_component = min(component_scores.items(), key=lambda x: x[1])
            root_cause = {
                "component": root_cause_component[0],
                "score": round(root_cause_component[1], 2),
                "primary_issue": next(
                    (i for i in issues if i["component"] == root_cause_component[0]),
                    {"issue": "Component underperforming", "recommendation": "Review component implementation"}
                )
            }
        else:
            root_cause = {
                "component": "unknown",
                "score": 0.0,
                "primary_issue": {"issue": "Insufficient data for diagnosis", "recommendation": "Run workflow with detailed logging"}
            }

        # Calculate weighted overall score
        weighted_score = sum(
            component_scores.get(comp, 0.0) * weight
            for comp, weight in {
                "retrieval": self.weights.retrieval_weight,
                "statute_analysis": self.weights.statute_analysis_weight,
                "policy_analysis": self.weights.policy_analysis_weight,
                "synthesis": self.weights.synthesis_weight,
                "quality_review": self.weights.quality_review_weight
            }.items()
        )

        # Determine overall severity
        if weighted_score < 0.3:
            severity = "critical"
        elif weighted_score < 0.5:
            severity = "high"
        elif weighted_score < 0.7:
            severity = "medium"
        else:
            severity = "low"

        return {
            "root_cause": root_cause,
            "component_scores": {k: round(v, 2) for k, v in component_scores.items()},
            "weighted_overall_score": round(weighted_score, 2),
            "severity": severity,
            "issues": issues,
            "weights_used": self.weights.to_dict(),
            "recommendations_summary": self._generate_recommendations_summary(issues, root_cause)
        }

    def _generate_recommendations_summary(
        self,
        issues: List[Dict[str, Any]],
        root_cause: Dict[str, Any]
    ) -> List[str]:
        """Generate prioritized list of recommendations"""
        recommendations = []

        # Add root cause recommendation first
        if "primary_issue" in root_cause:
            recommendations.append(
                f"[PRIORITY] {root_cause['component']}: "
                f"{root_cause['primary_issue'].get('recommendation', 'Investigate component')}"
            )

        # Add other critical/high issues
        for issue in issues:
            if issue["severity"] in ["critical", "high"] and issue["component"] != root_cause["component"]:
                recommendations.append(
                    f"[{issue['severity'].upper()}] {issue['component']}: {issue['recommendation']}"
                )

        return recommendations


class QualityMonitor:
    """
    Central monitoring system for the curation pipeline.

    Tracks:
    - Retrieval metrics (precision/recall)
    - Quality scores with confidence intervals
    - Component-level diagnostics
    - Root cause analysis
    """

    def __init__(self, weights: Optional[AgentWeights] = None):
        self.weights = weights or AgentWeights()
        self.analyzer = RootCauseAnalyzer()
        self.analyzer.weights = self.weights

        logger.info("Quality monitoring system initialized")

    def generate_report(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive quality report.

        Args:
            workflow_result: Complete workflow output

        Returns:
            Full diagnostic report with metrics, diagnostics, and recommendations
        """
        # Run root cause analysis
        diagnostics = self.analyzer.diagnose(workflow_result)

        # Extract quality score with confidence interval
        quality_score_obj = QualityScore(
            score=workflow_result.get("quality_score", 0.0),
            criteria_scores=workflow_result.get("metadata", {}).get("criteria_scores", {}),
            sample_size=1
        )

        # Build comprehensive report
        report = {
            "summary": {
                "quality_score": workflow_result.get("quality_score", 0.0),
                "passes_review": workflow_result.get("passes_review", False),
                "weighted_component_score": diagnostics["weighted_overall_score"],
                "severity": diagnostics["severity"]
            },
            "quality_score_detailed": quality_score_obj.to_dict(),
            "diagnostics": diagnostics,
            "metadata": {
                "revision_count": workflow_result.get("metadata", {}).get("revision_count", 0),
                "statute_confidence": workflow_result.get("metadata", {}).get("statute_confidence", "Unknown"),
                "policy_confidence": workflow_result.get("metadata", {}).get("policy_confidence", "Unknown"),
                "chunks_retrieved": {
                    "statute": workflow_result.get("metadata", {}).get("statute_chunks_retrieved", 0),
                    "policy": workflow_result.get("metadata", {}).get("policy_chunks_retrieved", 0)
                }
            },
            "recommendations": diagnostics["recommendations_summary"]
        }

        logger.info(
            f"Quality report generated: Score={report['summary']['quality_score']}, "
            f"Severity={report['summary']['severity']}, "
            f"Root Cause={diagnostics['root_cause']['component']}"
        )

        return report
