"""
Streamlit Dashboard for DHCS BHT Multi-Agent System
Admin interface for demonstrating AI capabilities
"""
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="DHCS BHT AI Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #555;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .agent-response {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 10px 0;
    }
    .high-risk {
        color: #d62728;
        font-weight: bold;
    }
    .success {
        color: #2ca02c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def call_api(endpoint: str, data: dict = None, method: str = "POST", timeout: int = 60) -> dict:
    """Call API endpoint with proper timeout and error handling"""
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.post(url, json=data, timeout=timeout)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error(f"API request timed out after {timeout} seconds. The AI agents may be processing a complex query.")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection Error: Unable to reach the API at {API_BASE_URL}. Please ensure the agent-api service is running.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None


# Sidebar
st.sidebar.markdown('<p class="main-header">🏥 DHCS BHT AI</p>', unsafe_allow_html=True)
st.sidebar.markdown("**Behavioral Health Treatment Crisis Intake Assistant**")
st.sidebar.markdown("---")

# Mode selection
mode = st.sidebar.radio(
    "Select Mode",
    ["💬 Chat Assistant", "📊 Analytics Dashboard", "🚨 Triage Center", "💡 Recommendations", "📚 Knowledge Base"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("""
This AI assistant helps DHCS behavioral health administrators:
- Query crisis intake data
- Analyze trends and anomalies
- Prioritize high-risk cases
- Get operational recommendations
- Access policy knowledge

**Note:** All data is synthetic for demonstration purposes.
""")

# Main content
if mode == "💬 Chat Assistant":
    st.markdown('<p class="main-header">AI Chat Assistant</p>', unsafe_allow_html=True)
    st.markdown("Ask questions about crisis intake data in natural language")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about crisis intake data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = call_api("chat", {"message": prompt})

                if result and result.get("success"):
                    response = result.get("response", "No response")
                    st.markdown(response)

                    # Show which agent was used
                    agent_used = result.get("agent_used", "unknown")
                    st.caption(f"_Agent used: {agent_used}_")

                    # Add to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    # Show raw data in expander
                    with st.expander("View detailed results"):
                        st.json(result)
                else:
                    error_msg = "Sorry, I encountered an error processing your request."
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

elif mode == "📊 Analytics Dashboard":
    st.markdown('<p class="main-header">Analytics Dashboard</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col2:
        time_window = st.selectbox("Time Window", [15, 30, 60, 120, 240], index=2)
        analysis_type = st.selectbox("Analysis Type", ["comprehensive", "trends", "surge", "anomalies"])

        if st.button("Run Analysis", type="primary"):
            st.session_state.analytics_result = call_api("analytics", {
                "analysis_type": analysis_type,
                "time_window_minutes": time_window
            })

    with col1:
        if "analytics_result" in st.session_state and st.session_state.analytics_result:
            result = st.session_state.analytics_result

            # Surge Detection
            if "surge_detection" in result:
                surge = result["surge_detection"]
                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    st.metric(
                        "Current Rate",
                        f"{surge.get('current_rate_per_minute', 0):.1f}/min",
                        delta=f"{surge.get('surge_multiplier', 0):.1f}x baseline"
                    )

                with col_b:
                    st.metric(
                        "Baseline Rate",
                        f"{surge.get('baseline_rate_per_minute', 0):.1f}/min"
                    )

                with col_c:
                    severity = surge.get('severity', 'normal')
                    color = {"normal": "🟢", "elevated": "🟡", "high": "🟠", "critical": "🔴"}
                    st.metric("Surge Status", f"{color.get(severity, '⚪')} {severity.upper()}")

                if surge.get("is_surge_detected"):
                    st.warning(f"⚠️ {surge.get('recommendation', 'Surge detected')}")

            st.markdown("---")

            # Insights
            if "insights" in result:
                st.markdown("### 💡 Key Insights")
                st.markdown(result["insights"])

            # County Trends
            if "county_trends" in result and result["county_trends"].get("top_counties"):
                st.markdown("### 🗺️ Top Counties by Volume")
                df_counties = pd.DataFrame(result["county_trends"]["top_counties"])
                fig = px.bar(df_counties, x="county", y="total_events", color="high_risk_count",
                             title="Event Volume by County")
                st.plotly_chart(fig, use_container_width=True)

            # Risk Distribution
            if "risk_trends" in result and result["risk_trends"].get("distribution"):
                st.markdown("### ⚠️ Risk Level Distribution")
                df_risk = pd.DataFrame(result["risk_trends"]["distribution"])
                fig = px.pie(df_risk, names="risk_level", values="count",
                             title="Events by Risk Level")
                st.plotly_chart(fig, use_container_width=True)

            # Detailed results
            with st.expander("View Raw Analytics Data"):
                st.json(result)
        else:
            st.info("👆 Click 'Run Analysis' to generate analytics")

elif mode == "🚨 Triage Center":
    st.markdown('<p class="main-header">Triage Center</p>', unsafe_allow_html=True)
    st.markdown("Prioritized high-risk cases requiring attention")

    col1, col2 = st.columns([3, 1])

    with col2:
        time_window = st.selectbox("Time Window (minutes)", [15, 30, 60, 120], index=1)
        limit = st.slider("Max Cases", 10, 50, 20)

        if st.button("Run Triage", type="primary"):
            st.session_state.triage_result = call_api("triage", {
                "time_window_minutes": time_window,
                "limit": limit
            })

    with col1:
        if "triage_result" in st.session_state and st.session_state.triage_result:
            result = st.session_state.triage_result

            if result.get("status") == "success":
                # Summary metrics
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("High-Risk Events", result.get("total_high_risk_events", 0))
                with col_b:
                    st.metric("Time Window", f"{time_window} min")
                with col_c:
                    st.metric("Status", "🟢 Active")

                # Triage summary
                if result.get("triage_summary"):
                    st.markdown("### 📋 Summary")
                    st.info(result["triage_summary"])

                # Recommendations
                if result.get("recommendations"):
                    st.markdown("### 💡 Recommended Actions")
                    st.markdown(result["recommendations"])

                # Prioritized cases table
                if result.get("prioritized_cases"):
                    st.markdown("### 🔴 Priority Cases")
                    df_cases = pd.DataFrame(result["prioritized_cases"])

                    # Format for display
                    display_df = df_cases[[
                        "priority_score", "risk_level", "county", "presenting_problem",
                        "suicidal_ideation", "homicidal_ideation", "minutes_ago"
                    ]].copy()

                    display_df.columns = [
                        "Priority", "Risk", "County", "Problem",
                        "SI", "HI", "Minutes Ago"
                    ]

                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True
                    )

                with st.expander("View Raw Triage Data"):
                    st.json(result)
            else:
                st.warning(result.get("message", "No high-risk events found"))
        else:
            st.info("👆 Click 'Run Triage' to identify high-risk cases")

elif mode == "💡 Recommendations":
    st.markdown('<p class="main-header">Operational Recommendations</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    with col2:
        focus_area = st.selectbox(
            "Focus Area",
            ["comprehensive", "staffing", "equity", "efficiency"]
        )
        time_window = st.selectbox("Time Window", [30, 60, 120, 240], index=1)

        if st.button("Generate Recommendations", type="primary"):
            st.session_state.rec_result = call_api("recommendations", {
                "focus_area": focus_area,
                "time_window_minutes": time_window
            })

    with col1:
        if "rec_result" in st.session_state and st.session_state.rec_result:
            result = st.session_state.rec_result

            st.markdown(f"### 📌 {focus_area.title()} Recommendations")
            st.markdown(result.get("recommendations", "No recommendations available"))

            # Supporting data
            if result.get("supporting_data"):
                with st.expander("View Supporting Data"):
                    data = result["supporting_data"]

                    if data.get("county_stats"):
                        st.markdown("**County Statistics**")
                        st.dataframe(pd.DataFrame(data["county_stats"]))

                    if data.get("channel_stats"):
                        st.markdown("**Channel Statistics**")
                        st.dataframe(pd.DataFrame(data["channel_stats"]))

                    if data.get("language_stats"):
                        st.markdown("**Language Statistics**")
                        st.dataframe(pd.DataFrame(data["language_stats"]))
        else:
            st.info("👆 Select a focus area and generate recommendations")

elif mode == "📚 Knowledge Base":
    st.markdown('<p class="main-header">DHCS Policy Knowledge Base</p>', unsafe_allow_html=True)

    # Knowledge base stats
    stats = call_api("knowledge/stats", method="GET")
    if stats:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.metric("Documents in Knowledge Base", stats.get("document_count", 0))
        with col2:
            if st.button("Refresh Stats"):
                st.rerun()

    st.markdown("---")

    # Search interface
    st.markdown("### 🔍 Search Policies & Procedures")
    query = st.text_input("Enter your search query", placeholder="e.g., mobile crisis team response time")
    n_results = st.slider("Number of results", 1, 10, 5)

    if st.button("Search", type="primary") or query:
        if query:
            result = call_api("knowledge/search", {"query": query, "n_results": n_results})

            if result and result.get("results"):
                st.success(f"Found {result.get('count', 0)} relevant documents")

                for i, doc in enumerate(result["results"], 1):
                    with st.expander(f"Result {i} - {doc.get('metadata', {}).get('source', 'Unknown Source')}"):
                        st.markdown(f"**Section:** {doc.get('metadata', {}).get('section', 'N/A')}")
                        st.markdown(f"**Category:** {doc.get('metadata', {}).get('category', 'N/A')}")
                        st.markdown("---")
                        st.markdown(doc.get("content", ""))
                        if doc.get("distance") is not None:
                            st.caption(f"Relevance score: {1 - doc['distance']:.2f}")
            else:
                st.warning("No results found")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>DHCS Behavioral Health Treatment AI Assistant | Demo System with Synthetic Data</p>
    <p>Powered by OpenAI GPT-4, LangGraph, Apache Pinot & ChromaDB</p>
</div>
""", unsafe_allow_html=True)
