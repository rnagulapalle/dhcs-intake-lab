"""
DHCS BHT Multi-Agent Dashboard - Wireframe Implementation
Handles multiple use cases with context-aware UI
"""
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import os

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="DHCS BHT AI Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Light, clean design inspired by ChatGPT/Grok
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Global styles */
    * {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Main container - pure white background */
    .main {
        padding: 0 !important;
        background-color: #FFFFFF;
    }

    /* Streamlit columns */
    [data-testid="column"] {
        background-color: #FFFFFF;
        padding: 20px 16px;
    }

    /* Left Navigation Panel - very light gray */
    [data-testid="column"]:first-child {
        background-color: #FAFAFA;
        border-right: 1px solid #E5E5E5;
    }

    /* Right Panel - very light gray */
    [data-testid="column"]:last-child {
        background-color: #FAFAFA;
        border-left: 1px solid #E5E5E5;
    }

    /* Use case navigation buttons - minimal style */
    div[data-testid="stButton"] > button {
        width: 100%;
        text-align: left;
        padding: 10px 14px;
        margin: 3px 0;
        background: #FFFFFF;
        border: 1px solid #E5E5E5;
        border-radius: 8px;
        color: #1F1F1F;
        font-size: 14px;
        font-weight: 400;
        cursor: pointer;
        transition: all 0.15s ease;
        box-shadow: none;
    }

    div[data-testid="stButton"] > button:hover {
        background: #F5F5F5;
        border-color: #D1D1D1;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    div[data-testid="stButton"] > button:active {
        background: #EBEBEB;
        border-color: #1F1F1F;
    }

    /* Primary button (Send) */
    button[kind="primary"] {
        background: #1F1F1F !important;
        color: #FFFFFF !important;
        border: 1px solid #1F1F1F !important;
    }

    button[kind="primary"]:hover {
        background: #3A3A3A !important;
        border-color: #3A3A3A !important;
    }

    /* Chat messages - ultra clean */
    .user-message {
        background: #F7F7F7;
        padding: 12px 16px;
        border-radius: 16px;
        margin: 10px 0;
        max-width: 75%;
        margin-left: auto;
        color: #1F1F1F;
        font-size: 15px;
        line-height: 1.5;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }

    .assistant-message {
        background: #FFFFFF;
        padding: 12px 16px;
        border-radius: 16px;
        margin: 10px 0;
        max-width: 75%;
        color: #1F1F1F;
        font-size: 15px;
        line-height: 1.5;
        border: 1px solid #E5E5E5;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }

    .user-message strong,
    .assistant-message strong {
        color: #666;
        font-weight: 500;
        font-size: 13px;
    }

    /* Input area - minimal clean style */
    .stTextInput > div > div > input {
        border-radius: 24px;
        padding: 12px 20px;
        border: 1px solid #E5E5E5;
        background: #FFFFFF;
        font-size: 15px;
        color: #1F1F1F;
        transition: all 0.2s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: #B0B0B0;
        box-shadow: 0 0 0 3px rgba(0,0,0,0.05);
    }

    /* Chat input form - Grok style */
    [data-testid="stForm"] {
        border: 1px solid #D1D1D1;
        border-radius: 28px;
        padding: 4px;
        background: #FFFFFF;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    /* Hide form border styling */
    [data-testid="stForm"] > div:first-child {
        border: none !important;
    }

    /* Form columns layout - ensure proper alignment */
    [data-testid="stForm"] [data-testid="column"] {
        padding: 0 !important;
        background: transparent !important;
    }

    /* Style input inside form */
    [data-testid="stForm"] .stTextInput {
        margin-bottom: 0 !important;
    }

    [data-testid="stForm"] .stTextInput > div > div > input {
        border: none !important;
        padding: 10px 16px !important;
        font-size: 15px !important;
        background: transparent !important;
    }

    [data-testid="stForm"] .stTextInput > div > div > input:focus {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* Button container alignment */
    [data-testid="stForm"] [data-testid="column"]:last-child {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-end !important;
        padding-right: 4px !important;
    }

    /* Send button - Black circular up arrow (Grok style) */
    [data-testid="stForm"] button {
        background: #000000 !important;
        color: #FFFFFF !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        padding: 0 !important;
        font-size: 20px !important;
        font-weight: bold !important;
        border: none !important;
        min-width: 40px !important;
        min-height: 40px !important;
        max-width: 40px !important;
        max-height: 40px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
        flex-shrink: 0 !important;
    }

    [data-testid="stForm"] button:hover {
        background: #2A2A2A !important;
        transform: scale(1.05);
    }

    [data-testid="stForm"] button:active {
        background: #000000 !important;
        transform: scale(0.95);
    }

    /* Clear chat button - minimal style */
    button[key="clear_btn"] {
        background: transparent !important;
        border: 1px solid #E5E5E5 !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        font-size: 13px !important;
        color: #666 !important;
        transition: all 0.2s ease !important;
        margin-top: 8px !important;
    }

    button[key="clear_btn"]:hover {
        background: #F5F5F5 !important;
        border-color: #D1D1D1 !important;
        color: #1F1F1F !important;
    }

    /* Headers - clean typography */
    h1, h2, h3, h4 {
        color: #1F1F1F;
        font-weight: 600;
        letter-spacing: -0.02em;
    }

    h2 {
        font-size: 24px;
        margin-bottom: 8px;
    }

    h3 {
        font-size: 18px;
        font-weight: 600;
    }

    /* Caption text */
    .stCaption, [data-testid="stCaption"] {
        color: #666;
        font-size: 13px;
    }

    /* Expander */
    [data-testid="stExpander"] {
        background: #FFFFFF;
        border: 1px solid #E5E5E5;
        border-radius: 8px;
    }

    /* Select boxes and inputs - minimal */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid #E5E5E5;
        background: #FFFFFF;
    }

    .stMultiSelect > div > div {
        border-radius: 8px;
        border: 1px solid #E5E5E5;
        background: #FFFFFF;
    }

    /* Metrics - clean cards */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #E5E5E5;
    }

    [data-testid="stMetricLabel"] {
        color: #666;
        font-size: 13px;
        font-weight: 500;
    }

    [data-testid="stMetricValue"] {
        color: #1F1F1F;
        font-size: 24px;
        font-weight: 600;
    }

    /* Status badges - minimal */
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
    }

    .status-active {
        background: #F0F0F0;
        color: #1F1F1F;
    }

    .status-pending {
        background: #F5F5F5;
        color: #666;
    }

    .status-critical {
        background: #F0F0F0;
        color: #1F1F1F;
    }

    /* Dividers */
    hr {
        border: none;
        border-top: 1px solid #E5E5E5;
        margin: 16px 0;
    }

    /* Info/warning boxes - minimal */
    .stInfo {
        background: #F9F9F9;
        border-left: 3px solid #D1D1D1;
        color: #1F1F1F;
    }

    /* Markdown in center panel */
    [data-testid="column"]:nth-child(2) {
        padding: 24px 32px;
    }

    /* Welcome message styling */
    [data-testid="column"]:nth-child(2) h3 {
        color: #1F1F1F;
        font-weight: 600;
        font-size: 22px;
    }

    [data-testid="column"]:nth-child(2) p {
        color: #666;
        font-size: 15px;
        line-height: 1.6;
    }

    /* Remove button emoji if needed */
    div[data-testid="stButton"] > button::before {
        content: none;
    }
</style>
""", unsafe_allow_html=True)

# Define use cases
USE_CASES = {
    "Crisis Triage": {
        "icon": "🚨",
        "description": "Real-time crisis monitoring and high-risk case triage",
        "contexts": ["Time Window", "Risk Level", "County", "Channel"],
        "sample_queries": [
            "Show me high-risk cases from the last hour",
            "Are we experiencing a crisis surge?",
            "What counties have the most imminent risk cases?",
            "Average wait time for crisis calls"
        ]
    },
    "Policy Q&A": {
        "icon": "📋",
        "description": "Search DHCS policies, AB 531, SB 326, Prop 1 guidelines",
        "contexts": ["Policy Type", "Section", "County Requirements"],
        "sample_queries": [
            "What are crisis stabilization unit requirements under Prop 1?",
            "AB 531 mobile crisis team standards",
            "Staffing requirements for crisis centers",
            "County compliance checklist for BHT"
        ]
    },
    "BHOATR Reporting": {
        "icon": "📊",
        "description": "Generate behavioral health outcomes and accountability reports",
        "contexts": ["Report Period", "County", "Metrics"],
        "sample_queries": [
            "Generate Q4 2024 report for Los Angeles County",
            "Show year-over-year crisis call trends",
            "Success rates by county",
            "30-day readmission rates"
        ]
    },
    "Licensing Assistant": {
        "icon": "🏢",
        "description": "Guide facilities through licensing and certification process",
        "contexts": ["Facility Type", "County", "Status"],
        "sample_queries": [
            "Requirements to open residential treatment facility in Fresno",
            "Crisis stabilization unit licensing checklist",
            "Application timeline and steps",
            "Required certifications for mobile crisis teams"
        ]
    },
    "IP Compliance": {
        "icon": "✅",
        "description": "Review Integrated Plans for BHT compliance",
        "contexts": ["County", "Section", "Compliance Status"],
        "sample_queries": [
            "Review Alameda County Integrated Plan",
            "Check housing services compliance",
            "Infrastructure timeline requirements",
            "Budget justification checklist"
        ]
    },
    "Infrastructure Tracking": {
        "icon": "🏗️",
        "description": "Monitor Prop 1 infrastructure projects and budgets",
        "contexts": ["Project Type", "County", "Status", "Timeline"],
        "sample_queries": [
            "Show all crisis center construction projects",
            "Projects behind schedule",
            "Budget utilization by county",
            "Completion timeline for new facilities"
        ]
    },
    "Population Analytics": {
        "icon": "👥",
        "description": "Analyze target populations and service gaps",
        "contexts": ["Population", "County", "Time Period"],
        "sample_queries": [
            "Justice-involved individuals crisis patterns",
            "Homeless population service gaps",
            "Youth transition-age crisis trends",
            "Co-occurring disorder demographics"
        ]
    },
    "Resource Allocation": {
        "icon": "💰",
        "description": "Optimize funding allocation and resource planning",
        "contexts": ["Budget", "Priority", "Impact"],
        "sample_queries": [
            "Optimal allocation for $10M Prop 1 funds",
            "ROI analysis for mobile crisis teams",
            "Cost per successful intervention by county",
            "High-impact investment opportunities"
        ]
    }
}

# Initialize session state
if "current_use_case" not in st.session_state:
    st.session_state.current_use_case = "Crisis Triage"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "context_filters" not in st.session_state:
    st.session_state.context_filters = {}
if "sample_query" not in st.session_state:
    st.session_state.sample_query = None

def call_api(endpoint: str, data: dict = None, method: str = "POST", timeout: int = 60) -> dict:
    """Call API endpoint"""
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        if method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        else:
            response = requests.get(url, params=data, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {"success": False, "error": str(e)}

# Create 3-column layout matching wireframe
col1, col2, col3 = st.columns([1, 2, 1])

# ============================================================================
# LEFT PANEL: Use Case Navigation
# ============================================================================
with col1:
    st.markdown("### 🏥 DHCS BHT Platform")
    st.markdown("---")

    st.markdown("**Use Cases**")

    for use_case, details in USE_CASES.items():
        # Create button for each use case
        button_class = "active" if use_case == st.session_state.current_use_case else ""

        if st.button(
            f"{details['icon']} {use_case}",
            key=f"nav_{use_case}",
            use_container_width=True
        ):
            st.session_state.current_use_case = use_case
            st.session_state.messages = []  # Clear chat history on use case change
            st.session_state.context_filters = {}
            st.rerun()

    st.markdown("---")

    # System status
    st.markdown("**System Status**")
    st.markdown('<span class="status-badge status-active">● All Systems Operational</span>', unsafe_allow_html=True)
    st.caption("Last updated: " + datetime.now().strftime("%I:%M %p"))

# ============================================================================
# CENTER PANEL: Chat Interface
# ============================================================================
with col2:
    current_use_case = st.session_state.current_use_case
    use_case_details = USE_CASES[current_use_case]

    # Header
    st.markdown(f"## {use_case_details['icon']} {current_use_case}")
    st.caption(use_case_details['description'])
    st.markdown("---")

    # Chat history display
    chat_container = st.container()
    with chat_container:
        if len(st.session_state.messages) == 0:
            # Welcome message for current use case
            st.markdown(f"""
            <div style='text-align: center; padding: 40px 20px;'>
                <h3>Welcome to {current_use_case}</h3>
                <p style='color: #666;'>{use_case_details['description']}</p>
                <p style='margin-top: 20px; font-size: 14px;'>
                    👉 Try one of the sample queries from the right panel, or type your own question below.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display chat history
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class='user-message'>
                        <strong>You:</strong><br/>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='assistant-message'>
                        <strong>AI Assistant:</strong><br/>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)

    # Processing indicator
    if st.session_state.is_processing:
        st.info("⏳ Processing your query... Please wait.")

    # Chat input - Grok style with up arrow
    st.markdown("---")

    # Create form for chat input
    with st.form(key="chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([30, 1])

        with col_input:
            user_input = st.text_input(
                "Message",
                placeholder=f"Ask about {current_use_case.lower()}...",
                label_visibility="collapsed",
                key="chat_input_field"
            )

        with col_btn:
            submitted = st.form_submit_button("↑", use_container_width=True)

    # Clear button below input (small, minimal)
    if st.button("🗑️ Clear Chat", help="Clear chat history", key="clear_btn"):
        st.session_state.messages = []
        st.rerun()

    # Handle sample query from right panel
    if 'sample_query' in st.session_state and st.session_state.sample_query and not st.session_state.is_processing:
        user_input = st.session_state.sample_query
        st.session_state.sample_query = None  # Clear it
        st.session_state.is_processing = True

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        # Call API based on use case
        with st.spinner("Processing..."):
            try:
                # Map use case to API endpoint
                if current_use_case == "Crisis Triage":
                    result = call_api("chat", {"message": user_input})
                    response = result.get("response", "No response available")

                elif current_use_case == "Policy Q&A":
                    result = call_api("knowledge/search", {"query": user_input, "n_results": 3})
                    # Format knowledge base results
                    if result.get("results"):
                        response_parts = []
                        for i, item in enumerate(result["results"][:3], 1):
                            content = item.get("content", "")
                            source = item.get("metadata", {}).get("source", "Unknown")
                            section = item.get("metadata", {}).get("section", "")
                            response_parts.append(f"**Source {i}: {source}**\n{f'Section: {section}' if section else ''}\n\n{content}")
                        response = "\n\n---\n\n".join(response_parts)
                    else:
                        response = "No relevant policy information found."

                elif current_use_case == "BHOATR Reporting":
                    result = call_api("analytics", {"analysis_type": "comprehensive", "time_window_minutes": 60})
                    response = result.get("analysis", result.get("response", "Analysis not available"))

                elif current_use_case == "IP Compliance":
                    # For IP Compliance, use knowledge base to get requirements
                    result = call_api("knowledge/search", {"query": f"Integrated Plan requirements {user_input}", "n_results": 3})
                    if result.get("results"):
                        response = "**Integrated Plan Compliance Requirements:**\n\n"
                        for item in result["results"][:2]:
                            content = item.get("content", "")
                            response += f"{content}\n\n"
                        response += f"\n\n**Your Query:** {user_input}\n\nTo perform a full compliance review, please provide your Integrated Plan document for detailed analysis."
                    else:
                        response = "Integrated Plan requirements not found. Please ensure the knowledge base is populated."

                else:
                    # Default for other use cases - use chat endpoint
                    result = call_api("chat", {"message": f"[{current_use_case}] {user_input}"})
                    response = result.get("response", "No response available")

                # Add response to chat
                if response:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": str(response)
                    })
                else:
                    raise Exception("Empty response from API")

            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error processing your request: {str(e)}\n\nPlease ensure:\n- The API service is running\n- The knowledge base is populated\n- The query is valid for this use case"
                })

            st.session_state.is_processing = False
            st.rerun()

    # Handle form submission
    if submitted and user_input and not st.session_state.is_processing:
        st.session_state.is_processing = True

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        # Call API based on use case
        with st.spinner("Processing..."):
            try:
                # Map use case to API endpoint
                if current_use_case == "Crisis Triage":
                    result = call_api("chat", {"message": user_input})
                    response = result.get("response", "No response available")

                elif current_use_case == "Policy Q&A":
                    result = call_api("knowledge/search", {"query": user_input, "n_results": 3})
                    # Format knowledge base results
                    if result.get("results"):
                        response_parts = []
                        for i, item in enumerate(result["results"][:3], 1):
                            content = item.get("content", "")
                            source = item.get("metadata", {}).get("source", "Unknown")
                            section = item.get("metadata", {}).get("section", "")
                            response_parts.append(f"**Source {i}: {source}**\n{f'Section: {section}' if section else ''}\n\n{content}")
                        response = "\n\n---\n\n".join(response_parts)
                    else:
                        response = "No relevant policy information found."

                elif current_use_case == "BHOATR Reporting":
                    result = call_api("analytics", {"analysis_type": "comprehensive", "time_window_minutes": 60})
                    response = result.get("analysis", result.get("response", "Analysis not available"))

                elif current_use_case == "IP Compliance":
                    # For IP Compliance, use knowledge base to get requirements
                    result = call_api("knowledge/search", {"query": f"Integrated Plan requirements {user_input}", "n_results": 3})
                    if result.get("results"):
                        response = "**Integrated Plan Compliance Requirements:**\n\n"
                        for item in result["results"][:2]:
                            content = item.get("content", "")
                            response += f"{content}\n\n"
                        response += f"\n\n**Your Query:** {user_input}\n\nTo perform a full compliance review, please provide your Integrated Plan document for detailed analysis."
                    else:
                        response = "Integrated Plan requirements not found. Please ensure the knowledge base is populated."

                else:
                    # Default for other use cases - use chat endpoint
                    result = call_api("chat", {"message": f"[{current_use_case}] {user_input}"})
                    response = result.get("response", "No response available")

                # Add response to chat
                if response:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": str(response)
                    })
                else:
                    raise Exception("Empty response from API")

            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error processing your request: {str(e)}\n\nPlease ensure:\n- The API service is running\n- The knowledge base is populated\n- The query is valid for this use case"
                })

            st.session_state.is_processing = False
            st.rerun()

