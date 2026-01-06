# DHCS Dashboard UI Enhancement Summary

## Overview

The DHCS BHT Dashboard has been enhanced with top K queries and auto-completion features to improve user experience and reduce cold-start friction.

## What Was Changed

### 1. Enhanced Chat Assistant UI

**Location**: [dashboard/streamlit_app.py](dashboard/streamlit_app.py)

**New Features**:
- **Top K Query Suggestions (Cold Start)**: When users first open the Chat Assistant (no chat history), they see suggested questions organized in tabs
- **Auto-Completion**: As users type, the system shows relevant query suggestions in real-time
- **Click-to-Query**: Users can click any suggestion to automatically execute it

### 2. Query Suggestions Module

**Location**: [dashboard/query_suggestions.py](dashboard/query_suggestions.py)

**Contains**:
- 70+ curated industry-standard questions organized by categories:
  - Overview (general crisis intake metrics)
  - Los Angeles County, San Diego County, Orange County (county-specific queries)
  - Risk Assessment (high-risk, imminent cases)
  - Language Access (Spanish, Mandarin, Vietnamese)
  - Response Times (wait times, mobile crisis teams)
  - Dispositions (outcomes, 911 transfers, ER referrals)
  - Youth Services (under 18, school-related)
  - Substance Use (overdose risk, withdrawal)

**Functions**:
- `get_top_queries_by_category()` - Returns all queries organized by category
- `get_suggestions_for_input(user_input, max_suggestions=5)` - Returns top matching suggestions based on user input
- `get_random_query_examples(count=5)` - Returns random query examples for cold start

## California County Focus

The query suggestions focus on major California counties:
- Los Angeles County
- San Diego County
- Orange County
- Santa Clara County
- Alameda County
- Sacramento County
- Riverside County
- San Bernardino County
- Contra Costa County
- Fresno County
- Kern County
- San Francisco County
- Ventura County
- San Mateo County
- San Joaquin County

## How to Use

### Cold Start (No Chat History)

When you first open the Chat Assistant, you'll see tabs with suggested questions:

1. **Overview Tab**: General questions about crisis call volume, high-risk cases, trending problems
2. **County Tabs**: Specific questions for Los Angeles, San Diego, Orange County
3. **Topic Tabs**: Risk Assessment, Language Access, Response Times, Dispositions, Youth Services, Substance Use

**Example Questions**:
- "How many crisis intake events happened in the last hour?"
- "What's the crisis call volume in San Diego County?"
- "Show me high-risk cases requiring mobile teams"
- "How many Spanish language crisis calls today?"
- "Youth suicidal ideation cases today"

### Auto-Completion (While Typing)

As you type in the query input box, you'll see suggestions that match your input:

**Typing "how many"** → Shows suggestions like:
- "how many crisis calls did Los Angeles County receive in the last hour?"
- "how many high-risk cases requiring mobile teams"
- "how many 988 calls"

**Typing "show high"** → Shows:
- "show high-risk cases in Los Angeles County"
- "show high-risk cases in San Diego requiring mobile teams"

**Typing "san diego"** → Shows:
- "What's the crisis call volume in San Diego County?"
- "Show me urgent cases in San Diego requiring mobile teams"
- "Average response time for San Diego crisis calls?"

### Matching Logic

The auto-completion uses three strategies (in priority order):

1. **Prefix Matching** (highest priority): Queries that start with your input
2. **Contains Matching** (medium priority): Queries that contain your input anywhere
3. **Pattern Matching** (lower priority): Queries based on common patterns (how, what, show, which, track, compare)

## AWS Deployment Status

### ✅ What's Running on AWS

- **Dashboard Service**: Enhanced UI with top K queries and auto-completion
  - URL: http://dhcs-bht-demo-alb-398486025.us-west-2.elb.amazonaws.com:8501
  - Status: ACTIVE (1 task running)
  - Health Check: /_stcore/health (passing)

