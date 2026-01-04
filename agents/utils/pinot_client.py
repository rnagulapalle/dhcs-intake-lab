"""
Pinot database client for querying crisis intake data
"""
import logging
from typing import List, Dict, Any, Optional
from pinotdb import connect
import pandas as pd

from agents.core.config import settings

logger = logging.getLogger(__name__)


class PinotClient:
    """Client for executing queries against Apache Pinot"""

    def __init__(self, broker_url: Optional[str] = None):
        self.broker_url = broker_url or settings.pinot_broker_url
        self.table_name = settings.pinot_table_name

        # Parse broker URL for pinotdb connection
        # pinotdb.connect() requires host and port separately, not a full URL
        self.broker_host, self.broker_port = self._parse_broker_url(self.broker_url)

    def _parse_broker_url(self, url: str) -> tuple:
        """Parse broker URL into host and port"""
        # Remove http:// or https:// prefix if present
        url = url.replace('http://', '').replace('https://', '')

        # Split host and port
        if ':' in url:
            host, port = url.split(':')
            return host, int(port)
        else:
            return url, 8099  # Default Pinot broker port

    def _get_connection(self):
        """Create a Pinot database connection"""
        return connect(
            host=self.broker_host,
            port=self.broker_port,
            path='/query/sql',
            scheme='http'
        )

    def execute_query(self, sql: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as pandas DataFrame

        Args:
            sql: SQL query string

        Returns:
            pandas DataFrame with query results
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            # Fetch all rows
            rows = cursor.fetchall()

            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=columns)

            logger.info(f"Query executed successfully. Rows returned: {len(df)}")
            return df

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"SQL: {sql}")
            raise

    def get_recent_events(self, limit: int = 100, minutes: int = 60) -> pd.DataFrame:
        """
        Get recent crisis intake events

        Args:
            limit: Maximum number of events to return
            minutes: Look back this many minutes

        Returns:
            DataFrame with recent events
        """
        sql = f"""
        SELECT
            event_id,
            event_time_ms,
            county,
            channel,
            risk_level,
            presenting_problem,
            disposition,
            language,
            age,
            wait_time_sec,
            call_duration_sec,
            suicidal_ideation,
            homicidal_ideation,
            substance_use
        FROM {self.table_name}
        WHERE event_time_ms > (now() - {minutes * 60 * 1000})
        ORDER BY event_time_ms DESC
        LIMIT {limit}
        """
        return self.execute_query(sql)

    def get_high_risk_events(self, limit: int = 50, minutes: int = 60) -> pd.DataFrame:
        """
        Get high-risk and imminent-risk events

        Args:
            limit: Maximum number of events
            minutes: Look back this many minutes

        Returns:
            DataFrame with high-risk events
        """
        sql = f"""
        SELECT
            event_id,
            event_time_ms,
            county,
            channel,
            risk_level,
            presenting_problem,
            disposition,
            suicidal_ideation,
            homicidal_ideation,
            substance_use
        FROM {self.table_name}
        WHERE risk_level IN ('high', 'imminent')
        AND event_time_ms > (now() - {minutes * 60 * 1000})
        ORDER BY event_time_ms DESC
        LIMIT {limit}
        """
        return self.execute_query(sql)

    def get_county_statistics(self, minutes: int = 60) -> pd.DataFrame:
        """
        Get event statistics by county

        Args:
            minutes: Time window in minutes

        Returns:
            DataFrame with county-level statistics
        """
        sql = f"""
        SELECT
            county,
            COUNT(*) as total_events,
            SUM(CASE WHEN risk_level IN ('high', 'imminent') THEN 1 ELSE 0 END) as high_risk_count,
            AVG(wait_time_sec) as avg_wait_time,
            AVG(call_duration_sec) as avg_call_duration
        FROM {self.table_name}
        WHERE event_time_ms > (now() - {minutes * 60 * 1000})
        GROUP BY county
        ORDER BY total_events DESC
        """
        return self.execute_query(sql)

    def get_channel_distribution(self, minutes: int = 60) -> pd.DataFrame:
        """
        Get event distribution by channel

        Args:
            minutes: Time window in minutes

        Returns:
            DataFrame with channel distribution
        """
        sql = f"""
        SELECT
            channel,
            COUNT(*) as event_count,
            AVG(wait_time_sec) as avg_wait_time
        FROM {self.table_name}
        WHERE event_time_ms > (now() - {minutes * 60 * 1000})
        GROUP BY channel
        ORDER BY event_count DESC
        """
        return self.execute_query(sql)

    def detect_surge(self, threshold_multiplier: float = 2.0) -> Dict[str, Any]:
        """
        Detect if there's a surge in crisis events

        Args:
            threshold_multiplier: Alert if current rate exceeds average by this factor

        Returns:
            Dict with surge detection results
        """
        # Get last 5 minutes vs previous 30 minutes
        sql_recent = f"""
        SELECT COUNT(*) as count
        FROM {self.table_name}
        WHERE event_time_ms > (now() - 5 * 60 * 1000)
        """

        sql_baseline = f"""
        SELECT COUNT(*) as count
        FROM {self.table_name}
        WHERE event_time_ms BETWEEN (now() - 35 * 60 * 1000) AND (now() - 5 * 60 * 1000)
        """

        recent_count = self.execute_query(sql_recent)['count'].iloc[0]
        baseline_count = self.execute_query(sql_baseline)['count'].iloc[0]

        # Normalize to per-minute rates
        recent_rate = recent_count / 5
        baseline_rate = baseline_count / 30

        is_surge = recent_rate > (baseline_rate * threshold_multiplier)

        return {
            "is_surge": is_surge,
            "recent_rate_per_min": recent_rate,
            "baseline_rate_per_min": baseline_rate,
            "multiplier": recent_rate / baseline_rate if baseline_rate > 0 else 0
        }
