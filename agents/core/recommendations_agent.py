"""
Recommendations Agent - Provides actionable recommendations for staffing, resources, and interventions
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
from langchain.prompts import ChatPromptTemplate

from agents.core.base_agent import BaseAgent
from agents.utils.pinot_client import PinotClient

logger = logging.getLogger(__name__)


class RecommendationsAgent(BaseAgent):
    """
    Agent specialized in providing actionable recommendations
    for operational improvements, staffing, and resource allocation
    """

    def __init__(self):
        super().__init__(
            name="Recommendations Agent",
            role="Operational Strategy Advisor",
            goal="Provide data-driven recommendations for improving crisis response operations",
            temperature=0.5  # Balanced for creativity and consistency
        )
        self.pinot_client = PinotClient()

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recommendations based on current operational data

        Args:
            input_data: Dict with optional 'focus_area' and 'time_window_minutes'

        Returns:
            Dict with recommendations and supporting data
        """
        focus_area = input_data.get("focus_area", "comprehensive")
        time_window = input_data.get("time_window_minutes", 60)

        logger.info(f"Generating {focus_area} recommendations for {time_window} minute window")

        # Gather operational data
        operational_data = self._gather_operational_data(time_window)

        # Generate recommendations based on focus area
        if focus_area == "comprehensive":
            recommendations = self._generate_comprehensive_recommendations(operational_data)
        elif focus_area == "staffing":
            recommendations = self._generate_staffing_recommendations(operational_data)
        elif focus_area == "equity":
            recommendations = self._generate_equity_recommendations(operational_data)
        elif focus_area == "efficiency":
            recommendations = self._generate_efficiency_recommendations(operational_data)
        else:
            recommendations = self._generate_comprehensive_recommendations(operational_data)

        return {
            "status": "success",
            "focus_area": focus_area,
            "time_window_minutes": time_window,
            "recommendations": recommendations,
            "supporting_data": operational_data,
            "timestamp": datetime.now().isoformat()
        }

    def _gather_operational_data(self, time_window: int) -> Dict[str, Any]:
        """Gather relevant operational data for recommendations"""

        data = {}

        # County statistics
        data["county_stats"] = self.pinot_client.get_county_statistics(minutes=time_window).to_dict('records')

        # Channel distribution
        data["channel_stats"] = self.pinot_client.get_channel_distribution(minutes=time_window).to_dict('records')

        # Risk distribution
        sql_risk = f"""
        SELECT
            risk_level,
            COUNT(*) as count,
            AVG(wait_time_sec) as avg_wait_time
        FROM dhcs_crisis_intake
        WHERE event_time_ms > (now() - {time_window * 60 * 1000})
        GROUP BY risk_level
        """
        data["risk_stats"] = self.pinot_client.execute_query(sql_risk).to_dict('records')

        # Language distribution
        sql_lang = f"""
        SELECT
            language,
            COUNT(*) as count,
            AVG(wait_time_sec) as avg_wait_time
        FROM dhcs_crisis_intake
        WHERE event_time_ms > (now() - {time_window * 60 * 1000})
        GROUP BY language
        ORDER BY count DESC
        """
        data["language_stats"] = self.pinot_client.execute_query(sql_lang).to_dict('records')

        # Surge detection
        data["surge_info"] = self.pinot_client.detect_surge()

        # High-risk count
        sql_high_risk = f"""
        SELECT COUNT(*) as high_risk_count
        FROM dhcs_crisis_intake
        WHERE risk_level IN ('high', 'imminent')
        AND event_time_ms > (now() - {time_window * 60 * 1000})
        """
        data["high_risk_count"] = self.pinot_client.execute_query(sql_high_risk).iloc[0]["high_risk_count"]

        return data

    def _generate_comprehensive_recommendations(self, data: Dict[str, Any]) -> str:
        """Generate comprehensive operational recommendations"""

        system_message = """You are an expert behavioral health operations consultant.
Your task is to provide actionable, data-driven recommendations for improving crisis intake operations.

Guidelines:
1. Base recommendations on the operational data provided
2. Prioritize recommendations by impact and urgency
3. Be specific and actionable
4. Consider staffing, resources, and process improvements
5. Address equity and access issues
6. Format as clear numbered recommendations
7. Keep recommendations concise but complete"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", """Based on the following operational data, provide comprehensive recommendations:

Operational Data:
{data}

Provide 5-7 prioritized recommendations for improving crisis intake operations.""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"data": str(data)})

        return response.content.strip()

    def _generate_staffing_recommendations(self, data: Dict[str, Any]) -> str:
        """Generate staffing-focused recommendations"""

        system_message = """You are a behavioral health workforce planning expert.
Your task is to provide specific staffing recommendations based on crisis intake patterns.

Guidelines:
1. Analyze volume patterns by county and channel
2. Consider surge patterns and capacity needs
3. Address language access requirements
4. Recommend specific staffing adjustments
5. Consider both immediate and longer-term needs"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", """Based on this operational data, provide staffing recommendations:

{data}

Focus on:
- Counties with high volume or wait times
- Channels under pressure
- Language interpreter needs
- Surge response capacity

Provide specific, actionable staffing recommendations.""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"data": str(data)})

        return response.content.strip()

    def _generate_equity_recommendations(self, data: Dict[str, Any]) -> str:
        """Generate equity-focused recommendations"""

        system_message = """You are a health equity analyst for behavioral health services.
Your task is to identify and address equity gaps in crisis intake services.

Guidelines:
1. Analyze language access patterns
2. Identify disparities in wait times or service levels
3. Consider cultural competency needs
4. Address accessibility across channels
5. Focus on underserved populations"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", """Analyze this data for equity issues and provide recommendations:

{data}

Focus on:
- Language access (interpreter availability, wait times by language)
- Geographic equity (county-level disparities)
- Channel accessibility
- Service quality consistency

Provide equity-focused recommendations to improve access and reduce disparities.""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"data": str(data)})

        return response.content.strip()

    def _generate_efficiency_recommendations(self, data: Dict[str, Any]) -> str:
        """Generate efficiency-focused recommendations"""

        system_message = """You are a process improvement expert for behavioral health services.
Your task is to identify operational inefficiencies and recommend improvements.

Guidelines:
1. Analyze wait times and call durations
2. Identify bottlenecks by channel or county
3. Recommend process improvements
4. Consider technology or workflow enhancements
5. Focus on measurable efficiency gains"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", """Analyze this data for efficiency opportunities:

{data}

Focus on:
- Wait time reduction opportunities
- Channel performance optimization
- Call handling efficiency
- Resource allocation improvements

Provide specific recommendations to improve operational efficiency.""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"data": str(data)})

        return response.content.strip()
