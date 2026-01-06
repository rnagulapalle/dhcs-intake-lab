# DHCS Behavioral Health Transformation (BHT) - Use Cases

**Source**: BHT Project Background & DHCS Prop 1 Fact Sheet
**Date**: January 2026
**System**: DHCS BHT Multi-Agent AI Platform

---

## Overview

The California Department of Health Care Services (DHCS) is implementing a comprehensive Behavioral Health Transformation initiative through Proposition 1 and related legislation (AB 531, SB 326). This document outlines specific use cases where AI agents can support these efforts.

---

## Background: Proposition 1 & BHT Goals

### Proposition 1 (2024)
- **$6.38 billion** bond measure for behavioral health infrastructure
- Focus on treatment facilities, housing, crisis services
- Target populations: individuals experiencing homelessness, justice involvement
- Goals:
  - Increase county compliance with BHT requirements
  - Improve access to behavioral health care
  - Expand treatment facilities statewide

### Key Legislation
- **AB 531**: Behavioral Health Services Act (2020) - foundational BHT framework
- **SB 326**: Behavioral Health Infrastructure (2023) - funding and facilities

---

## Digital Products Being Developed

### 1. Policy Manual (Digital)
**Purpose**: Central repository for BHT policies, guidelines, and procedures

**Current Challenge**:
- Policies scattered across multiple documents
- Hard to find relevant information quickly
- Updates not communicated effectively

**AI Use Case: Policy Q&A Agent**
```
User Query: "What are the requirements for crisis stabilization units under Prop 1?"

AI Response:
According to Proposition 1 guidelines (Section 4.2), crisis stabilization units must:

1. Provide 24/7 acute psychiatric care
2. Average length of stay: 5-10 days
3. Staff-to-patient ratio: 1:6 minimum
4. Crisis intervention training required for all staff
5. Within 30 minutes of emergency services

Source: Prop 1 Implementation Guide, pg 47
Last updated: December 2024

Related policies:
- AB 531 crisis service standards
- DHCS certification requirements
```

**Implementation**: Use ChromaDB RAG over policy documents

### 2. BHOATR (Behavioral Health Outcomes, Accountability, Transparency Report)
**Purpose**: Track and report outcomes, accountability metrics

**Current Challenge**:
- Manual data collection from counties
- Inconsistent reporting formats
- Difficult to identify trends or issues
- Delayed insights

**AI Use Case: Automated Reporting & Analytics Agent**
```
Quarterly Report Generation:

Query: "Generate BHOATR report for Q4 2024, Los Angeles County"

AI Output:
## Q4 2024 BHOATR Report - Los Angeles County

### Key Metrics:
- Total crisis events: 12,847 (↑ 8% vs Q3)
- High-risk interventions: 1,234 (↓ 3%)
- Average response time: 14 minutes (target: 15 min) ✓
- Successful stabilizations: 89% (target: 85%) ✓
- 30-day readmission rate: 12% (target: <15%) ✓

### Outcomes:
- Lives saved (estimated): 47
- Successful referrals to treatment: 3,421
- Housing placements: 289

### Areas for Improvement:
- Weekend wait times 23% higher than weekdays
- Spanish language services need expansion (18% unmet demand)
- North LA region showing higher recidivism

### Recommendations:
1. Add weekend crisis staff (est. $120k/year)
2. Hire 3 bilingual clinicians
3. Open satellite crisis center in North LA

Sources: County crisis database, DHCS outcomes tracker
```

**Implementation**: Analytics Agent + Reporting templates

### 3. Licensing and Certification Portal
**Purpose**: Streamline facility licensing process

**Current Challenge**:
- Complex application process
- Unclear requirements
- Long approval times
- Manual document review