# ============================================================================
# RIGHT PANEL: Context & Suggestions
# ============================================================================
with col3:
    st.markdown("### Context")

    # Context filters based on use case
    with st.expander("🎯 Filters", expanded=True):
        contexts = use_case_details['contexts']

        for context in contexts:
            if context == "Time Window":
                st.selectbox("Time Window", ["Last Hour", "Last 24 Hours", "Last Week", "Last Month"], key="filter_time")
            elif context == "Risk Level":
                st.multiselect("Risk Level", ["Low", "Moderate", "High", "Imminent"], key="filter_risk")
            elif context == "County":
                st.selectbox("County", ["All Counties", "Los Angeles", "San Diego", "Orange", "Fresno", "Sacramento"], key="filter_county")
            elif context == "Channel":
                st.multiselect("Channel", ["988 Call", "Mobile Team", "Walk-in", "ER Referral"], key="filter_channel")
            elif context == "Policy Type":
                st.selectbox("Policy Type", ["All Policies", "AB 531", "SB 326", "Prop 1", "DHCS Guidelines"], key="filter_policy")
            elif context == "Report Period":
                st.selectbox("Report Period", ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "YTD 2024"], key="filter_period")
            elif context == "Facility Type":
                st.selectbox("Facility Type", ["All Types", "Crisis Stabilization", "Residential Treatment", "Mobile Crisis"], key="filter_facility")
            elif context == "Status":
                st.selectbox("Status", ["All", "Active", "Pending", "Completed"], key="filter_status")
            elif context == "Project Type":
                st.selectbox("Project Type", ["All Projects", "Crisis Centers", "Housing", "Workforce"], key="filter_project")
            elif context == "Population":
                st.selectbox("Population", ["All", "Justice-Involved", "Homeless", "Youth", "Co-occurring"], key="filter_population")

    # Sample queries
    st.markdown("---")
    st.markdown("### 💡 Sample Queries")

    for query in use_case_details['sample_queries']:
        if st.button(query, key=f"sample_{query[:20]}", use_container_width=True):
            # Store the sample query to be processed
            st.session_state.sample_query = query
            st.rerun()

    # Quick stats (context-aware based on use case)
    st.markdown("---")
    st.markdown("### 📈 Quick Stats")

    if current_use_case == "Crisis Triage":
        st.metric("Active Cases", "47", delta="↑ 8")
        st.metric("High Risk", "12", delta="-2")
        st.metric("Avg Wait", "14 min", delta="↓ 3")
    elif current_use_case == "Infrastructure Tracking":
        st.metric("Active Projects", "23", delta="↑ 2")
        st.metric("On Schedule", "18", delta="")
        st.metric("Budget Used", "38%", delta="↑ 5%")
    else:
        st.metric("Total Queries", "0", delta="")
        st.caption("Stats will appear after queries")
