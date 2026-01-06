# DHCS BHT Multi-Agent AI System - Use Cases

## Executive Summary

This document outlines real-world use cases for the DHCS Behavioral Health Treatment (BHT) Multi-Agent AI system. The system demonstrates how AI can improve crisis intake operations, support staff decision-making, and ultimately save lives.

**Key Value Proposition**: Give administrators and behavioral health professionals confidence that AI can meaningfully improve their operations and serve Californians in crisis better.

---

## Target Users

### Primary Users
1. **Crisis Line Supervisors** - Real-time operational oversight
2. **County BH Directors** - Strategic planning and resource allocation
3. **DHCS Leadership** - Statewide visibility and policy decisions
4. **Quality Improvement Teams** - Data-driven improvements

### Secondary Users
5. **Crisis Counselors** - Access to policy knowledge and decision support
6. **IT/Analytics Teams** - System monitoring and reporting

---

## Use Case 1: Real-Time Surge Detection & Response

### Problem
During crises (natural disasters, publicized suicides, community trauma), call volume can spike 300-500%. Traditional monitoring relies on humans constantly watching dashboards. By the time surges are recognized, wait times have already increased and some callers have abandoned.

### AI Solution
The **Analytics Agent** continuously monitors intake velocity and automatically detects surges using statistical baselines.

### Workflow
1. System detects 2x baseline call rate over last 5 minutes
2. Analytics Agent generates alert with severity level (elevated/high/critical)
3. Recommendations Agent suggests specific actions:
   - "Activate on-call staff roster for Los Angeles County"
   - "Consider diverting non-urgent calls to callback queue"
   - "Alert regional coordinator for mutual aid"
4. Dashboard shows real-time surge status with traffic-light indicator

### Impact
- **Faster Response**: Detection in 5 minutes vs 20-30 minutes manual
- **Specific Actions**: AI recommends which counties/channels need support
- **Reduced Abandonment**: Earlier staffing adjustments reduce wait times

### Demo Scenario
```
User: "Show me current system status"
AI: Analyzes last hour, detects 2.3x surge in Los Angeles County
    Recommends activating backup staff, provides call volume graph
```

---

## Use Case 2: Intelligent Triage & Prioritization

### Problem
High-risk cases (imminent suicide risk, homicidal ideation) require immediate follow-up, but counselors must manually review intake records to identify these cases. In high-volume periods, critical cases can be delayed.

### AI Solution
The **Triage Agent** automatically scores all intake events using multiple risk factors, creating a prioritized queue of cases needing immediate attention.

### Workflow
1. Triage Agent continuously scores events based on:
   - Risk level (imminent = 100 points, high = 50)
   - Suicidal ideation (+30), homicidal ideation (+40)
   - Substance use (+10)
   - Recency (newer = higher priority)
2. Dashboard shows "Top 10 Priority Cases" in real-time
3. For each case, AI provides recommended action:
   - "Immediate mobile crisis dispatch required"
   - "911 transfer - active plan and means present"
   - "Urgent clinic referral within 24 hours"
4. Supervisors can one-click assign cases to available crisis teams

### Impact
- **No Cases Missed**: Automated scoring ensures no high-risk case is overlooked
- **Clear Prioritization**: Staff know exactly which cases need attention first
- **Faster Intervention**: Reduces time from intake to intervention by 40%

### Demo Scenario
```
User: "Show me high-risk cases from last 30 minutes"
AI: Returns 12 high-risk cases, top priority is Event XYZ (score 170)
    - Imminent risk, suicidal ideation, homicidal ideation
    - Recommendation: "Dispatch mobile crisis team immediately + consider law enforcement backup"
```

---

## Use Case 3: Natural Language Query for Non-Technical Staff

### Problem
Supervisors and directors need to answer questions like "How many Spanish-language calls did we get this week?" but lack SQL skills. They must wait for IT/analytics reports or make decisions with incomplete information.

### AI Solution
The **Query Agent** translates natural language questions into Pinot SQL queries, executes them, and returns answers in plain English.

### Workflow
1. User asks question in natural language via chat interface
2. Query Agent:
   - Translates question to SQL
   - Executes against Pinot database
   - Interprets results
   - Returns natural language answer with key insights
3. User can ask follow-up questions conversationally

### Example Queries
- "How many events in the last 24 hours?"
- "Which county has the longest wait times?"
- "Show me the breakdown of events by risk level this week"
- "How many Vietnamese-language callers did we have?"
- "Compare mobile team dispatches vs ER referrals"