**AI Use Case: Licensing Assistant Agent**
```
Query: "I want to open a new residential treatment facility in Fresno County. What do I need?"

AI Response:
To open a residential treatment facility in Fresno County, you need:

## Step 1: Pre-Application (Est. 2-4 weeks)
✓ Facility location identified
✓ Zoning approval from city/county
✓ Business license
✓ Proof of financial stability

## Step 2: DHCS Application (Est. 8-12 weeks)
Required documents:
- Facility floor plan (must meet AB 531 standards)
- Staffing plan (minimum 1 licensed clinician per 8 beds)
- Emergency protocols
- Medication management procedures
- Cultural competency training plan

## Step 3: Site Inspection (Est. 4-6 weeks)
Checklist:
- Physical accessibility (ADA compliant)
- Safety measures (fire, emergency exits)
- Private counseling rooms
- Secure medication storage

## Step 4: Final Approval (Est. 2 weeks)

Total timeline: 16-24 weeks

Next steps:
1. Schedule pre-application consultation: [Book Here]
2. Download application packet: [Download]
3. Review Fresno County-specific requirements: [View]

Need help? Call DHCS Licensing: 1-800-XXX-XXXX
```

**Implementation**: Policy Q&A Agent + Process Workflow Tracker

### 4. County Portal (Integrated Plans Submission)
**Purpose**: Counties submit Integrated Plans (IP) for BHT compliance

**Current Challenge**:
- Complex IP requirements
- Inconsistent submissions
- Manual review process (slow)
- Counties unsure if they're compliant

**AI Use Case: IP Compliance Checker Agent**
```
Query: "Review my Integrated Plan draft and check for compliance issues"

AI Analysis:
## Integrated Plan Compliance Review - Alameda County

### Overall Compliance: 87% (Good)

### ✅ Compliant Sections:
1. Crisis Services (100%)
   - 24/7 crisis line: Yes
   - Mobile crisis teams: 3 teams (meets 1 per 100k requirement)
   - Crisis stabilization: 2 facilities (adequate)

2. Workforce Development (95%)
   - Training plan: Comprehensive
   - Cultural competency: Addressed
   - Minor issue: No specific plan for peer support specialists

3. Data Reporting (100%)
   - Metrics identified
   - Reporting schedule established

### ⚠️ Needs Attention:
1. **Housing Services (70%)** - CRITICAL
   - Issue: Only 45 supportive housing units planned
   - Required: Minimum 120 units (1 per 500 estimated need)
   - Recommendation: Partner with County Housing Authority
   - Impact: May delay approval

2. **Infrastructure Plan (75%)**
   - Issue: Timeline for crisis center construction unclear
   - Required: Specific milestones with dates
   - Recommendation: Add Gantt chart and quarterly milestones

3. **Budget Justification (80%)**
   - Issue: Prop 1 fund allocation not fully detailed
   - Missing: Line-item budget for new facilities
   - Recommendation: Use template in Appendix C

### Next Steps:
1. Address critical housing services gap (Priority 1)
2. Add infrastructure timeline details
3. Complete budget section
4. Resubmit for review

Estimated time to fix: 2-3 weeks

Questions? Email: [email protected]
```

**Implementation**: Document analysis + Compliance rules engine

---

## Additional Use Cases from Prop 1 Implementation

### 5. Infrastructure Project Tracking
**Purpose**: Track $6.38B in infrastructure projects (facilities, housing)

**Current Challenge**:
- 58 counties implementing projects
- Difficult to track progress statewide
- Bottlenecks not identified early
- Budget overruns

**AI Use Case: Infrastructure Dashboard Agent**
```
Query: "Show me all crisis center construction projects and their status"

AI Response:
## Crisis Center Construction Projects (Statewide)

### In Progress (23 projects)
| County | Project | Budget | Status | Completion |
|--------|---------|--------|--------|------------|
| Los Angeles | North LA Crisis Center | $45M | 67% | Q2 2025 ✓ |
| San Diego | East County Crisis Hub | $32M | 45% | Q4 2025 ⚠️ |
| Fresno | Central Valley Crisis Unit | $28M | 89% | Q1 2025 ✓ |
| ... | ... | ... | ... | ... |

### Delayed Projects (5) - ATTENTION NEEDED:
1. **San Diego East County** (3 months behind)
   - Issue: Permitting delays
   - Impact: 50 beds delayed
   - Action: DHCS intervention scheduled

2. **Riverside County** (2 months behind)
   - Issue: Labor shortage
   - Impact: $2M budget overrun
   - Action: Exploring prefab options

### Completed (12 projects)
- Total beds added: 487
- Total spent: $324M
- Average time to completion: 18 months

### Budget Summary:
- Allocated: $1.2B for crisis centers
- Spent: $456M (38%)
- Committed: $612M (51%)
- Remaining: $132M (11%)

### Recommendations:
1. Accelerate permitting in San Diego
2. Statewide labor pool coordination
3. Consider modular construction for remaining projects

Updated: Real-time from project management system
```