### ❌ What's NOT Running on AWS (Cost Savings)

- **API Backend**: Not deployed to AWS (saves ~$15-20/month)
- **Kafka/Zookeeper**: Not deployed to AWS (saves ~$40-60/month)
- **Apache Pinot**: Not deployed to AWS (saves ~$30-40/month)
- **Generator**: Not continuously running (saves on data processing costs)

**Total Estimated Savings**: ~$85-120/month

### 💰 Current AWS Costs

- Dashboard only: ~$10-15/month (1 Fargate task, 0.5 vCPU, 1GB RAM)
- ALB: ~$16/month (load balancer hours)
- ECR: ~$1-2/month (image storage)

**Total Estimated Monthly Cost**: ~$27-33/month (vs $150-200/month for full stack)

## Local Development Setup

All services run locally for development and testing:

```bash
# Start all services (Kafka, Pinot, API, Dashboard, Generator API)
docker-compose up -d

# Access locally
# - Dashboard: http://localhost:8501
# - Agent API: http://localhost:8000/docs
# - Generator API: http://localhost:8001/docs
# - Pinot Console: http://localhost:9000
```

## On-Demand Data Generation

The data generator has been converted from continuous 24/7 generation to on-demand API:

**Generate data for 5 minutes at 5 events/second**:
```bash
curl -X POST http://localhost:8001/generate \
  -H 'Content-Type: application/json' \
  -d '{"duration_minutes": 5, "rate_per_second": 5}'
```

**Check status**:
```bash
curl http://localhost:8001/status
```

**Stop generation**:
```bash
curl -X POST http://localhost:8001/stop
```

See [DATA_GENERATOR_CONTROL.md](DATA_GENERATOR_CONTROL.md) for full documentation.

## Testing the Enhanced UI

### Local Testing
1. Open http://localhost:8501
2. Navigate to "💬 Chat Assistant"
3. You should see tabs with suggested questions
4. Click any suggestion or start typing to see auto-completion

### AWS Testing
1. Open http://dhcs-bht-demo-alb-398486025.us-west-2.elb.amazonaws.com:8501
2. Navigate to "💬 Chat Assistant"
3. Same experience as local

## Files Changed

### New Files
- [dashboard/query_suggestions.py](dashboard/query_suggestions.py) - Query suggestions module

### Modified Files
- [dashboard/streamlit_app.py](dashboard/streamlit_app.py) - Enhanced Chat Assistant UI

### Documentation Files
- [UI_ENHANCEMENT_SUMMARY.md](UI_ENHANCEMENT_SUMMARY.md) - This file
- [DATA_GENERATOR_CONTROL.md](DATA_GENERATOR_CONTROL.md) - Generator API documentation

## Future Enhancements

Potential improvements for the UI:

1. **Personalization**: Track user's most common queries and show personalized suggestions
2. **Query History**: Save query history across sessions
3. **Favorites**: Allow users to save favorite queries
4. **Query Templates**: Allow users to create custom query templates with parameters
5. **Voice Input**: Add speech-to-text for hands-free querying
6. **Mobile Optimization**: Optimize UI for mobile devices
7. **Dark Mode**: Add dark mode support
8. **Export Results**: Allow exporting query results to CSV/Excel

## Support

For questions or issues:
- Check [DATA_GENERATOR_CONTROL.md](DATA_GENERATOR_CONTROL.md) for generator API usage
- Review [DEPLOYMENT_INFO.txt](DEPLOYMENT_INFO.txt) for AWS deployment details
- Check docker logs: `docker logs dashboard` or `docker logs agent-api`

## Summary

✅ Enhanced UI with top K queries and auto-completion
✅ Deployed to AWS with cost optimization
✅ On-demand data generation (no continuous 24/7 processes)
✅ Comprehensive California county-specific queries
✅ Industry-standard behavioral health questions
✅ Real-time auto-completion as users type
✅ Estimated monthly savings: $85-120