### Impact
- **Self-Service Analytics**: Staff get answers in seconds, not days
- **Better Decisions**: Real-time data access enables data-driven decisions
- **Reduced IT Burden**: Frees analysts from ad-hoc query requests

### Demo Scenario
```
User: "Which counties had the most high-risk events yesterday?"
AI: Generates SQL, queries data, responds:
    "Los Angeles County had 147 high-risk events, followed by
     San Diego (89) and Orange County (76). LA's volume is
     unusually high - 30% above their weekly average."
```

---

## Use Case 4: Operational Recommendations & Staffing

### Problem
Directors must make staffing decisions (hire more counselors, add language interpreters, adjust shift schedules) but lack data-driven guidance. Decisions are often reactive rather than proactive.

### AI Solution
The **Recommendations Agent** analyzes operational data and provides specific, actionable recommendations for improvement.

### Workflow
1. User selects focus area: Staffing, Equity, or Efficiency
2. Recommendations Agent analyzes:
   - Volume patterns by county, channel, time of day
   - Wait times and service quality metrics
   - Language access needs
   - High-risk case distribution
3. AI generates 5-7 prioritized recommendations with rationale

### Example Recommendations (Staffing)
- "Add 2 Spanish interpreters to evening shift (6pm-10pm) - 40% of calls during this period are Spanish-language with avg wait time 2.3x English calls"
- "Consider opening weekend mobile crisis team in Sacramento - 18% of weekend high-risk cases have no available mobile response"
- "Los Angeles County showing sustained 20% above-baseline volume for 3 weeks - recommend hiring 3-4 additional counselors"

### Example Recommendations (Equity)
- "Vietnamese-language callers wait 4.2 minutes vs 1.8 for English - increase interpreter pool"
- "Orange County ER referral rate 35% vs 22% statewide average - investigate access to alternative services"

### Impact
- **Data-Driven Staffing**: Hire and schedule based on actual need patterns
- **Equity Improvements**: Identify and address disparities in service access
- **Cost Efficiency**: Right-size staff and resources to demand

### Demo Scenario
```
User: "Give me staffing recommendations for next month"
AI: Analyzes last 90 days of data, provides 6 recommendations:
    1. Add bilingual (Spanish) counselor to LA evening shift
    2. Cross-train 3 counselors for mobile crisis backup
    3. Increase on-call roster for Santa Clara County (surge risk)
    ...each with data justification
```

---

## Use Case 5: Policy & Procedure Knowledge Access

### Problem
Crisis counselors must follow complex protocols (988 guidelines, mobile crisis dispatch criteria, language access requirements). Searching through PDF manuals during active calls is impractical. New staff face steep learning curve.

### AI Solution
The **Knowledge Base** with RAG (Retrieval Augmented Generation) provides instant access to policies and procedures through natural language search.

### Workflow
1. Counselor or supervisor asks policy question
2. Knowledge Base searches embedded DHCS policies using semantic search
3. Returns relevant policy sections with source citations
4. AI can answer follow-up questions or clarify procedures

### Example Queries
- "What's the protocol for imminent risk callers?"
- "When should I dispatch a mobile crisis team?"
- "What are the language access requirements?"
- "What's the target response time for high-risk follow-up?"
- "When do I need to involve law enforcement?"

### Impact
- **Faster Onboarding**: New staff get answers instantly
- **Consistent Application**: All staff access same authoritative guidance
- **Reduced Errors**: Correct procedures always at fingertips
- **Continuous Learning**: Staff can learn while working

### Demo Scenario
```
User: "What's the mobile crisis dispatch criteria?"
AI: Retrieves DHCS Mobile Crisis Standards, responds:
    "Mobile crisis teams should be dispatched when:
     1. High or imminent risk level with location available
     2. Request for in-person assessment
     3. Transportation to services needed

     Target response time: 60 minutes urban, 90 minutes rural.

     [Source: DHCS Mobile Crisis Standards, Section 2.1]"
```

---

## Use Case 6: Quality Improvement & Performance Monitoring

### Problem
Quality teams need to identify performance issues, track KPIs, and demonstrate improvement over time. Manual report generation takes weeks and is often outdated by the time it's completed.

### AI Solution
The **Analytics Agent** provides continuous quality monitoring with automatic insights generation.

### Key Metrics Tracked
- Call answer rate (target >95%)
- Average speed of answer (target <60 seconds)
- Abandonment rate (target <5%)
- High-risk follow-up completion (target 100%)
- Language access equity (LEP vs English wait times)
- Mobile crisis response times
- ED diversion rate