**Implementation**: Pinot for project data + Analytics Agent

### 6. Target Population Analytics
**Purpose**: Understand and serve priority populations

**Target Populations per Prop 1**:
- Individuals experiencing homelessness
- Justice-involved individuals
- Transition-age youth (16-25)
- Individuals with co-occurring disorders
- Underserved racial/ethnic groups

**AI Use Case: Population Insights Agent**
```
Query: "Analyze crisis events for justice-involved individuals in the last quarter"

AI Response:
## Justice-Involved Population Analysis - Q4 2024

### Demographics:
- Total crisis events: 3,847
- % of all events: 23%
- Gender: 71% male, 27% female, 2% non-binary
- Age: 58% ages 25-40

### Presenting Issues:
1. Substance use disorders: 42%
2. Psychotic symptoms: 28%
3. Suicidal ideation: 18%
4. Acute anxiety/panic: 12%

### Touchpoints:
- Prior arrests: Average 3.2
- Prior psychiatric hospitalizations: 68%
- Currently on probation/parole: 79%

### Dispositions:
- Crisis stabilization: 45%
- Psychiatric hospitalization: 22%
- Sobering center: 18%
- Released with referral: 15%

### Gaps Identified:
1. **Critical**: Transition services from jail to community
   - 67% have crisis within 30 days of release
   - Only 23% attend first follow-up appointment

2. **High Priority**: Co-occurring treatment programs
   - 89% have substance use + mental health needs
   - Only 34% of programs equipped for both

3. **Important**: Probation officer training
   - Early intervention could reduce crises by est. 30%

### Recommendations:
1. Launch 30-day post-release intensive case management
2. Expand co-occurring treatment capacity (need 200 more slots)
3. Train 150 probation officers in crisis recognition

Estimated impact: 25% reduction in crisis events, $2.3M savings

Sources: Crisis database, justice system data share
```

**Implementation**: Analytics Agent + Demographic data integration

### 7. Funding Optimization
**Purpose**: Maximize impact of limited BHT funds

**AI Use Case: Resource Allocation Agent**
```
Query: "Where should we allocate $10M in new Prop 1 funds for maximum impact?"

AI Analysis:
## Optimal Fund Allocation Analysis - $10M Budget

### Data Considered:
- Crisis volume by county (12-month trend)
- Current service gaps
- Cost per intervention
- Estimated lives saved
- ROI for different interventions

### Recommended Allocation:

**Option A: Crisis Response Optimization** (Recommended)
Estimated impact: 450 additional successful interventions, 12 lives saved

| Investment | Amount | Impact |
|------------|--------|--------|
| 5 new mobile crisis teams (LA, SD, SF) | $4.2M | +890 responses/year |
| Crisis stabilization expansion (Central Valley) | $3.1M | +120 beds |
| Bilingual crisis staff (statewide) | $1.8M | +23% Spanish coverage |
| Training & supervision | $0.9M | Quality improvement |
| **Total** | **$10M** | **High impact** |

**Option B: Infrastructure Focus**
Estimated impact: 200 beds, long-term capacity

| Investment | Amount | Impact |
|------------|--------|--------|
| 1 new crisis residential facility (Riverside) | $7.5M | +80 beds |
| Renovation of 3 existing facilities | $2.5M | +120 beds |
| **Total** | **$10M** | **Medium impact** |

**Option C: Prevention & Early Intervention**
Estimated impact: 30% reduction in crisis escalations

| Investment | Amount | Impact |
|------------|--------|--------|
| School-based mental health (10 districts) | $4.0M | Reach 45k students |
| Homeless outreach teams (5 counties) | $3.5M | +15 teams |
| Peer support programs | $2.0M | +50 peer counselors |
| Community education | $0.5M | |
| **Total** | **$10M** | **Long-term value** |

### Recommendation: **Option A**
Rationale:
- Immediate impact on crisis response
- Addresses current capacity bottlenecks
- Cost-effective (cost per life saved: $833k)
- Geographically balanced

### 12-Month Projected Outcomes (Option A):
- Crisis response time: 18 min → 12 min (33% improvement)
- Successful stabilizations: 87% → 92%
- High-risk cases missed: 45 → 12
- Lives saved: +12
- ROI: $1.8 return per $1 invested (reduced hospitalizations)

Approve allocation? [Yes] [Modify] [Compare Options]
```

