"""
Triage Agent - Prioritizes high-risk cases and suggests immediate actions
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
from langchain.prompts import ChatPromptTemplate

from agents.core.base_agent import BaseAgent
from agents.utils.pinot_client import PinotClient

logger = logging.getLogger(__name__)


class TriageAgent(BaseAgent):
    """
    Agent specialized in triaging crisis intake events,
    identifying high-risk cases, and prioritizing interventions
    """

    def __init__(self):
        super().__init__(
            name="Triage Agent",
            role="Crisis Triage Specialist",
            goal="Identify and prioritize high-risk cases requiring immediate attention",
            temperature=0.2  # Very low temperature for consistent risk assessment
        )
        self.pinot_client = PinotClient()

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Triage crisis intake events and prioritize high-risk cases

        Args:
            input_data: Dict with optional 'time_window_minutes' and 'limit'

        Returns:
            Dict with prioritized cases and triage recommendations
        """
        time_window = input_data.get("time_window_minutes", 30)
        limit = input_data.get("limit", 20)

        logger.info(f"Triaging events from last {time_window} minutes")

        # Get high-risk events
        high_risk_df = self.pinot_client.get_high_risk_events(
            limit=limit,
            minutes=time_window
        )

        if high_risk_df.empty:
            return {
                "status": "no_high_risk_events",
                "message": "No high-risk events in the specified time window",
                "triage_timestamp": datetime.now().isoformat()
            }

        # Score and prioritize cases
        prioritized_cases = self._prioritize_cases(high_risk_df)

        # Generate triage summary
        triage_summary = self._generate_triage_summary(prioritized_cases)

        # Get specific recommendations
        recommendations = self._generate_recommendations(prioritized_cases)

        return {
            "status": "success",
            "total_high_risk_events": len(prioritized_cases),
            "prioritized_cases": prioritized_cases[:10],  # Top 10 most critical
            "triage_summary": triage_summary,
            "recommendations": recommendations,
            "triage_timestamp": datetime.now().isoformat()
        }

    def _prioritize_cases(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Score and prioritize cases based on risk factors

        Scoring system:
        - Risk level: imminent (100), high (50)
        - Suicidal ideation: +30
        - Homicidal ideation: +40
        - Substance use: +10
        - Prior contacts (more = higher familiarity = slight priority boost)
        """
        cases = []

        for _, row in df.iterrows():
            score = 0

            # Base score from risk level
            if row["risk_level"] == "imminent":
                score += 100
            elif row["risk_level"] == "high":
                score += 50

            # Additional risk factors
            if row.get("suicidal_ideation", 0) == 1:
                score += 30

            if row.get("homicidal_ideation", 0) == 1:
                score += 40

            if row.get("substance_use", 0) == 1:
                score += 10

            # Recency factor (more recent = higher priority)
            # This is already handled by sorting, but we note it

            case = {
                "event_id": row["event_id"],
                "priority_score": score,
                "risk_level": row["risk_level"],
                "county": row["county"],
                "channel": row["channel"],
                "presenting_problem": row["presenting_problem"],
                "disposition": row["disposition"],
                "suicidal_ideation": bool(row.get("suicidal_ideation", 0)),
                "homicidal_ideation": bool(row.get("homicidal_ideation", 0)),
                "substance_use": bool(row.get("substance_use", 0)),
                "event_time_ms": row["event_time_ms"],
                "minutes_ago": self._calculate_minutes_ago(row["event_time_ms"])
            }

            cases.append(case)

        # Sort by priority score (descending)
        cases.sort(key=lambda x: x["priority_score"], reverse=True)

        return cases

    def _calculate_minutes_ago(self, event_time_ms: int) -> int:
        """Calculate how many minutes ago an event occurred"""
        now_ms = datetime.now().timestamp() * 1000
        diff_ms = now_ms - event_time_ms
        return int(diff_ms / 60000)

    def _generate_triage_summary(self, cases: List[Dict[str, Any]]) -> str:
        """Generate a summary of triage results"""

        if not cases:
            return "No high-risk cases to triage."

        # Count critical indicators
        imminent_count = sum(1 for c in cases if c["risk_level"] == "imminent")
        suicidal_count = sum(1 for c in cases if c["suicidal_ideation"])
        homicidal_count = sum(1 for c in cases if c["homicidal_ideation"])

        summary_parts = [
            f"Triaged {len(cases)} high-risk events.",
            f"- {imminent_count} imminent risk cases",
            f"- {suicidal_count} cases with suicidal ideation",
            f"- {homicidal_count} cases with homicidal ideation"
        ]

        # Top priority case
        top_case = cases[0]
        summary_parts.append(
            f"\nHighest priority: {top_case['event_id']} "
            f"(score: {top_case['priority_score']}, {top_case['presenting_problem']})"
        )

        return "\n".join(summary_parts)

    def _generate_recommendations(self, cases: List[Dict[str, Any]]) -> str:
        """Generate AI-powered recommendations for triage actions"""

        if not cases:
            return "No recommendations needed."

        # Prepare case summary for LLM
        top_cases = cases[:5]  # Focus on top 5 most critical

        case_summary = "\n\n".join([
            f"Case {i+1} (Priority Score: {case['priority_score']}):\n"
            f"- Risk Level: {case['risk_level']}\n"
            f"- County: {case['county']}\n"
            f"- Channel: {case['channel']}\n"
            f"- Problem: {case['presenting_problem']}\n"
            f"- Disposition: {case['disposition']}\n"
            f"- Suicidal Ideation: {case['suicidal_ideation']}\n"
            f"- Homicidal Ideation: {case['homicidal_ideation']}\n"
            f"- Substance Use: {case['substance_use']}\n"
            f"- Time: {case['minutes_ago']} minutes ago"
            for i, case in enumerate(top_cases)
        ])

        system_message = """You are an expert behavioral health crisis coordinator.
Your task is to provide clear, actionable triage recommendations for crisis cases.

Guidelines:
1. Prioritize immediate safety and risk mitigation
2. Suggest specific actions (e.g., "dispatch mobile team", "contact ER")
3. Consider resource allocation across counties
4. Be concise and directive
5. Use professional clinical language
6. Focus on the most critical cases first"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", """Review these high-priority crisis cases and provide triage recommendations:

{case_summary}

Provide specific, prioritized recommendations for handling these cases.""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"case_summary": case_summary})

        return response.content.strip()
