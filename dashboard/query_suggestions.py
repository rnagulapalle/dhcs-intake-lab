"""
Top K Query Suggestions for DHCS BHT Dashboard
Industry-standard questions for California counties
"""

# Top K queries organized by California counties and use cases
TOP_QUERIES = {
    "Overview": [
        "How many crisis intake events happened in the last hour?",
        "What is the current crisis call volume across all counties?",
        "Show me high-risk cases from the last 30 minutes",
        "What are the most common presenting problems today?",
        "Which counties have the highest call volumes?",
    ],
    "Los Angeles County": [
        "How many crisis calls did Los Angeles County receive in the last hour?",
        "What's the average wait time for crisis calls in Los Angeles?",
        "Show high-risk cases in Los Angeles County",
        "What's the 988 call volume for Los Angeles?",
        "How many mobile crisis team dispatches in LA County?",
    ],
    "San Diego County": [
        "What's the crisis call volume in San Diego County?",
        "Show me urgent cases in San Diego requiring mobile teams",
        "Average response time for San Diego crisis calls?",
        "How many substance use related cases in San Diego?",
        "San Diego 988 call trends for the last 24 hours",
    ],
    "Orange County": [
        "Crisis intake volume for Orange County in the last hour",
        "High-risk youth cases in Orange County",
        "Orange County mobile crisis team utilization",
        "Suicidal ideation cases in Orange County today",
        "Average call duration for Orange County crisis calls",
    ],
    "Risk Assessment": [
        "How many imminent risk cases in the last hour?",
        "Show all high-risk cases with suicidal ideation",
        "Which counties have the most imminent risk cases?",
        "Track risk level distribution across all counties",
        "Cases requiring immediate 911 transfer",
    ],
    "Language Access": [
        "How many Spanish language crisis calls today?",
        "Which languages are most frequently requested?",
        "Show non-English crisis calls by county",
        "Language access trends for the last week",
        "Mandarin and Cantonese speaker call volumes",
    ],
    "Response Times": [
        "What's the average wait time across all counties?",
        "Counties with longest wait times right now",
        "Mobile crisis team response time analysis",
        "Compare wait times: 988 calls vs walk-ins",
        "Track wait time trends over the last 24 hours",
    ],
    "Dispositions": [
        "How many cases were stabilized via phone?",
        "Mobile crisis team dispatch rates by county",
        "911 transfer frequency in the last hour",
        "ER referral patterns across counties",
        "Success rate of phone stabilization by risk level",
    ],
    "Youth Services": [
        "Crisis calls from individuals under 18",
        "Youth high-risk cases requiring mobile teams",
        "School-related crisis intake patterns",
        "Youth suicidal ideation cases today",
        "Average age of crisis callers by county",
    ],
    "Substance Use": [
        "Substance use related crisis calls today",
        "Overdose risk cases in the last hour",
        "Counties with highest substance use crisis rates",
        "Co-occurring substance use and mental health crises",
        "Withdrawal-related crisis intake trends",
    ],
}

# Auto-completion suggestions (will match as user types)
AUTO_COMPLETE_SUGGESTIONS = []
for category, queries in TOP_QUERIES.items():
    AUTO_COMPLETE_SUGGESTIONS.extend(queries)

# Add more granular auto-complete patterns
AUTO_COMPLETE_PATTERNS = {
    "how many": [
        "how many crisis calls",
        "how many high-risk cases",
        "how many mobile team dispatches",
        "how many 988 calls",
        "how many ER referrals",
    ],
    "what": [
        "what's the average wait time",
        "what's the call volume",
        "what are the most common problems",
        "what's the response time",
        "what counties have the most",
    ],
    "show": [
        "show high-risk cases",
        "show all crisis calls",
        "show mobile team dispatches",
        "show language distribution",
        "show trending issues",
    ],
    "which": [
        "which counties have the highest volume",
        "which languages are most requested",
        "which risk levels are most common",
        "which dispositions are most frequent",
        "which age groups need the most support",
    ],
    "track": [
        "track risk levels over time",
        "track call volume trends",
        "track wait time changes",
        "track mobile team utilization",
        "track language access patterns",
    ],
    "compare": [
        "compare counties by call volume",
        "compare risk levels across regions",
        "compare wait times by channel",
        "compare language access patterns",
        "compare mobile team response times",
    ],
}

# County-specific keywords for smart suggestions
CA_COUNTIES = [
    "Los Angeles", "San Diego", "Orange", "Santa Clara", "Alameda",
    "Sacramento", "Riverside", "San Bernardino", "Contra Costa", "Fresno",
    "Kern", "San Francisco", "Ventura", "San Mateo", "San Joaquin"
]

# Channel types
CHANNELS = ["988 call", "mobile team", "walk-in", "ER referral"]

# Risk levels
RISK_LEVELS = ["low", "moderate", "high", "imminent"]

# Presenting problems
PROBLEMS = [
    "suicidal thoughts", "panic attack", "psychosis", "overdose risk",
    "domestic violence", "withdrawal", "substance use", "depression",
    "anxiety", "mania", "self-harm"
]


def get_suggestions_for_input(user_input: str, max_suggestions: int = 5) -> list:
    """
    Get query suggestions based on user input
    Returns top matching suggestions
    """
    if not user_input:
        return []

    user_input_lower = user_input.lower().strip()
    suggestions = []

    # Exact prefix matches (highest priority)
    for query in AUTO_COMPLETE_SUGGESTIONS:
        if query.lower().startswith(user_input_lower):
            suggestions.append(query)

    # Contains matches (medium priority)
    if len(suggestions) < max_suggestions:
        for query in AUTO_COMPLETE_SUGGESTIONS:
            if user_input_lower in query.lower() and query not in suggestions:
                suggestions.append(query)

    # Pattern-based matches (lower priority)
    if len(suggestions) < max_suggestions:
        for pattern_key, pattern_queries in AUTO_COMPLETE_PATTERNS.items():
            if pattern_key in user_input_lower:
                for query in pattern_queries:
                    if query not in suggestions:
                        suggestions.append(query)

    return suggestions[:max_suggestions]


def get_top_queries_by_category() -> dict:
    """Get all top queries organized by category"""
    return TOP_QUERIES


def get_random_query_examples(count: int = 5) -> list:
    """Get random query examples for cold start"""
    import random
    all_queries = []
    for queries in TOP_QUERIES.values():
        all_queries.extend(queries)
    return random.sample(all_queries, min(count, len(all_queries)))