**Implementation**: Advanced Analytics Agent + Cost-benefit modeling

---

## Crisis Triage System (Current Implementation)

**Status**: ✅ Already built and running

This is the demo system you have running locally. Use cases:

### Use Case 8: Real-time Crisis Monitoring
```
Query: "Are we experiencing a crisis surge right now?"

AI Response:
## Surge Detection Analysis

**Status**: ⚠️ MODERATE SURGE DETECTED

Current rate: 8.3 events/minute
Baseline rate: 5.1 events/minute
Multiplier: 1.63x (threshold: 1.5x)

### Surge Details:
- Started: 47 minutes ago (3:15 PM)
- Affected regions: Los Angeles (primary), Orange County
- Primary issues: Substance-related crises (47%)

### Contributing Factors:
- Time of day: Post-lunch peak (normal pattern)
- Weather: Extreme heat alert in LA (103°F)
- Event: Suspected batch of contaminated drugs (unconfirmed)

### Current Capacity:
- Available crisis beds: 23 (statewide)
- Mobile teams on duty: 47
- Average wait time: 18 minutes (↑ from 12 min baseline)

### Recommended Actions:
1. IMMEDIATE: Activate surge protocol in LA County
2. URGENT: Deploy 2 additional mobile teams to LA
3. IMPORTANT: Alert hospitals to expect increased psychiatric admissions
4. MONITOR: Track substance-related patterns for contaminated drug confirmation

Auto-escalation: Alerts sent to LA County Crisis Director
```

### Use Case 9: High-Risk Case Triage
```
Query: "Show me the top 10 highest priority cases right now"

AI Response:
## High-Risk Triage - Top Priority Cases

Updated: 2 minutes ago

**CASE #1 - IMMINENT RISK** 🔴
- Event ID: CR-2024-48392
- Location: San Diego County, Downtown
- Issue: Suicidal ideation + weapon access
- Risk factors: Previous attempt (2 months ago), intoxicated
- Wait time: 4 minutes
- Recommended action: Immediate dispatch, law enforcement coordination
- Assigned: Mobile Team SD-3

**CASE #2 - IMMINENT RISK** 🔴
- Event ID: CR-2024-48387
- Location: Los Angeles County, Venice
- Issue: Homicidal ideation, psychotic symptoms
- Risk factors: Threatening family members, previous violence
- Wait time: 11 minutes ⚠️ ESCALATE
- Recommended action: Law enforcement lead, psychiatric evaluation
- Status: In progress

**CASE #3 - HIGH RISK** 🟠
- Event ID: CR-2024-48401
- Location: Fresno County, Central
- Issue: Severe substance withdrawal + seizure risk
- Risk factors: Homeless, no recent medical care
- Wait time: 6 minutes
- Recommended action: Medical stabilization first, then crisis intervention
- Assigned: Mobile Team FR-1

[... 7 more cases ...]

### Summary:
- Imminent risk: 4 cases
- High risk: 6 cases
- All assigned: Yes
- Avg wait: 8 minutes (target: <10 min) ✓

Refresh: Auto-updates every 60 seconds
```

---

## Implementation Roadmap

### Phase 1: Foundation (Current)
- [x] Crisis Triage System (operational)
- [x] Analytics Agent
- [x] Query Agent
- [x] Knowledge Base (basic)

### Phase 2: Policy & Compliance (Next 3 months)
- [ ] Policy Q&A Agent (from Policy Manual)
- [ ] IP Compliance Checker
- [ ] Licensing Assistant
- [ ] Document ingestion pipeline for all DHCS policies

### Phase 3: Reporting & Infrastructure (Months 4-6)
- [ ] BHOATR Automated Reporting
- [ ] Infrastructure Project Tracker
- [ ] Population Analytics
- [ ] Integration with county systems

