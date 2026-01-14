"""
Analytics Agent - Detects trends, patterns, and anomalies in crisis data
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate

from agents.core.base_agent import BaseAgent
from agents.utils.pinot_client import PinotClient

logger = logging.getLogger(__name__)


class AnalyticsAgent(BaseAgent):
    """
    Agent specialized in analyzing trends, detecting anomalies,
    and identifying patterns in crisis intake data
    """

    def __init__(self):
        super().__init__(
            name="Analytics Agent",
            role="Data Analytics Specialist",
            goal="Analyze crisis intake data to detect trends, anomalies, and patterns for operational insights",
            temperature=0.3  # Lower temperature for more consistent analysis
        )
        self.pinot_client = PinotClient()

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform analytics on crisis intake data

        Args:
            input_data: Dict with optional 'analysis_type' and 'time_window_minutes'

        Returns:
            Dict with analytics results and insights
        """
        analysis_type = input_data.get("analysis_type", "comprehensive")
        time_window = input_data.get("time_window_minutes", 60)

        logger.info(f"Performing {analysis_type} analysis over {time_window} minutes")

        results = {}

        if analysis_type in ["comprehensive", "surge"]:
            results["surge_detection"] = self._detect_surge()

        if analysis_type in ["comprehensive", "trends"]:
            results["county_trends"] = self._analyze_county_trends(time_window)
            results["risk_trends"] = self._analyze_risk_trends(time_window)
            results["channel_performance"] = self._analyze_channel_performance(time_window)

        if analysis_type in ["comprehensive", "anomalies"]:
            results["anomalies"] = self._detect_anomalies(time_window)

        # Generate insights summary
        results["insights"] = self._generate_insights(results)
        results["analysis_timestamp"] = datetime.now().isoformat()

        return results

    def _detect_surge(self) -> Dict[str, Any]:
        """Detect if there's a surge in crisis events"""
        surge_data = self.pinot_client.detect_surge(threshold_multiplier=2.0)

        return {
            "is_surge_detected": surge_data["is_surge"],
            "current_rate_per_minute": round(surge_data["recent_rate_per_min"], 2),
            "baseline_rate_per_minute": round(surge_data["baseline_rate_per_min"], 2),
            "surge_multiplier": round(surge_data["multiplier"], 2),
            "severity": self._classify_surge_severity(surge_data["multiplier"]),
            "recommendation": self._get_surge_recommendation(surge_data["multiplier"])
        }

    def _classify_surge_severity(self, multiplier: float) -> str:
        """Classify surge severity based on multiplier"""
        if multiplier < 1.5:
            return "normal"
        elif multiplier < 2.0:
            return "elevated"
        elif multiplier < 3.0:
            return "high"
        else:
            return "critical"

    def _get_surge_recommendation(self, multiplier: float) -> str:
        """Get recommendation based on surge severity"""
        if multiplier < 1.5:
            return "No action needed. Volume within normal range."
        elif multiplier < 2.0:
            return "Monitor closely. Consider alerting supervisors."
        elif multiplier < 3.0:
            return "Consider activating additional staff. Alert management."
        else:
            return "Activate surge protocols. Immediate management notification required."

    def _analyze_county_trends(self, time_window: int) -> Dict[str, Any]:
        """Analyze trends by county"""
        df = self.pinot_client.get_county_statistics(minutes=time_window)

        if df.empty:
            return {"status": "no_data"}

        # Sort by total events
        df = df.sort_values("total_events", ascending=False)

        return {
            "top_counties": df.head(3)[["county", "total_events", "high_risk_count"]].to_dict('records'),
            "highest_wait_time_county": df.nlargest(1, "avg_wait_time")[["county", "avg_wait_time"]].to_dict('records')[0] if not df.empty else None,
            "total_events_all_counties": int(df["total_events"].sum()),
            "total_high_risk_events": int(df["high_risk_count"].sum())
        }

    def _analyze_risk_trends(self, time_window: int) -> Dict[str, Any]:
        """Analyze risk level distribution and trends"""
        sql = f"""
        SELECT
            risk_level,
            COUNT(*) as count,
            AVG(wait_time_sec) as avg_wait_time,
            AVG(call_duration_sec) as avg_call_duration
        FROM dhcs_crisis_intake
        WHERE event_time_ms > (now() - {time_window * 60 * 1000})
        GROUP BY risk_level
        ORDER BY
            CASE risk_level
                WHEN 'imminent' THEN 1
                WHEN 'high' THEN 2
                WHEN 'moderate' THEN 3
                WHEN 'low' THEN 4
            END
        """

        df = self.pinot_client.execute_query(sql)

        if df.empty:
            return {"status": "no_data"}

        total_events = df["count"].sum()
        high_risk_count = df[df["risk_level"].isin(["high", "imminent"])]["count"].sum()

        return {
            "distribution": df.to_dict('records'),
            "high_risk_percentage": round((high_risk_count / total_events * 100), 2) if total_events > 0 else 0,
            "total_events": int(total_events)
        }

    def _analyze_channel_performance(self, time_window: int) -> Dict[str, Any]:
        """Analyze performance by intake channel"""
        df = self.pinot_client.get_channel_distribution(minutes=time_window)

        if df.empty:
            return {"status": "no_data"}

        return {
            "channel_breakdown": df.to_dict('records'),
            "most_used_channel": df.iloc[0]["channel"] if not df.empty else None,
            "longest_wait_channel": df.nlargest(1, "avg_wait_time")[["channel", "avg_wait_time"]].to_dict('records')[0] if not df.empty else None
        }

    def _detect_anomalies(self, time_window: int) -> List[Dict[str, Any]]:
        """Detect anomalies in the data"""
        anomalies = []

        # Check for unusual language patterns
        sql_lang = f"""
        SELECT
            language,
            COUNT(*) as count
        FROM dhcs_crisis_intake
        WHERE event_time_ms > (now() - {time_window * 60 * 1000})
        GROUP BY language
        ORDER BY count DESC
        """
        lang_df = self.pinot_client.execute_query(sql_lang)

        if not lang_df.empty and len(lang_df) > 0:
            total = lang_df["count"].sum()
            for _, row in lang_df.iterrows():
                pct = (row["count"] / total * 100)
                # Flag if non-English language is > 40% of volume
                if row["language"] != "en" and pct > 40:
                    anomalies.append({
                        "type": "language_spike",
                        "description": f"Unusually high {row['language']} language requests ({pct:.1f}%)",
                        "severity": "medium"
                    })

        # Check for specific problem types surging
        sql_problem = f"""
        SELECT
            presenting_problem,
            COUNT(*) as count
        FROM dhcs_crisis_intake
        WHERE event_time_ms > (now() - {time_window * 60 * 1000})
        GROUP BY presenting_problem
        ORDER BY count DESC
        LIMIT 1
        """
        problem_df = self.pinot_client.execute_query(sql_problem)

        if not problem_df.empty:
            top_problem = problem_df.iloc[0]
            # If one problem type is > 50% of volume, flag it
            total_events_sql = f"SELECT COUNT(*) as total FROM dhcs_crisis_intake WHERE event_time_ms > (now() - {time_window * 60 * 1000})"
            total_events = self.pinot_client.execute_query(total_events_sql).iloc[0]["total"]

            if total_events > 0:
                pct = (top_problem["count"] / total_events * 100)
                if pct > 50:
                    anomalies.append({
                        "type": "problem_concentration",
                        "description": f"High concentration of {top_problem['presenting_problem']} cases ({pct:.1f}%)",
                        "severity": "high"
                    })

        return anomalies

    def _generate_insights(self, results: Dict[str, Any]) -> str:
        """Generate natural language insights from analytics results"""

        system_message = """You are an expert behavioral health data analyst.
Your task is to provide clear, actionable insights from crisis intake analytics.

Guidelines:
1. Focus on the most important findings
2. Highlight operational implications
3. Suggest specific actions when appropriate
4. Use professional, empathetic language
5. Keep insights concise (3-5 bullet points)"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", """Based on the following crisis intake analytics, provide key insights:

Analytics Results:
{results}

Provide 3-5 concise, actionable insights.""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"results": str(results)})

        return response.content.strip()
