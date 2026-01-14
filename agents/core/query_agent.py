"""
Query Agent - Answers natural language questions about crisis intake data
"""
import logging
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic.v1 import BaseModel, Field

from agents.core.base_agent import BaseAgent
from agents.utils.pinot_client import PinotClient

logger = logging.getLogger(__name__)


class QueryResponse(BaseModel):
    """Structured response from Query Agent"""
    sql_query: str = Field(description="Generated Pinot SQL query")
    explanation: str = Field(description="Explanation of what the query does")
    answer: str = Field(description="Natural language answer to the user's question")


class QueryAgent(BaseAgent):
    """
    Agent specialized in answering questions about crisis intake data
    Generates Pinot SQL queries and interprets results
    """

    def __init__(self):
        super().__init__(
            name="Query Agent",
            role="Data Query Specialist",
            goal="Answer natural language questions about crisis intake data by generating and executing SQL queries"
        )
        self.pinot_client = PinotClient()
        self.output_parser = PydanticOutputParser(pydantic_object=QueryResponse)

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute query based on natural language question

        Args:
            input_data: Dict with 'question' key containing user's question

        Returns:
            Dict with SQL query, results, and natural language answer
        """
        question = input_data.get("question", "")
        logger.info(f"Processing question: {question}")

        # Step 1: Generate SQL query
        sql_query = self._generate_sql(question)

        # Step 2: Execute query
        try:
            results_df = self.pinot_client.execute_query(sql_query)
            results_summary = self._summarize_results(results_df)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {
                "success": False,
                "error": str(e),
                "sql_query": sql_query
            }

        # Step 3: Generate natural language answer
        answer = self._generate_answer(question, sql_query, results_summary)

        return {
            "success": True,
            "question": question,
            "sql_query": sql_query,
            "results": results_df.to_dict('records'),
            "results_summary": results_summary,
            "answer": answer
        }

    def _generate_sql(self, question: str) -> str:
        """Generate Pinot SQL query from natural language question"""

        schema_info = """
        Table: dhcs_crisis_intake

        Dimensions:
        - event_id (STRING): Unique event identifier
        - channel (STRING): 988_call, mobile_team, walk_in, ER_referral
        - county (STRING): Los Angeles, San Diego, Orange, Santa Clara, Alameda, Sacramento
        - presenting_problem (STRING): suicidal_thoughts, panic_attack, psychosis, overdose_risk, DV_related, withdrawal
        - risk_level (STRING): low, moderate, high, imminent
        - disposition (STRING): phone_stabilized, urgent_clinic, mobile_team_dispatched, 911_transfer, ER_referred
        - language (STRING): en, es, zh, vi, tl

        Metrics:
        - age (INT): Patient age
        - wait_time_sec (INT): Wait time in seconds
        - call_duration_sec (INT): Call duration in seconds
        - prior_contacts_90d (INT): Number of prior contacts in last 90 days
        - suicidal_ideation (INT): 0 or 1
        - homicidal_ideation (INT): 0 or 1
        - substance_use (INT): 0 or 1

        DateTime:
        - event_time_ms (LONG): Event timestamp in milliseconds (epoch)

        Common patterns:
        - Use now() for current time
        - Use event_time_ms > (now() - X) for time windows (X in milliseconds)
        - Use COUNT(*), AVG(), SUM() for aggregations
        - Use GROUP BY for breakdowns
        - Use ORDER BY ... DESC LIMIT N for top N results
        """

        system_message = f"""You are an expert SQL query generator for Apache Pinot.
Your task is to convert natural language questions into valid Pinot SQL queries.

Schema Information:
{schema_info}

Rules:
1. Always generate syntactically correct Pinot SQL
2. Use appropriate aggregations and filters
3. Include reasonable time windows (default to last 60 minutes if not specified)
4. Order results logically (DESC for counts, recent events first)
5. Add LIMIT clause to prevent huge result sets (default LIMIT 100)
6. Only use columns that exist in the schema

Return ONLY the SQL query, no explanation or markdown formatting."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{question}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"question": question})

        sql_query = response.content.strip()

        # Clean up any markdown formatting
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        logger.info(f"Generated SQL: {sql_query}")
        return sql_query

    def _summarize_results(self, results_df) -> str:
        """Create a text summary of query results"""
        if results_df.empty:
            return "No results found."

        summary_parts = [
            f"Returned {len(results_df)} rows.",
            f"Columns: {', '.join(results_df.columns)}"
        ]

        # Add sample of first few rows
        if len(results_df) <= 5:
            summary_parts.append(f"\nAll results:\n{results_df.to_string()}")
        else:
            summary_parts.append(f"\nFirst 5 rows:\n{results_df.head().to_string()}")

        return "\n".join(summary_parts)

    def _generate_answer(self, question: str, sql_query: str, results_summary: str) -> str:
        """Generate natural language answer from query results"""

        system_message = """You are a helpful analyst interpreting crisis intake data for DHCS stakeholders.
Your task is to provide clear, actionable answers to questions about behavioral health crisis data.

Guidelines:
1. Be concise and direct
2. Highlight key insights and trends
3. Use specific numbers from the data
4. Provide context when helpful
5. Suggest follow-up questions or actions when appropriate
6. Use professional, empathetic language appropriate for healthcare context"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", """Question: {question}

SQL Query Used: {sql_query}

Query Results Summary:
{results_summary}

Provide a clear, natural language answer to the question based on the results.""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "question": question,
            "sql_query": sql_query,
            "results_summary": results_summary
        })

        return response.content.strip()