### Phase 4: Optimization (Months 7-12)
- [ ] Resource Allocation Agent
- [ ] Predictive analytics (forecast surges)
- [ ] Automated recommendations
- [ ] Statewide dashboard for DHCS leadership

---

## Technical Integration Requirements

### Data Sources Needed:

**For Policy Q&A**:
- [ ] DHCS BHT Policy Manual (PDF/Word)
- [ ] AB 531 full text
- [ ] SB 326 full text
- [ ] Prop 1 implementation guidelines
- [ ] County-specific requirements

**For BHOATR**:
- [ ] County crisis databases (API access)
- [ ] Outcomes tracking system
- [ ] Financial data (grants, spending)

**For Infrastructure Tracking**:
- [ ] Project management systems (Smartsheet, MS Project, etc.)
- [ ] Budget tracking systems
- [ ] Contractor reporting data

**For County Portal**:
- [ ] IP submission system (existing portal)
- [ ] Compliance rules database
- [ ] Review workflow system

### Integration Methods:
- **ChromaDB**: Policy documents, text-heavy resources
- **Pinot**: Time-series data (events, projects, metrics)
- **API Connectors**: External county systems
- **File Upload**: Manual document uploads (temporary solution)

---

## Success Metrics

### Technical Metrics:
- Query response time: < 3 seconds
- Agent accuracy: > 90%
- System uptime: > 99.5%
- Data freshness: < 5 minutes

### Operational Metrics:
- **Policy Q&A**: Staff find answers 70% faster
- **BHOATR**: Report generation time: 2 weeks → 2 hours
- **Licensing**: Application review time: -40%
- **County Portal**: IP compliance rate: 78% → 95%
- **Infrastructure**: On-time completion rate: 65% → 85%

### Impact Metrics:
- Lives saved (estimated)
- Crisis response time reduction
- Treatment access improvement
- Staff satisfaction with AI tools
- Cost savings

---

## Security & Privacy Considerations

### For BHT Use Cases:

**Policy Q&A**:
- No PHI involved ✓
- Public information
- Can be fully public-facing

**BHOATR**:
- Aggregated data only (no individual cases)
- County-level reporting
- Some access controls needed

**Licensing**:
- Business information (not PHI)
- Access control by facility/applicant
- SSL/TLS required

**County Portal**:
- County plans (not PHI)
- Access control by county
- Audit logging

**Crisis Triage** (Current system):
- ⚠️ Contains PHI (if using real data)
- HIPAA compliance required
- Currently: Synthetic data only (safe)

---

## Cost Estimates

### Per Use Case (Monthly AWS Cost):

| Use Case | Compute | Storage | AI API | Total |
|----------|---------|---------|--------|-------|
| Crisis Triage | $50 | $30 | $500 | $580 |
| Policy Q&A | $20 | $5 | $100 | $125 |
| BHOATR | $30 | $20 | $200 | $250 |
| Licensing | $20 | $10 | $50 | $80 |
| County Portal | $30 | $10 | $150 | $190 |
| Infrastructure | $25 | $50 | $75 | $150 |
| **Total (All)** | **$175** | **$125** | **$1,075** | **$1,375** |

**Note**: OpenAI API costs dominate. Consider:
- Using GPT-3.5-turbo where appropriate (10x cheaper)
- Caching common queries
- Fine-tuned models for specific use cases (future)

---

## Next Steps

1. **Review with DHCS Stakeholders**
   - Validate use cases
   - Prioritize by impact
   - Get access to data sources

2. **Pilot Selection**
   - Recommend starting with: Policy Q&A (low risk, high value)
   - Then: BHOATR (immediate need)
   - Then: Infrastructure tracking

3. **Data Partnerships**
   - Establish data sharing agreements with counties
   - API access to existing systems
   - Document ingestion pipeline

4. **Compliance Review**
   - HIPAA assessment for each use case
   - Security architecture review
   - Privacy impact assessments

5. **Training & Change Management**
   - Staff training plans
   - User acceptance testing
   - Feedback mechanisms

---

**This document provides the foundation for expanding the current crisis triage demo into a comprehensive BHT support platform.**
