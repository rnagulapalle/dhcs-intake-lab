"""
Policy Documents Generator for DHCS BHT Knowledge Base
Generates comprehensive synthetic policy documents for all BHT use cases
"""
import json
import os
from typing import List, Dict


class PolicyDocumentsGenerator:
    """Generate synthetic DHCS policy documents for vector DB"""

    @staticmethod
    def generate_all_documents() -> List[Dict[str, any]]:
        """Generate all policy documents"""
        documents = []

        # Prop 1 Documents
        documents.extend(PolicyDocumentsGenerator._generate_prop1_docs())

        # AB 531 Documents
        documents.extend(PolicyDocumentsGenerator._generate_ab531_docs())

        # SB 326 Documents
        documents.extend(PolicyDocumentsGenerator._generate_sb326_docs())

        # Crisis Stabilization Unit Requirements
        documents.extend(PolicyDocumentsGenerator._generate_csu_docs())

        # Licensing Requirements
        documents.extend(PolicyDocumentsGenerator._generate_licensing_docs())

        # Integrated Plan Requirements
        documents.extend(PolicyDocumentsGenerator._generate_ip_docs())

        # BHOATR Requirements
        documents.extend(PolicyDocumentsGenerator._generate_bhoatr_docs())

        # Infrastructure Standards
        documents.extend(PolicyDocumentsGenerator._generate_infrastructure_docs())

        # Population-Specific Guidelines
        documents.extend(PolicyDocumentsGenerator._generate_population_docs())

        # Budget and Allocation Guidelines
        documents.extend(PolicyDocumentsGenerator._generate_budget_docs())

        return documents

    @staticmethod
    def _generate_prop1_docs() -> List[Dict]:
        """Proposition 1 documents"""
        return [
            {
                "id": "prop1_overview",
                "content": """
                Proposition 1: Behavioral Health Infrastructure Bond Act (2024)

                OVERVIEW:
                Proposition 1 authorizes $6.38 billion in general obligation bonds for construction,
                renovation, and acquisition of behavioral health facilities throughout California.

                FUNDING BREAKDOWN:
                - Crisis Stabilization Units: $1.8 billion
                - Residential Treatment Facilities: $2.1 billion
                - Supportive Housing for Behavioral Health: $1.5 billion
                - Mobile Crisis Infrastructure: $480 million
                - Workforce Development and Training: $500 million

                PRIORITY POPULATIONS:
                1. Individuals experiencing homelessness with serious mental illness or substance use disorders
                2. Justice-involved individuals with behavioral health needs
                3. Transition-age youth (16-25 years) with emerging serious mental illness
                4. Individuals with co-occurring mental health and substance use disorders

                COUNTY ALLOCATION FORMULA:
                - 40% based on population size
                - 30% based on demonstrated need (homeless counts, crisis call volume)
                - 20% based on current service gaps
                - 10% competitive grants for innovation

                COMPLIANCE REQUIREMENTS:
                Counties must submit Integrated Plans demonstrating:
                - Comprehensive needs assessment
                - Service gap analysis
                - Three-year implementation timeline
                - Budget justification
                - Workforce development plan
                - Data reporting and accountability measures

                TIMELINE:
                - Phase 1 (Year 1): Planning and design
                - Phase 2 (Years 2-3): Major construction
                - Phase 3 (Years 4-5): Completion and service launch

                All facilities must be operational within 5 years of funding award.
                """,
                "metadata": {
                    "source": "Proposition 1 Implementation Guide 2024",
                    "section": "Overview and Requirements",
                    "version": "2024.1",
                    "category": "policy",
                    "use_case": "Policy Q&A, IP Compliance, Infrastructure Tracking"
                }
            },
            {
                "id": "prop1_crisis_standards",
                "content": """
                Proposition 1: Crisis Stabilization Unit Standards

                FACILITY REQUIREMENTS:

                Physical Infrastructure:
                - Minimum 16 beds per facility (optimal: 20-30 beds)
                - Private assessment rooms (minimum 3)
                - Group therapy space (minimum 800 sq ft)
                - Secure outdoor space for patient use
                - Administrative and staff areas
                - Medication storage and dispensing area (secure)

                Staffing Requirements (24/7):
                - Medical Director (psychiatrist): On-call minimum
                - Psychiatric nurse practitioners: 1 per 10 beds
                - Licensed Clinical Social Workers/MFTs: 1 per 8 beds
                - Psychiatric technicians: 1 per 6 beds
                - Peer support specialists: 1 per shift
                - Security staff: As needed based on risk assessment

                Clinical Standards:
                - Average length of stay: 5-10 days
                - Maximum length of stay: 14 days
                - Voluntary admission only (5150 transfers to IMD)
                - Evidence-based interventions required
                - Medication-assisted treatment available

                Accessibility:
                - ADA compliant
                - Within 30 minutes of emergency services
                - Public transportation accessible
                - Language services for all threshold languages

                Budget Guidelines:
                - Construction cost: $400,000-$600,000 per bed
                - Annual operating cost: $75,000-$100,000 per bed
                - Staffing represents 60-70% of operating costs

                Performance Metrics:
                - Occupancy rate target: 75-85%
                - Successful discharge to community services: >80%
                - 30-day readmission rate: <15%
                - Average wait time for admission: <4 hours
                """,
                "metadata": {
                    "source": "Proposition 1 Facility Standards",
                    "section": "Crisis Stabilization Units",
                    "version": "2024.1",
                    "category": "standards",
                    "use_case": "Policy Q&A, Licensing, Infrastructure"
                }
            },
            {
                "id": "prop1_housing_requirements",
                "content": """
                Proposition 1: Supportive Housing Requirements

                DEFINITION:
                Supportive housing provides affordable housing integrated with intensive
                wrap-around behavioral health services for individuals with serious mental illness.

                UNIT SPECIFICATIONS:
                - Studio or 1-bedroom units
                - Private bathroom and kitchenette
                - Minimum 350 square feet
                - Accessible units: 10% of total
                - Substance-free environment not required (harm reduction approach)

                SERVICE REQUIREMENTS:
                - Intensive case management: 1 case manager per 15 residents
                - On-site mental health services (minimum 20 hours/week)
                - Substance use disorder treatment access
                - Life skills and employment support
                - Peer support services
                - 24/7 crisis support access

                ELIGIBILITY CRITERIA:
                Priority 1: Chronically homeless with serious mental illness
                Priority 2: Homeless with serious mental illness
                Priority 3: At imminent risk of homelessness with serious mental illness
                Priority 4: Justice-involved with serious mental illness

                Serious Mental Illness Defined:
                - Schizophrenia spectrum disorders
                - Bipolar disorder
                - Major depressive disorder (severe, recurrent)
                - Co-occurring substance use disorder
                - Documented functional impairment

                FUNDING MODEL:
                - Capital construction: Prop 1 bond funds
                - Operating subsidy: County behavioral health department
                - Tenant contribution: 30% of income
                - Services funding: Medi-Cal or county mental health funds

                COMPLIANCE METRICS:
                - Housing retention rate: >85% at 12 months
                - Connection to services: 100% within 30 days
                - Crisis intervention reduction: >40% compared to baseline
                - Tenant satisfaction: >75% positive

                County must demonstrate partnership with housing developers
                and commitment to long-term operating support (minimum 20 years).
                """,
                "metadata": {
                    "source": "Proposition 1 Housing Standards",
                    "section": "Supportive Housing Requirements",
                    "version": "2024.1",
                    "category": "standards",
                    "use_case": "Policy Q&A, IP Compliance, Infrastructure"
                }
            }
        ]

    @staticmethod
    def _generate_ab531_docs() -> List[Dict]:
        """AB 531 (Behavioral Health Services Act) documents"""
        return [
            {
                "id": "ab531_overview",
                "content": """
                Assembly Bill 531: Behavioral Health Services Act (2020)

                PURPOSE:
                AB 531 establishes the foundational framework for California's Behavioral Health
                Transformation (BHT) initiative, creating comprehensive crisis response systems
                and expanding treatment capacity statewide.

                KEY PROVISIONS:

                1. CRISIS RESPONSE SYSTEMS:
                   - 24/7 crisis hotline (988) in all counties
                   - Mobile crisis response teams
                   - Crisis stabilization units
                   - Crisis residential treatment
                   - Warm line peer support

                2. MOBILE CRISIS TEAM STANDARDS:
                   - Must include licensed mental health clinician
                   - Peer support specialist recommended
                   - Response time: <60 minutes urban, <90 minutes rural
                   - Available 24/7
                   - Voluntary transport capability
                   - Connection to follow-up services within 24 hours

                3. DATA AND REPORTING:
                   - Counties must track all crisis contacts
                   - Quarterly reporting to DHCS
                   - Demographic data collection (race, ethnicity, language, age)
                   - Outcome tracking (30, 60, 90 days post-crisis)
                   - Public dashboard with aggregate data

                4. WORKFORCE DEVELOPMENT:
                   - Peer support specialist certification program
                   - Crisis intervention training standards
                   - Bilingual staff recruitment incentives
                   - Retention bonuses for high-need areas
                   - Loan forgiveness for mental health professionals

                5. EQUITY REQUIREMENTS:
                   - Culturally responsive services
                   - Language access (all threshold languages)
                   - LGBTQ+ competency training
                   - Tribal consultation and coordination
                   - Disparities reduction targets

                FUNDING:
                - State general fund: $500 million annually
                - Mental Health Services Act (MHSA) flexible funding
                - Medi-Cal reimbursement for services
                - Prop 1 capital for infrastructure

                IMPLEMENTATION TIMELINE:
                - Year 1: Crisis hotline operational (all counties)
                - Year 2: Mobile crisis teams established
                - Year 3: Crisis stabilization units operational
                - Year 4-5: Full system integration and optimization

                Counties failing to meet requirements may face funding reductions
                after 2-year grace period and technical assistance.
                """,
                "metadata": {
                    "source": "AB 531 Full Text and Regulations",
                    "section": "Overview and Requirements",
                    "version": "2024.1",
                    "category": "legislation",
                    "use_case": "Policy Q&A, IP Compliance"
                }
            },
            {
                "id": "ab531_mobile_crisis_standards",
                "content": """
                AB 531: Mobile Crisis Team Standards and Best Practices

                TEAM COMPOSITION:
                Required:
                - Licensed mental health clinician (LCSW, LMFT, LPCC, Psych NP, or Psychologist)
                - Crisis intervention specialist or paramedic (with mental health training)

                Recommended:
                - Peer support specialist (with lived experience)
                - Substance use disorder counselor
                - Language interpreter (for high-need languages)

                DISPATCH CRITERIA:
                Mobile teams should be dispatched for:
                - Mental health crisis with location information
                - Suicidal ideation requiring in-person assessment
                - Requests for voluntary psychiatric evaluation
                - Welfare checks with behavioral health concern
                - De-escalation needs in community settings
                - Follow-up crisis assessments within 24 hours

                NOT appropriate for:
                - Active violence or weapon present (law enforcement lead)
                - Medical emergency without mental health component
                - Criminal activity without crisis component

                RESPONSE PROTOCOLS:

                Initial Contact (First 5 minutes):
                - Safety assessment (team, individual, bystanders)
                - Rapport building and de-escalation
                - Gather basic information

                Assessment Phase (10-20 minutes):
                - Comprehensive mental status exam
                - Suicide risk assessment
                - Substance use screening
                - Medical needs assessment
                - Support system identification

                Intervention Phase (20-45 minutes):
                - Crisis counseling and stabilization
                - Safety planning
                - Medication reconciliation
                - Resource connection

                Disposition Options:
                1. Stabilized in place with follow-up plan
                2. Voluntary transport to crisis stabilization unit
                3. Connection to urgent clinic or crisis respite
                4. Referral to emergency department (medical needs)
                5. 5150 hold (if criteria met and least restrictive)

                DOCUMENTATION REQUIREMENTS:
                Within 2 hours of contact:
                - Crisis assessment form completed
                - Risk assessment documented
                - Disposition and safety plan recorded
                - Follow-up appointments scheduled
                - Warm handoff to continuing care

                QUALITY STANDARDS:
                - Average response time: <45 minutes
                - Successful community stabilization: >75%
                - Emergency department diversion: >60%
                - Follow-up contact completion: >85%
                - Client satisfaction: >80% positive ratings

                EQUIPMENT AND RESOURCES:
                - Mobile communications (cell + radio backup)
                - Assessment and safety planning materials
                - Resource guides (county-specific)
                - Voluntary transport vehicle
                - PPE and safety equipment
                - Medication information databases
                """,
                "metadata": {
                    "source": "AB 531 Implementation Manual",
                    "section": "Mobile Crisis Response",
                    "version": "2024.1",
                    "category": "protocol",
                    "use_case": "Policy Q&A, Licensing"
                }
            }
        ]

    @staticmethod
    def _generate_sb326_docs() -> List[Dict]:
        """SB 326 (Behavioral Health Infrastructure) documents"""
        return [
            {
                "id": "sb326_overview",
                "content": """
                Senate Bill 326: Behavioral Health Infrastructure Bond Act (2023)

                PURPOSE:
                SB 326 provides $2.2 billion in bond authority specifically for renovation
                and expansion of existing behavioral health facilities, complementing
                Proposition 1's focus on new construction.

                ELIGIBLE PROJECTS:

                Renovation Projects:
                - Seismic retrofitting of existing psychiatric facilities
                - ADA compliance upgrades
                - HVAC and infrastructure modernization
                - Technology infrastructure (EHR, telehealth)
                - Safety and security improvements

                Expansion Projects:
                - Bed capacity increases (minimum 20% increase)
                - New crisis wings in existing facilities
                - Community clinic expansions
                - Mobile crisis fleet expansion

                Equipment and Technology:
                - Electronic health record systems
                - Telehealth infrastructure
                - Crisis communication systems
                - Medical equipment for crisis units

                FUNDING ALLOCATION:
                - Large counties (>1M population): $30M-$100M each
                - Medium counties (250K-1M): $10M-$30M each
                - Small counties (<250K): $2M-$10M each
                - Tribal nations: $50M set-aside
                - Innovation grants: $100M competitive

                APPLICATION PROCESS:

                Phase 1 - Eligibility (Month 1-2):
                - Submit notice of intent
                - Preliminary project description
                - Budget estimate
                - Local match commitment (10% minimum)

                Phase 2 - Full Application (Month 3-5):
                - Detailed project plans and specifications
                - Environmental review compliance
                - Community engagement documentation
                - Workforce impact analysis
                - Timeline and milestones

                Phase 3 - Review and Approval (Month 6-8):
                - Technical review by DHCS
                - Community stakeholder input
                - Funding decision and award

                LOCAL MATCH REQUIREMENTS:
                - County general fund: 10% minimum
                - Can include in-kind contributions
                - MHSA funds eligible for match
                - Private philanthropy accepted

                PROJECT TIMELINES:
                - Renovation projects: 12-24 months
                - Expansion projects: 18-36 months
                - Equipment/technology: 6-12 months
                - Extensions require DHCS approval

                REPORTING REQUIREMENTS:
                - Quarterly financial reports
                - Semi-annual progress reports
                - Final project completion report
                - 3-year post-completion outcome report

                Projects failing to meet timelines may require fund reversion.
                """,
                "metadata": {
                    "source": "SB 326 Implementation Guidelines",
                    "section": "Overview and Application Process",
                    "version": "2024.1",
                    "category": "legislation",
                    "use_case": "Policy Q&A, Infrastructure Tracking"
                }
            }
        ]

    @staticmethod
    def _generate_csu_docs() -> List[Dict]:
        """Crisis Stabilization Unit detailed requirements"""
        return [
            {
                "id": "csu_operational_standards",
                "content": """
                Crisis Stabilization Unit (CSU) Operational Standards

                ADMISSION CRITERIA:

                Appropriate Admissions:
                - Acute psychiatric crisis not requiring locked setting
                - Substance intoxication with psychiatric component
                - Suicide risk with agreement to safety plan
                - Medication management needs during crisis
                - Social crisis with mental health exacerbation
                - Step-down from hospital psychiatric unit

                Exclusion Criteria:
                - Active psychosis with danger to others (needs psychiatric hospital)
                - Severe medical instability (needs emergency department)
                - 5150 hold status (needs locked facility)
                - Active withdrawal requiring medical detox

                CLINICAL PROGRAMMING:

                Required Daily Activities:
                - Individual therapy session (minimum 30 minutes)
                - Group therapy (2 sessions daily)
                - Psychiatric medication evaluation and management
                - Nursing assessment (twice daily)
                - Recreation therapy or activities
                - Meal planning and nutritional support
                - Discharge planning (from day 1)

                Evidence-Based Interventions:
                - Dialectical Behavior Therapy (DBT) skills
                - Cognitive Behavioral Therapy (CBT)
                - Motivational Interviewing
                - Trauma-Informed Care approaches
                - Safety planning and crisis coping
                - Peer support services

                MEDICATION SERVICES:
                - Psychiatric evaluation within 4 hours of admission
                - Medication reconciliation completed
                - Prescription filling arranged
                - Education on medications provided
                - Side effect monitoring
                - Discharge medication supply (7-14 days)

                DISCHARGE PLANNING:

                Required Before Discharge:
                - Follow-up appointment scheduled (within 7 days)
                - Outpatient provider identified and contacted
                - Medications and prescriptions provided
                - Crisis plan documented and reviewed
                - Transportation arranged
                - Family/support system engaged (with consent)
                - Housing stability addressed

                Discharge Destinations:
                - Outpatient mental health services (primary goal)
                - Intensive outpatient program (IOP)
                - Partial hospitalization program (PHP)
                - Supportive housing with services
                - Return to stable housing with outpatient care
                - Transfer to higher level of care (if needed)

                QUALITY METRICS:

                Process Measures:
                - Admission within 4 hours of acceptance: >90%
                - Psychiatric eval within 4 hours: 100%
                - Discharge plan completed: 100%
                - Follow-up appointment scheduled: 100%

                Outcome Measures:
                - Successful community discharge: >85%
                - Attendance at first follow-up: >70%
                - 30-day psychiatric hospitalization: <20%
                - 30-day return to crisis services: <25%
                - Client satisfaction (positive rating): >80%

                STAFFING SCHEDULE (24-hour facility):

                Day Shift (7am-3pm):
                - Psychiatrist or Psych NP: On-site
                - Clinical supervisor (LCSW/LMFT): 1
                - Therapists: 2
                - Psychiatric nurses: 2
                - Psychiatric technicians: 3
                - Peer specialists: 2

                Evening Shift (3pm-11pm):
                - Psychiatrist: On-call
                - Clinical supervisor: 1
                - Therapists: 1
                - Psychiatric nurses: 2
                - Psychiatric technicians: 3
                - Peer specialists: 1

                Night Shift (11pm-7am):
                - Psychiatrist: On-call
                - Nursing supervisor: 1
                - Psychiatric nurses: 1
                - Psychiatric technicians: 2
                """,
                "metadata": {
                    "source": "DHCS Crisis Stabilization Standards",
                    "section": "Operational Requirements",
                    "version": "2024.1",
                    "category": "operations",
                    "use_case": "Policy Q&A, Licensing"
                }
            }
        ]

    @staticmethod
    def _generate_licensing_docs() -> List[Dict]:
        """Licensing and certification requirements"""
        return [
            {
                "id": "licensing_process_overview",
                "content": """
                DHCS Behavioral Health Facility Licensing Process

                FACILITY TYPES AND LICENSES:

                1. Crisis Stabilization Unit (CSU)
                   License type: Mental Health Rehabilitation Center (MHRC) - Crisis
                   Capacity: 16-30 beds
                   Timeline: 16-24 weeks

                2. Residential Treatment Facility
                   License type: Mental Health Rehabilitation Center (MHRC) - Residential
                   Capacity: 8-50 beds
                   Timeline: 20-32 weeks

                3. Crisis Residential Program
                   License type: Residential Care Facility for Adults (RCFA) - Mental Health
                   Capacity: 6-16 beds
                   Timeline: 12-20 weeks

                4. Partial Hospitalization Program
                   License type: Outpatient Mental Health Program
                   Capacity: 20-60 clients
                   Timeline: 12-16 weeks

                LICENSING PROCESS (Standard Path):

                PHASE 1: Pre-Application (2-4 weeks)
                Required:
                - Facility location secured
                - Zoning approval obtained
                - Business entity established
                - Financial stability documentation
                - Community notification completed

                Submit to DHCS:
                - Pre-application inquiry form
                - Facility address and description
                - Proposed services and capacity
                - Estimated timeline

                DHCS Response:
                - Preliminary eligibility determination
                - County-specific requirements provided
                - Application packet and checklist

                PHASE 2: Application Preparation (4-8 weeks)
                Required Documents:
                1. Completed DHCS licensing application (LIC 9217)
                2. Facility floor plans (to scale, room dimensions)
                3. Program description and policies
                4. Staffing plan with job descriptions
                5. Administrator qualifications
                6. Medical director agreement (if required)
                7. Emergency and safety plans
                8. Medication management protocols
                9. Admission and discharge criteria
                10. Quality improvement plan

                Financial Documents:
                - Operating budget (2 years)
                - Proof of liability insurance ($1M minimum)
                - Surety bond or financial guarantee
                - Source of startup funding

                Personnel Documents:
                - Administrator resume and license
                - Staff credentials (Licensed clinicians)
                - Background check authorization
                - TB clearance for all staff

                PHASE 3: Application Review (6-10 weeks)
                DHCS Review Process:
                - Completeness review (5 business days)
                - Technical review by licensing staff
                - Policy and procedure review
                - Staffing plan evaluation
                - Financial viability assessment

                Common Deficiencies:
                - Incomplete floor plans
                - Insufficient clinical staffing
                - Unclear admission criteria
                - Missing emergency protocols
                - Inadequate financial documentation

                Applicant Response:
                - Deficiency correction (30 days given)
                - Resubmission review (2-3 weeks)

                PHASE 4: Site Inspection (2-3 weeks)
                Inspection Areas:
                - Physical plant (ADA compliance, safety, cleanliness)
                - Medication storage and handling
                - Medical records systems
                - Emergency equipment and procedures
                - Staff training and credentials
                - Policies and procedures implementation

                Common Issues:
                - Fire safety violations
                - ADA accessibility gaps
                - Inadequate medication security
                - Missing safety equipment
                - Incomplete staff files

                Correction Period:
                - Minor issues: 14 days
                - Major issues: 30 days
                - Re-inspection scheduled

                PHASE 5: Final Approval (1-2 weeks)
                Upon successful inspection:
                - Conditional license issued
                - Valid for 6 months
                - Begin operations allowed
                - Full license issued after 6-month operational review

                ONGOING COMPLIANCE:
                - Annual license renewal
                - Unannounced inspections (1-2 per year)
                - Complaint investigations
                - Quarterly financial reports
                - Annual program evaluation

                LICENSE FEES:
                - Application fee: $3,000-$5,000 (non-refundable)
                - Annual license fee: $2,000-$4,000 (capacity-based)
                - Inspection fees: $500 per inspection
                - Late renewal penalty: 50% of annual fee

                EXPEDITED LICENSING (Available for high-need areas):
                - Timeline: 8-12 weeks (vs 16-24 weeks)
                - Additional fee: $10,000
                - Requirements: Same standards, faster review
                - Eligibility: County with demonstrated crisis capacity shortage
                """,
                "metadata": {
                    "source": "DHCS Licensing and Certification Division",
                    "section": "Licensing Process Guide",
                    "version": "2024.1",
                    "category": "licensing",
                    "use_case": "Licensing Assistant"
                }
            },
            {
                "id": "facility_requirements_by_type",
                "content": """
                Facility Physical Requirements by License Type

                CRISIS STABILIZATION UNIT (CSU):

                Minimum Space Requirements:
                - Total square footage: 4,000-6,000 sq ft (16-30 beds)
                - Per bed: 150-200 sq ft minimum

                Required Rooms/Areas:
                - Private assessment rooms: Minimum 3 (100 sq ft each)
                - Group therapy room: 800 sq ft minimum
                - Medication room (secure): 120 sq ft
                - Nursing station: 200 sq ft
                - Staff offices: 1 per 5 staff (80 sq ft each)
                - Break room (staff): 300 sq ft
                - Kitchen (warming only): 200 sq ft
                - Laundry facilities: Commercial capacity
                - Secure outdoor space: 500 sq ft minimum
                - Storage: 300 sq ft

                Bedroom Requirements:
                - Single rooms: 120 sq ft minimum
                - Double rooms: 200 sq ft minimum (max 2 beds per room)
                - Each bed: Call button, lighting, storage
                - Windows required in all bedrooms
                - Privacy (curtains or dividers for double rooms)

                Bathroom Requirements:
                - Minimum 1 bathroom per 4 beds
                - ADA accessible: Minimum 2 bathrooms
                - Shower facilities: 1 per 6 beds
                - Safety features: Breakaway bars, suicide-resistant fixtures

                Safety Requirements:
                - All windows: Security screens or limited opening (4 inches max)
                - Doors: Non-lockable from inside (except bathrooms with override)
                - Camera surveillance: Common areas (not bedrooms/bathrooms)
                - Emergency exits: Alarmed
                - Fire suppression: Sprinkler system required
                - Secure perimeter: Fencing or controlled access

                Technology Requirements:
                - Nurse call system in all rooms
                - Electronic health records capability
                - Secure medication dispensing system
                - Staff communication system (phones, radios, or panic buttons)

                RESIDENTIAL TREATMENT FACILITY:

                Minimum Space Requirements:
                - Per bed: 100 sq ft minimum
                - Total: Based on capacity (8-50 beds)

                Required Spaces:
                - Individual therapy rooms: 1 per 10 beds (100 sq ft each)
                - Group therapy room: 600 sq ft
                - Activities/recreation room: 400 sq ft
                - Dining room: 15 sq ft per bed
                - Kitchen: Full commercial or warming
                - Laundry: On-site or contracted

                Bedroom Requirements:
                - Maximum 4 beds per room
                - Minimum 80 sq ft per person
                - Personal storage for each resident
                - Natural light required

                Bathroom Requirements:
                - Minimum 1 bathroom per 8 residents
                - Minimum 1 ADA bathroom
                - Shower: 1 per 8 residents

                COUNTY-SPECIFIC VARIATIONS:

                Los Angeles County Additional Requirements:
                - Minimum outdoor space: 50 sq ft per bed
                - Soundproofing in therapy rooms
                - Bilingual signage (English/Spanish minimum)
                - Additional parking (1 space per 4 beds)

                San Francisco Bay Area (Alameda, SF, Marin, SM Counties):
                - Enhanced seismic standards (2019 code minimum)
                - Additional staff space (20% above minimum)
                - Secure bicycle storage
                - Public transit access required

                Rural Counties (Less than 250K population):
                - Reduced square footage acceptable (10% below minimums)
                - Telehealth infrastructure required
                - Generator backup power required
                - Well water testing (if applicable)
                """,
                "metadata": {
                    "source": "DHCS Licensing Standards Manual",
                    "section": "Physical Plant Requirements",
                    "version": "2024.1",
                    "category": "licensing",
                    "use_case": "Licensing Assistant"
                }
            }
        ]

    @staticmethod
    def _generate_ip_docs() -> List[Dict]:
        """Integrated Plan requirements"""
        return [
            {
                "id": "integrated_plan_requirements",
                "content": """
                County Integrated Plan (IP) Requirements for BHT Compliance

                PURPOSE:
                The Integrated Plan demonstrates county readiness and compliance with
                Behavioral Health Transformation requirements under AB 531, SB 326, and Proposition 1.

                SUBMISSION SCHEDULE:
                - Initial IP: Due 6 months before funding release
                - Annual Updates: Due January 31 each year
                - Major Revisions: Requires DHCS approval

                REQUIRED SECTIONS:

                1. EXECUTIVE SUMMARY (5-10 pages)
                   - County overview and demographics
                   - Behavioral health needs summary
                   - Transformation goals and objectives
                   - Funding request summary
                   - High-level timeline

                2. NEEDS ASSESSMENT (15-25 pages)
                   Required Data:
                   - Population demographics
                   - Homelessness statistics (PIT count)
                   - Justice-involved population data
                   - Current behavioral health service utilization
                   - Crisis call volume (988 data)
                   - Emergency department behavioral health visits
                   - Psychiatric hospitalization rates
                   - Substance use treatment needs

                   Service Gap Analysis:
                   - Crisis services capacity vs need
                   - Treatment bed availability
                   - Geographic access barriers
                   - Linguistic/cultural barriers
                   - Workforce shortages
                   - Wait times for services

                3. CRISIS SERVICES PLAN (20-30 pages)

                   a) 988 Crisis Hotline:
                      - Current capacity (calls per day)
                      - Staffing plan
                      - Language access plan
                      - Call answer rate metrics
                      - Quality assurance procedures

                   b) Mobile Crisis Teams:
                      - Number of teams (minimum 1 per 100K population)
                      - Geographic coverage areas
                      - Team composition and staffing
                      - Response time targets and current performance
                      - Dispatch protocols
                      - Law enforcement coordination
                      - Equipment and vehicles

                   c) Crisis Stabilization Units:
                      - Current beds vs required beds
                      - New facility plans (if needed)
                      - Locations (accessibility analysis)
                      - Staffing model
                      - Admission criteria and protocols
                      - Average length of stay
                      - Discharge planning processes

                   d) Crisis Residential Services:
                      - Capacity (beds)
                      - Admission criteria
                      - Length of stay protocols
                      - Integration with other services

                4. INFRASTRUCTURE PLAN (25-40 pages)

                   For Each Proposed Project:
                   - Project description and justification
                   - Location and site plan
                   - Capacity (beds or clients served)
                   - Construction timeline with milestones
                   - Budget (itemized)
                   - Funding sources (Prop 1, SB 326, local match)
                   - Environmental review status
                   - Community engagement summary
                   - Workforce impact (jobs created)
                   - Expected outcomes and metrics

                   Required Milestones:
                   - Site acquisition: Quarter and year
                   - Design completion: Quarter and year
                   - Construction start: Quarter and year
                   - Construction completion: Quarter and year
                   - Licensing and certification: Quarter and year
                   - Service launch: Quarter and year

                   Must include:
                   - Gantt charts or timeline graphics
                   - Risk mitigation plans
                   - Contingency budgets (10% minimum)

                5. HOUSING SERVICES (10-20 pages)

                   Required:
                   - Current supportive housing units
                   - Additional units needed (based on needs assessment)
                   - New construction or acquisition plans
                   - Service integration model
                   - Partnership with housing authorities/developers
                   - Tenant eligibility and prioritization
                   - Long-term operating plan (20+ years)
                   - Funding sustainability model

                6. WORKFORCE DEVELOPMENT (10-15 pages)

                   Required Elements:
                   - Current workforce inventory
                   - Projected staffing needs (by role and FTE)
                   - Recruitment strategies
                   - Training and competency development
                   - Peer workforce expansion plan
                   - Bilingual staff recruitment
                   - Retention strategies and incentives
                   - Pipeline development (partnerships with universities, etc.)
                   - Cultural competency training plan

                7. DATA AND ACCOUNTABILITY (10-15 pages)

                   Required:
                   - Data infrastructure (EHR systems, data warehouses)
                   - Reporting capabilities
                   - Quality metrics and targets
                   - Outcome measures
                   - Disparities tracking and reduction plan
                   - Data sharing agreements (county agencies)
                   - Privacy and security compliance
                   - Continuous quality improvement processes

                8. COMMUNITY ENGAGEMENT (5-10 pages)

                   Required:
                   - Stakeholder consultation process
                   - Community input summary
                   - Lived experience involvement
                   - Tribal consultation (if applicable)
                   - Public comment period results
                   - Advisory board or committee structure
                   - Ongoing engagement plan

                9. BUDGET JUSTIFICATION (15-25 pages)

                   Required Budget Tables:
                   - Capital costs (construction, renovation, equipment)
                   - Operating costs (personnel, services, overhead)
                   - Revenue sources (state, federal, county, other)
                   - Multi-year budget (minimum 3 years)
                   - Cost per outcome (e.g., cost per bed, cost per crisis response)
                   - Local match documentation
                   - Sustainability plan (post-grant funding)

                   Narrative:
                   - Budget assumptions and methodology
                   - Cost-effectiveness analysis
                   - Comparison to current costs
                   - Return on investment projections

                10. IMPLEMENTATION TIMELINE (5-10 pages)

                    3-Year Implementation Plan:
                    - Year 1 milestones and deliverables
                    - Year 2 milestones and deliverables
                    - Year 3 milestones and deliverables
                    - Critical path analysis
                    - Dependencies and sequencing
                    - Quarterly progress reporting plan

                COMPLIANCE CHECKLIST:
                Counties must meet ALL of the following:

                [] 24/7 crisis hotline (988) operational
                [] Mobile crisis teams (minimum ratio met)
                [] Crisis stabilization capacity plan (even if not yet built)
                [] Data reporting infrastructure
                [] Workforce development plan
                [] Housing services integration
                [] Community engagement documented
                [] Budget fully justified with local match
                [] 3-year timeline with quarterly milestones
                [] Disparities reduction targets
                [] Tribal consultation (if Native population present)

                NON-COMPLIANCE CONSEQUENCES:
                - Year 1: Technical assistance provided
                - Year 2: Funding withheld (up to 25%)
                - Year 3: Funding withheld (up to 50%)
                - Year 4+: Full funding loss, state intervention

                REVIEW PROCESS:
                - County submission: 6 months before funding needed
                - DHCS completeness review: 2 weeks
                - Technical review: 4-6 weeks
                - Community input period: 2 weeks
                - Conditional approval or deficiency letter: Week 10
                - County revisions: 4 weeks
                - Final approval: Week 16

                APPROVAL CRITERIA:
                - Meets all minimum requirements: Pass/Fail
                - Budget is reasonable and justified: Pass/Fail
                - Timeline is realistic: Pass/Fail
                - Likely to achieve outcomes: Scored 1-5
                - Community support: Scored 1-5
                - Innovation and best practices: Scored 1-5

                Minimum score for approval: Pass all Pass/Fail + Average 3.0 or higher on scored sections
                """,
                "metadata": {
                    "source": "DHCS Integrated Plan Guidance",
                    "section": "IP Requirements and Compliance",
                    "version": "2024.1",
                    "category": "compliance",
                    "use_case": "IP Compliance, Policy Q&A"
                }
            }
        ]

    @staticmethod
    def _generate_bhoatr_docs() -> List[Dict]:
        """BHOATR reporting requirements"""
        return [
            {
                "id": "bhoatr_reporting_requirements",
                "content": """
                Behavioral Health Outcomes, Accountability, and Transparency Reporting (BHOATR)

                PURPOSE:
                BHOATR provides standardized, public reporting of behavioral health system
                performance, outcomes, and accountability to ensure transparency and drive
                continuous improvement.

                REPORTING SCHEDULE:
                - Quarterly Reports: Due 30 days after quarter end
                - Annual Reports: Due 90 days after fiscal year end
                - Ad-hoc Reports: As requested by DHCS

                REQUIRED METRICS BY CATEGORY:

                1. ACCESS METRICS

                   Crisis Services Access:
                   - 988 call volume (total calls)
                   - 988 call answer rate (%)
                   - Average speed of answer (seconds)
                   - Call abandonment rate (%)
                   - Calls by language
                   - Calls by county
                   - Calls by time of day
                   - Average call duration (minutes)

                   Mobile Crisis Access:
                   - Dispatch requests (total)
                   - Dispatches completed (%)
                   - Average response time (minutes)
                   - Response time by urban/rural
                   - Geographic coverage (% of county served within target times)

                   Crisis Stabilization Access:
                   - Admission requests (total)
                   - Admissions completed (%)
                   - Average wait time for admission (hours)
                   - Occupancy rate (%)
                   - Diversions due to capacity (count)
                   - Average length of stay (days)

                2. CLINICAL OUTCOME METRICS

                   Short-term Outcomes (30 days post-crisis):
                   - Community stabilization rate (%)
                   - Psychiatric hospitalization rate (%)
                   - Emergency department visits (count per 100 clients)
                   - Follow-up appointment attendance (%)
                   - Return to crisis services (%)
                   - Mortality (suicide deaths)

                   Medium-term Outcomes (90 days post-crisis):
                   - Engagement in ongoing treatment (%)
                   - Housing stability (%)
                   - Criminal justice involvement (new arrests/incarcerations)
                   - Substance use treatment engagement (%)
                   - Repeated psychiatric hospitalizations (%)

                   Long-term Outcomes (12 months post-crisis):
                   - Recovery outcomes (using standardized scales)
                   - Employment/education status
                   - Housing status (permanent housing %)
                   - Social connectedness measures
                   - Quality of life scores

                3. QUALITY METRICS

                   Clinical Quality:
                   - Risk assessment completion rate (%)
                   - Safety plan completion rate (%)
                   - Medication reconciliation rate (%)
                   - Discharge planning completion rate (%)
                   - Evidence-based practice utilization (%)

                   Service Quality:
                   - Client satisfaction scores (average and distribution)
                   - Family satisfaction scores
                   - Complaint rate (per 1000 services)
                   - Adverse events (restraints, seclusion, injuries)
                   - Staff satisfaction scores

                   System Quality:
                   - Service coordination (warm handoffs %)
                   - Information sharing (releases signed %)
                   - Continuity of care (gaps in care episodes)
                   - Cultural competency (language concordance %)

                4. EQUITY METRICS

                   Demographic Service Utilization:
                   - By race/ethnicity
                   - By primary language
                   - By age group
                   - By gender identity
                   - By sexual orientation
                   - By geographic region (urban/rural)
                   - By insurance status

                   Equity in Outcomes:
                   - Clinical outcomes by demographic group
                   - Service access by demographic group
                   - Quality measures by demographic group
                   - Disparity ratios (comparing outcomes across groups)
                   - Disparities reduction progress (trend over time)

                5. WORKFORCE METRICS

                   Staffing:
                   - Total FTEs by role (clinicians, peers, support staff)
                   - Vacancy rates (%)
                   - Time to hire (days)
                   - Staff turnover rate (%)
                   - Staff diversity (demographics)
                   - Bilingual staff (% by language)

                   Training and Development:
                   - Staff training hours (average per FTE)
                   - Crisis intervention certification (% of staff)
                   - Cultural competency training (% of staff)
                   - Peer specialist certification (count)

                6. FINANCIAL METRICS

                   Utilization:
                   - Total crisis events (count)
                   - Services delivered (units)
                   - Cost per crisis event ($)
                   - Cost per admission day ($)
                   - Cost per mobile crisis response ($)

                   Efficiency:
                   - Administrative overhead (% of total budget)
                   - Staff productivity (clients per FTE)
                   - Facility utilization (bed days used vs available)
                   - No-show rate (%)

                   Value:
                   - Emergency department diversions (count and estimated savings)
                   - Psychiatric hospitalization days avoided (count and savings)
                   - Return on investment calculations
                   - Cost-effectiveness ratios

                7. INFRASTRUCTURE PROGRESS

                   For Construction Projects:
                   - Projects in planning phase (count)
                   - Projects in construction (count)
                   - Projects completed (count)
                   - Budget spent vs allocated (%)
                   - Timeline status (on-time, delayed, ahead)
                   - Beds added (count)
                   - Capacity increase (% vs baseline)

                DATA QUALITY REQUIREMENTS:
                - Completeness: >95% of required fields populated
                - Accuracy: Random audit error rate <5%
                - Timeliness: Submitted within 30 days of quarter end
                - Consistency: Year-over-year methodology consistent

                REPORTING FORMAT:
                - Standardized Excel templates (provided by DHCS)
                - Narrative report (max 20 pages)
                - Data visualizations (charts, graphs)
                - Executive summary (2 pages)
                - Action plans for areas needing improvement

                PUBLIC TRANSPARENCY:
                - County reports published on DHCS website
                - Statewide dashboard with county comparisons
                - Annual public report to legislature
                - Community presentations required

                CONSEQUENCES OF NON-REPORTING:
                - 30 days late: Warning letter
                - 60 days late: 10% funding withhold
                - 90 days late: 25% funding withhold
                - Persistent non-compliance: Technical assistance, potential state oversight
                """,
                "metadata": {
                    "source": "DHCS BHOATR Reporting Manual",
                    "section": "Reporting Requirements and Standards",
                    "version": "2024.1",
                    "category": "reporting",
                    "use_case": "BHOATR Reporting, Policy Q&A"
                }
            }
        ]

    @staticmethod
    def _generate_infrastructure_docs() -> List[Dict]:
        """Infrastructure development standards"""
        return [
            {
                "id": "infrastructure_project_management",
                "content": """
                Infrastructure Project Management Standards for BHT Projects

                PROJECT LIFECYCLE:

                PHASE 1: PLANNING (Months 1-6)

                Needs Assessment:
                - Service gap analysis
                - Population projections
                - Geographic access analysis
                - Competitive landscape review

                Site Selection:
                - Zoning compliance verification
                - Environmental review (CEQA)
                - Community engagement and input
                - Accessibility assessment (transit, parking)
                - Utility capacity review
                - Site acquisition or lease negotiation

                Program Design:
                - Service model definition
                - Staffing model development
                - Operational policies and procedures
                - Technology requirements
                - Partnership agreements

                Financial Planning:
                - Capital budget development
                - Operating pro forma (5 years)
                - Funding source identification
                - Local match commitment
                - Sustainability analysis

                Deliverables:
                - Needs assessment report
                - Site selection justification
                - Program design document
                - Financial feasibility study
                - Community engagement summary

                PHASE 2: DESIGN (Months 7-12)

                Architectural Design:
                - Schematic design (30% plans)
                - Design development (60% plans)
                - Construction documents (100% plans)
                - DHCS licensing review and approval
                - Permit applications

                Design Requirements:
                - Compliance with DHCS licensing standards
                - ADA accessibility
                - California Building Code
                - Energy efficiency (Title 24)
                - Seismic standards (current code)
                - Sustainable design (LEED optional but encouraged)

                Bid Process:
                - General contractor RFP
                - Bid evaluation
                - Contractor selection
                - Contract negotiation

                Deliverables:
                - Approved construction plans
                - Building permits
                - Contractor agreement
                - Construction schedule

                PHASE 3: CONSTRUCTION (Months 13-24)

                Construction Management:
                - Weekly site meetings
                - Progress inspections
                - Change order management
                - Quality control
                - Safety compliance
                - Schedule tracking

                Key Milestones:
                - Groundbreaking
                - Foundation completion
                - Framing completion
                - Substantial completion
                - Final inspection
                - Certificate of occupancy

                Reporting:
                - Monthly progress reports to DHCS
                - Budget status (spent vs allocated)
                - Timeline status (on schedule, delayed, ahead)
                - Issue log and resolution
                - Photos and documentation

                PHASE 4: LICENSING & ACTIVATION (Months 25-30)

                Licensing Process:
                - DHCS license application
                - Site inspection
                - Deficiency correction
                - Conditional license issuance

                Operational Readiness:
                - Staff recruitment and hiring
                - Staff training (minimum 40 hours)
                - Policies and procedures finalized
                - EHR system implementation
                - Furnishing and equipment installation
                - Vendor contracts (food, laundry, medical supplies)
                - Emergency drills and procedures testing

                Soft Opening:
                - Limited capacity operations (50% beds)
                - Quality assurance monitoring
                - Staff adjustment period
                - Process refinement

                Full Operations Launch:
                - Full capacity
                - Full license application
                - Community outreach and referral source notification
                - Grand opening event

                PROJECT MONITORING AND REPORTING:

                Required Monthly Reports to DHCS:
                - Budget status
                  - Total budget vs spent
                  - Current month expenditures
                  - Projected completion cost
                  - Variance explanations

                - Schedule status
                  - Key milestones completion
                  - Percent complete overall
                  - Projected completion date
                  - Delays and mitigation plans

                - Quality and compliance
                  - Inspections completed
                  - Issues identified and resolved
                  - Safety incidents
                  - Change orders (description and cost impact)

                - Photos and progress documentation

                Risk Management:

                Common Risks and Mitigation:
                - Permitting delays
                  Mitigation: Early engagement, expedited review requests

                - Construction cost overruns
                  Mitigation: 10% contingency budget, value engineering

                - Labor shortages
                  Mitigation: Early contractor engagement, flexible scheduling

                - Community opposition
                  Mitigation: Early engagement, address concerns, benefits communication

                - Supply chain disruptions
                  Mitigation: Early material ordering, alternative suppliers

                - Scope creep
                  Mitigation: Clear change order process, budget discipline

                SUCCESS METRICS:
                - On-time completion (within 10% of baseline timeline)
                - On-budget completion (within 10% of baseline budget)
                - Successful licensing (full license within 6 months of opening)
                - Service volume (75% of projected utilization within 12 months)
                - Quality outcomes (meet DHCS standards within 12 months)

                PROJECT FAILURE CRITERIA:
                - More than 6 months behind schedule (without approved extension)
                - More than 25% over budget (without additional funding approval)
                - Unable to obtain licensing within 12 months of construction completion
                - Failure to launch services within 18 months of construction completion

                DHCS INTERVENTION:
                DHCS may intervene with technical assistance, project management support,
                or funding reallocation if projects fail to meet milestones or performance standards.
                """,
                "metadata": {
                    "source": "DHCS Infrastructure Development Guide",
                    "section": "Project Management Standards",
                    "version": "2024.1",
                    "category": "infrastructure",
                    "use_case": "Infrastructure Tracking, Policy Q&A"
                }
            }
        ]

    @staticmethod
    def _generate_population_docs() -> List[Dict]:
        """Target population-specific guidelines"""
        return [
            {
                "id": "justice_involved_population",
                "content": """
                Services for Justice-Involved Individuals with Behavioral Health Needs

                PRIORITY POPULATION DEFINITION:
                Justice-involved individuals include:
                - Currently incarcerated with mental illness or substance use disorder
                - Recently released from jail or prison (past 12 months)
                - On probation or parole with behavioral health conditions
                - Frequent criminal justice system contact related to untreated mental illness

                ESTIMATED POPULATION SIZE (California):
                - County jails: ~70,000 individuals (65% with behavioral health needs)
                - State prisons: ~95,000 individuals (35% with serious mental illness)
                - Probation: ~250,000 individuals (40% with behavioral health needs)
                - Parole: ~45,000 individuals (50% with behavioral health needs)

                KEY CHALLENGES:
                - Criminalization of mental illness (arrests for behaviors related to symptoms)
                - Treatment interruption during incarceration
                - Limited discharge planning and community connection
                - High crisis rates immediately post-release (67% within 30 days)
                - Poor treatment engagement (only 23% attend first follow-up)
                - Co-occurring substance use disorders (85% prevalence)
                - Housing instability (45% homeless post-release)

                EVIDENCE-BASED INTERVENTIONS:

                1. Pre-Release Planning:
                   - In-reach services while incarcerated
                   - Medication continuity planning
                   - Appointment scheduling before release
                   - Housing placement coordination
                   - Benefits enrollment/re-enrollment (Medi-Cal, SSI)

                2. Transition Services (0-30 days post-release):
                   - Intensive case management (weekly contact minimum)
                   - Immediate access to crisis services
                   - Medication supply and prescriptions
                   - Peer support (someone with lived experience)
                   - Housing support (emergency, transitional, permanent)
                   - Basic needs assistance (food, clothing, transportation)

                3. Specialized Treatment Programs:
                   - Mental Health Treatment Court programs
                   - Co-occurring disorders treatment (integrated model)
                   - Trauma-informed care (high rates of trauma history)
                   - Forensic Assertive Community Treatment (FACT teams)
                   - Supported employment

                4. Crisis Intervention Training for Justice Partners:
                   - Law enforcement: Crisis Intervention Training (CIT)
                   - Correctional officers: Mental health first aid
                   - Probation/parole officers: Behavioral health awareness
                   - Court personnel: Trauma-informed practices

                BHT REQUIREMENTS FOR JUSTICE-INVOLVED SERVICES:

                County Integrated Plans Must Include:
                - Data sharing agreements with criminal justice agencies
                - In-reach services to county jails
                - Post-release intensive case management program
                - Crisis services coordination with law enforcement
                - Forensic-specific treatment capacity
                - Recidivism reduction targets and measurement

                Staffing Requirements:
                - Forensic specialists (clinicians with criminal justice experience)
                - Peer support specialists with justice-involvement lived experience
                - Case managers with small caseloads (1:15 ratio max)
                - 24/7 crisis response for high-risk individuals

                Coordination Requirements:
                - Liaison with county jail mental health services
                - Collaboration with probation and parole
                - Partnership with public defender and assigned counsel
                - Connection with reentry programs
                - Housing authority coordination

                OUTCOME METRICS:
                Primary Outcomes:
                - Recidivism reduction (new arrests, incarcerations)
                - Treatment engagement (% attending appointments)
                - Housing stability (% in stable housing at 90 days)
                - Crisis service utilization reduction
                - Employment/education engagement

                Process Metrics:
                - Pre-release planning completion (% of eligible individuals)
                - Warm handoff at release (% receiving immediate services)
                - Crisis contact within 72 hours post-release
                - Medication continuity (no gaps)
                - Follow-up attendance at 7, 30, 90 days

                FUNDING AND SUSTAINABILITY:
                - Prop 1 capital for forensic treatment facilities
                - Criminal justice grants (federal and state)
                - Medi-Cal reimbursement for services
                - County behavioral health and criminal justice budgets
                - Recidivism reduction savings (reinvestment)

                BEST PRACTICE EXAMPLES:
                - Los Angeles County: Office of Diversion and Reentry (ODR)
                - San Francisco: Forensic Intensive Case Management Services (FICMS)
                - Alameda County: Behavioral Health Court Liaison program
                - San Diego: Serial Inebriate Program (SIP) with treatment focus
                """,
                "metadata": {
                    "source": "DHCS Justice-Involved Population Guidelines",
                    "section": "Services and Requirements",
                    "version": "2024.1",
                    "category": "populations",
                    "use_case": "Population Analytics, Policy Q&A"
                }
            },
            {
                "id": "homeless_population_services",
                "content": """
                Services for Individuals Experiencing Homelessness with Behavioral Health Needs

                PRIORITY POPULATION DEFINITION:
                - Chronically homeless (12+ months or 4+ episodes) with serious mental illness
                - Currently homeless with untreated behavioral health conditions
                - At imminent risk of homelessness due to behavioral health crisis
                - Living in places not meant for human habitation
                - Emergency shelters, transitional housing residents with behavioral health needs

                POPULATION SIZE (California 2024):
                - Total homeless population: ~181,000 individuals
                - With serious mental illness: ~67,000 (37%)
                - With substance use disorders: ~90,000 (50%)
                - Unsheltered: ~123,000 (68%)

                KEY CHALLENGES:
                - Difficulty engaging in traditional clinic-based services
                - High crisis utilization (emergency services)
                - Complex co-occurring needs (medical, behavioral, social)
                - Lack of safe place to stabilize
                - Medication non-adherence (storage, stability issues)
                - High mortality rate (3x general population)

                EVIDENCE-BASED INTERVENTIONS:

                1. Street Outreach and Engagement:
                   - Mobile behavioral health teams
                   - Peer outreach workers
                   - Harm reduction approach
                   - Relationship building over time
                   - Meeting basic needs first (food, clothing, medical)
                   - Low-barrier engagement (no prerequisites)

                2. Housing First with Services:
                   - Permanent supportive housing (gold standard)
                   - No sobriety or treatment requirements for housing
                   - Intensive case management (1:15 ratio)
                   - Integrated behavioral health services
                   - Medication management
                   - Life skills and independent living support

                3. Interim Stabilization:
                   - Crisis respite programs (safe place to stabilize)
                   - Recuperative care (medical respite)
                   - Sobering centers (substance use focus)
                   - Bridge housing with services

                4. Specialized Treatment:
                   - Co-occurring disorders treatment (integrated)
                   - Trauma-informed care (high rates of trauma)
                   - Medication-assisted treatment for opioid use
                   - Primary care integration (high medical needs)

                BHT REQUIREMENTS FOR HOMELESS SERVICES:

                County Integrated Plans Must Address:
                - Street outreach behavioral health services
                - Low-barrier crisis services (no ID, insurance required)
                - Permanent supportive housing capacity (units needed)
                - Interim stabilization options
                - Data integration with homeless services system (HMIS)
                - Coordinated entry system participation

                Crisis Services Modifications for Homeless Population:
                - Mobile response prioritized over phone-based
                - Flexible locations (meet people where they are)
                - Extended engagement time (not rushed)
                - Connection to housing resources
                - Basic needs support
                - Harm reduction approach

                Permanent Supportive Housing Requirements:
                - Minimum 1 unit per 500 individuals experiencing chronic homelessness
                - On-site or closely integrated behavioral health services
                - 24/7 crisis support access
                - Low barrier (no sobriety requirement)
                - Housing retention support
                - Medication storage and management assistance

                STAFFING FOR HOMELESS SERVICES:
                - Outreach workers (with lived experience preferred)
                - Licensed clinicians (LCSW, LMFT, LPCC)
                - Psychiatric prescribers (psychiatrists or NPs)
                - Substance use disorder counselors
                - Case managers (housing-focused)
                - Peer support specialists
                - Medical providers or nurses (integrated care)

                OUTCOME METRICS:
                Primary Outcomes:
                - Housing stability (% in permanent housing at 12 months)
                - Treatment engagement (% in ongoing services)
                - Crisis utilization reduction
                - Emergency department visits reduction
                - Mortality reduction

                Process Metrics:
                - Outreach contacts (encounters)
                - Housing placements (move-ins)
                - Services linkage (% connected within 30 days)
                - Housing retention (% retained at 6, 12 months)
                - Medication adherence

                FUNDING STREAMS:
                - Proposition 1 (supportive housing construction)
                - Homeless Housing, Assistance and Prevention (HHAP) grants
                - Project Homekey (state program)
                - Medi-Cal (services reimbursement)
                - Mental Health Services Act (MHSA)
                - County behavioral health and homeless funds
                - Federal HUD funding (Continuum of Care)

                BEST PRACTICE MODELS:
                - Pathways Housing First (evidence-based model)
                - San Francisco: Flexible Housing Subsidy Pool
                - Los Angeles: Project Roomkey/Homekey
                - San Diego: Housing First - Housing Fast approach
                - Sacramento: Whole Person Care model
                """,
                "metadata": {
                    "source": "DHCS Homeless Population Guidelines",
                    "section": "Services and Requirements",
                    "version": "2024.1",
                    "category": "populations",
                    "use_case": "Population Analytics, Policy Q&A, IP Compliance"
                }
            }
        ]

    @staticmethod
    def _generate_budget_docs() -> List[Dict]:
        """Budget and resource allocation guidelines"""
        return [
            {
                "id": "resource_allocation_framework",
                "content": """
                Resource Allocation and Funding Optimization Framework

                PURPOSE:
                Guide counties in making data-driven funding allocation decisions to maximize
                impact of limited Behavioral Health Transformation resources.

                AVAILABLE FUNDING SOURCES:

                1. Proposition 1 Bond Funds ($6.38 billion):
                   - Crisis stabilization units
                   - Residential treatment facilities
                   - Supportive housing construction
                   - Mobile crisis infrastructure
                   - Workforce development

                2. SB 326 Bond Funds ($2.2 billion):
                   - Facility renovation and modernization
                   - Equipment and technology
                   - Capacity expansion projects

                3. AB 531 State General Fund ($500M annually):
                   - Crisis hotline operations
                   - Mobile crisis team operations
                   - Training and workforce development
                   - Data infrastructure

                4. Mental Health Services Act (MHSA):
                   - Prevention and early intervention
                   - Community services and supports
                   - Innovation projects
                   - Workforce education and training
                   - Capital facilities (limited)

                5. Medi-Cal:
                   - Reimbursement for covered services
                   - Enhanced case management
                   - Community health workers
                   - Crisis intervention services

                6. County General Funds:
                   - Local match requirements
                   - Services for uninsured
                   - Flexible funding for gaps

                ALLOCATION DECISION FRAMEWORK:

                STEP 1: Needs-Based Prioritization

                Data to Analyze:
                - Crisis call volume and trends
                - Emergency department behavioral health visits
                - Psychiatric hospitalization rates
                - Homelessness with mental illness (PIT count)
                - Justice involvement rates
                - Service capacity gaps (wait times, unmet demand)
                - Geographic access barriers
                - Demographic disparities in access/outcomes

                Prioritization Criteria:
                - Severity of need (life/death impact)
                - Size of affected population
                - Current service gap size
                - Feasibility of intervention
                - Potential for sustainable impact

                STEP 2: Cost-Effectiveness Analysis

                Calculate for Each Intervention Option:
                - Total cost (capital + operating, multi-year)
                - Number of individuals served annually
                - Cost per person served
                - Estimated outcomes (lives saved, stabilizations, housing placements)
                - Cost per outcome achieved
                - Return on investment (savings from prevented hospitalizations, incarcerations)

                Example Calculations:

                Mobile Crisis Team:
                - Annual cost: $850,000 (2 FTE clinicians, 2 FTE specialists, vehicle, overhead)
                - Individuals served: 600 per year
                - Cost per person: $1,417
                - Estimated ED diversions: 350 (58%)
                - ED visit cost avoided: $2,000 each = $700,000 savings
                - ROI: $700K savings / $850K cost = 82% (near break-even, plus non-monetary benefits)

                Crisis Stabilization Unit (20 beds):
                - Capital cost: $10 million (construction)
                - Annual operating cost: $1.8 million
                - Individuals served: 400 per year
                - Cost per admission: $4,500
                - Estimated hospital diversions: 300 (75%)
                - Hospital cost avoided: $15,000 per stay = $4.5M savings
                - ROI: $4.5M savings / $1.8M operating = 250% annual return
                - Capital payback: 2.2 years

                Permanent Supportive Housing (50 units):
                - Capital cost: $25 million ($500K per unit)
                - Annual operating cost: $1.2 million ($24K per unit)
                - Individuals served: 50 per year (high retention)
                - Crisis utilization reduction: 60% vs baseline
                - Hospitalization reduction: 40% vs baseline
                - Incarceration reduction: 75% vs baseline
                - Combined savings: $35,000 per person annually = $1.75M
                - ROI: $1.75M savings / $1.2M cost = 146% annual return
                - Capital payback: 4.5 years
                - Long-term value: Extremely high (housing stability enables recovery)

                STEP 3: Equity Impact Assessment

                Analyze how each funding option affects:
                - Racial/ethnic disparities in access
                - Geographic equity (urban vs rural)
                - Linguistic accessibility
                - LGBTQ+ population access
                - Justice-involved individuals
                - Homeless population

                Prioritize investments that:
                - Reduce existing disparities
                - Reach underserved populations
                - Remove barriers to access
                - Demonstrate cultural responsiveness

                STEP 4: Feasibility and Risk Assessment

                Consider for each option:
                - Implementation timeline (how soon impact achieved?)
                - Local capacity (workforce, partners, infrastructure)
                - Community support (opposition risks?)
                - Regulatory barriers (licensing, zoning, etc.)
                - Sustainability (operating funding secured?)
                - Scalability (can it grow if successful?)

                Risk Mitigation:
                - Start with pilots before large-scale investment
                - Build in contingency budgets (10-15%)
                - Secure operating funding before capital projects
                - Engage community early and often
                - Plan for workforce recruitment challenges

                STEP 5: Portfolio Approach

                Recommended Balanced Portfolio:
                - 40% Infrastructure (long-term capacity)
                - 35% Operations (immediate crisis response)
                - 15% Workforce (enable quality services)
                - 10% Innovation and flexibility (test new approaches)

                Balanced Across Service Levels:
                - 30% Prevention and early intervention
                - 40% Crisis response and stabilization
                - 30% Treatment and recovery support

                Geographic Distribution:
                - Proportional to population and need
                - Minimum investments in rural/underserved areas
                - Concentrate some services for efficiency (e.g., specialized programs)

                DECISION SUPPORT TOOLS:

                Cost-Benefit Matrix:
                - X-axis: Cost (low to high)
                - Y-axis: Impact (low to high)
                - Prioritize: High impact, low cost (quick wins)
                - Second priority: High impact, high cost (strategic investments)
                - Deprioritize: Low impact, high cost (avoid)

                Scenario Modeling:
                - Model 3-5 different allocation scenarios
                - Project outcomes for each at 1, 3, 5 years
                - Stress test assumptions (what if costs 20% higher?)
                - Compare scenarios against strategic goals

                Stakeholder Input:
                - Clinical experts (what works?)
                - People with lived experience (what do they need?)
                - Community members (what does community want?)
                - Administrators (what's feasible?)
                - Funders (what will they support?)

                ONGOING OPTIMIZATION:

                Quarterly Reviews:
                - Track actual performance vs projections
                - Identify underperforming investments
                - Identify overperforming investments (scale up?)
                - Adjust allocations based on data

                Annual Reallocation:
                - Redirect funds from ineffective programs
                - Invest more in proven successful programs
                - Sunset programs that have accomplished goals
                - Launch new initiatives based on emerging needs

                DHCS TECHNICAL ASSISTANCE:
                Counties can request DHCS help with:
                - Cost-benefit analysis
                - Data analysis and needs assessment
                - Scenario modeling
                - Peer county consultation
                - Best practice identification
                """,
                "metadata": {
                    "source": "DHCS Resource Allocation Guide",
                    "section": "Funding Optimization Framework",
                    "version": "2024.1",
                    "category": "budget",
                    "use_case": "Resource Allocation, Policy Q&A, IP Compliance"
                }
            }
        ]


def save_documents_to_json(output_path: str = "policy_documents.json"):
    """Generate and save all documents to JSON file"""
    generator = PolicyDocumentsGenerator()
    documents = generator.generate_all_documents()

    with open(output_path, 'w') as f:
        json.dump(documents, f, indent=2)

    print(f"Generated {len(documents)} policy documents")
    print(f"Saved to {output_path}")

    # Print summary
    categories = {}
    for doc in documents:
        cat = doc['metadata'].get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print("\nDocuments by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    return documents


if __name__ == "__main__":
    save_documents_to_json()