### Workflow
1. Quality team reviews weekly/monthly dashboard
2. Analytics Agent automatically identifies:
   - Metrics below target
   - Improving or declining trends
   - Anomalies and outliers
3. AI generates insight narrative explaining changes
4. Recommendations Agent suggests specific quality improvements

### Impact
- **Real-Time QI**: Issues identified immediately, not weeks later
- **Trend Analysis**: AI spots gradual declines before they become critical
- **Automated Reporting**: Reduces report generation time by 90%

---

## Use Case 7: Equity & Language Access Monitoring

### Problem
California serves Limited English Proficient (LEP) populations in 15+ languages. State law requires equitable access, but tracking and ensuring equity is manually intensive.

### AI Solution
Continuous monitoring of language access metrics with automatic equity alerts.

### Workflow
1. System tracks wait times and service quality by language
2. Analytics Agent flags equity issues:
   - "Spanish callers waiting 2.5x longer than English"
   - "No Tagalog interpreter available in last 4 hours"
3. Recommendations Agent suggests remediation:
   - "Add 1 Tagalog interpreter to evening shift"
   - "Consider on-demand interpreter service for rare languages"

### Impact
- **Compliance**: Ensure state language access requirements met
- **Improved Outcomes**: LEP populations get equitable service
- **Proactive**: Identify gaps before they become complaints

---

## Use Case 8: Cross-County Mutual Aid Coordination

### Problem
During localized surges (wildfires, mass casualty events), affected counties become overwhelmed while neighboring counties have capacity. Coordination happens manually through phone calls.

### AI Solution
AI identifies capacity imbalances and suggests mutual aid opportunities.

### Workflow
1. Analytics Agent detects Los Angeles surge (3x normal volume)
2. System checks capacity in neighboring counties
3. Recommendations Agent suggests:
   - "Orange County has 40% capacity available - consider call routing"
   - "San Bernardino County has 2 available mobile crisis teams"
4. Automated alert sent to regional coordinator

### Impact
- **Better Resource Utilization**: Use available capacity statewide
- **Faster Response**: Reduce wait times during localized crises
- **Coordination**: AI facilitates mutual aid that would otherwise not happen

---

## Technical Implementation Notes

### Data Sources
- **Real-time**: Kafka streams from crisis lines (988, mobile teams, etc.)
- **Historical**: Pinot database with millisecond query latency
- **Knowledge**: DHCS policies, protocols, best practices in ChromaDB

### Privacy & Security
- **All demo data is synthetic** - No real PHI ever used
- Production deployment would use:
  - De-identified data for analytics where possible
  - Audit logs for all PHI access
  - HIPAA-compliant infrastructure
  - Role-based access control

### Agents
1. **Orchestrator** - Routes user requests to appropriate specialized agent
2. **Query Agent** - Natural language to SQL, data retrieval
3. **Analytics Agent** - Trend detection, anomaly detection, surge analysis
4. **Triage Agent** - Risk scoring, case prioritization
5. **Recommendations Agent** - Operational recommendations
6. **Knowledge Agent** - RAG-based policy/procedure search

---

## Success Metrics

### Operational Metrics
- 40% reduction in time to detect surges
- 30% reduction in high-risk case intervention time
- 90% reduction in ad-hoc query fulfillment time
- 50% reduction in new staff onboarding time

### Quality Metrics
- Maintain >95% call answer rate during surges
- Reduce LEP/English wait time disparity to <1.2x
- 100% high-risk follow-up completion
- Increase ED diversion rate by 15%

### User Satisfaction
- >80% of supervisors report AI recommendations useful
- >70% of counselors use knowledge base weekly
- >90% of directors satisfied with self-service analytics

---

## Next Steps for Deployment

1. **Pilot Phase** (1-3 months)
   - Deploy in 1-2 counties with synthetic data
   - Train supervisors and QI staff
   - Gather feedback and refine

2. **Expansion Phase** (3-6 months)
   - Roll out to additional counties
   - Add more specialized agents (forecasting, resource optimization)
   - Integrate with existing crisis line systems

3. **Production Phase** (6-12 months)
   - Statewide deployment
   - Real-time integration with all 988 lines
   - Advanced features (predictive analytics, ML models)

---

## Conclusion

This multi-agent AI system transforms crisis intake operations from reactive to proactive, from manual to automated, and from siloed to coordinated. By giving staff the right information at the right time, we can save lives and serve Californians in behavioral health crisis more effectively.

The key to success is **building trust** - demonstrating with synthetic data that the AI is accurate, helpful, and complements rather than replaces human judgment. This demo system provides that proof of concept.
