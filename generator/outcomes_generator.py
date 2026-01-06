"""
BHOATR Outcomes Data Generator
Generates synthetic behavioral health outcome and accountability data
"""
import json
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

COUNTIES = [
    "Los Angeles", "San Diego", "Orange", "Riverside", "San Bernardino",
    "Santa Clara", "Alameda", "Sacramento", "Contra Costa", "Fresno",
    "Kern", "San Francisco", "Ventura", "San Mateo", "San Joaquin"
]

DEMOGRAPHICS = {
    "age_groups": ["13-17", "18-25", "26-35", "36-50", "51-64", "65+"],
    "race_ethnicity": ["White", "Hispanic/Latino", "Black/African American", "Asian", "Native American", "Pacific Islander", "Two or More Races"],
    "gender": ["Male", "Female", "Non-Binary", "Transgender", "Other"],
    "languages": ["English", "Spanish", "Chinese", "Vietnamese", "Tagalog", "Korean", "Armenian", "Other"],
}


class OutcomesGenerator:
    """Generate BHOATR outcomes data"""

    @staticmethod
    def generate_quarterly_report(county: str, year: int, quarter: int) -> dict:
        """Generate quarterly BHOATR report for a county"""

        # Base crisis event volume (scaled by county size)
        county_scale = {
            "Los Angeles": 4.0,
            "San Diego": 1.3,
            "Orange": 1.2,
            "Riverside": 0.9,
            "San Bernardino": 0.8,
            "Santa Clara": 0.7,
            "Alameda": 0.6,
            "Sacramento": 0.6,
            "Contra Costa": 0.5,
            "Fresno": 0.4
        }
        scale = county_scale.get(county, 0.3)
        base_events = int(3000 * scale)

        # Generate crisis metrics
        total_crisis_events = base_events + random.randint(-200, 200)
        call_answer_rate = random.uniform(92, 98)
        avg_speed_of_answer = random.randint(35, 65)
        abandonment_rate = random.uniform(2, 8)
        high_risk_events = int(total_crisis_events * random.uniform(0.12, 0.18))
        imminent_risk_events = int(total_crisis_events * random.uniform(0.03, 0.07))

        # Mobile crisis metrics
        mobile_dispatches = int(total_crisis_events * random.uniform(0.25, 0.35))
        avg_response_time = random.randint(35, 55)
        community_stabilization_rate = random.uniform(72, 85)

        # Crisis stabilization admissions
        csu_admissions = int(total_crisis_events * random.uniform(0.15, 0.25))
        avg_length_of_stay = random.uniform(5, 9)
        occupancy_rate = random.uniform(70, 92)

        # Clinical outcomes (30-day)
        successful_stabilizations = int(total_crisis_events * random.uniform(0.82, 0.91))
        psychiatric_hospitalizations = int(total_crisis_events * random.uniform(0.08, 0.15))
        ed_visits = int(total_crisis_events * random.uniform(0.12, 0.20))
        followup_attendance = random.uniform(65, 82)
        return_to_crisis = random.uniform(18, 28)

        # Demographic breakdown
        demographics = {}
        for category, values in DEMOGRAPHICS.items():
            distribution = {}
            remaining = 100.0
            for i, value in enumerate(values):
                if i == len(values) - 1:
                    distribution[value] = round(remaining, 1)
                else:
                    pct = random.uniform(5, remaining / (len(values) - i))
                    distribution[value] = round(pct, 1)
                    remaining -= pct
            demographics[category] = distribution

        # Quality metrics
        risk_assessment_completion = random.uniform(97, 100)
        safety_plan_completion = random.uniform(93, 100)
        client_satisfaction = random.uniform(78, 92)

        # Workforce metrics
        total_fte = int(base_events / random.randint(15, 25))
        vacancy_rate = random.uniform(8, 22)
        turnover_rate = random.uniform(12, 28)
        staff_satisfaction = random.uniform(68, 85)

        # Financial metrics
        cost_per_crisis_event = random.randint(450, 750)
        cost_per_mobile_response = random.randint(800, 1400)
        cost_per_csu_day = random.randint(350, 550)
        ed_diversions = int(mobile_dispatches * random.uniform(0.55, 0.72))
        ed_diversion_savings = ed_diversions * random.randint(1800, 2500)

        report = {
            "report_id": str(uuid.uuid4()),
            "county": county,
            "year": year,
            "quarter": quarter,
            "reporting_period": f"Q{quarter} {year}",
            "submission_date": datetime.now().strftime("%Y-%m-%d"),

            "access_metrics": {
                "crisis_hotline": {
                    "total_calls": total_crisis_events,
                    "call_answer_rate_pct": round(call_answer_rate, 1),
                    "avg_speed_of_answer_seconds": avg_speed_of_answer,
                    "abandonment_rate_pct": round(abandonment_rate, 1),
                    "avg_call_duration_minutes": random.randint(18, 32),
                    "calls_by_language": {
                        "English": int(total_crisis_events * random.uniform(0.65, 0.75)),
                        "Spanish": int(total_crisis_events * random.uniform(0.15, 0.25)),
                        "Other": int(total_crisis_events * random.uniform(0.05, 0.15))
                    }
                },
                "mobile_crisis": {
                    "total_dispatches": mobile_dispatches,
                    "dispatch_completion_rate_pct": random.uniform(92, 98),
                    "avg_response_time_minutes": avg_response_time,
                    "response_time_urban_minutes": avg_response_time - random.randint(5, 15),
                    "response_time_rural_minutes": avg_response_time + random.randint(10, 25),
                    "within_60min_urban_pct": random.uniform(85, 95),
                    "within_90min_rural_pct": random.uniform(78, 92)
                },
                "crisis_stabilization": {
                    "total_admissions": csu_admissions,
                    "admission_completion_rate_pct": random.uniform(88, 96),
                    "avg_wait_time_hours": random.uniform(2.5, 5.5),
                    "occupancy_rate_pct": round(occupancy_rate, 1),
                    "avg_length_of_stay_days": round(avg_length_of_stay, 1),
                    "capacity_diversions": int(csu_admissions * random.uniform(0.05, 0.12))
                }
            },

            "clinical_outcomes": {
                "30_day": {
                    "community_stabilization_pct": round((successful_stabilizations / total_crisis_events) * 100, 1),
                    "psychiatric_hospitalization_pct": round((psychiatric_hospitalizations / total_crisis_events) * 100, 1),
                    "ed_visits_per_100": round((ed_visits / total_crisis_events) * 100, 1),
                    "followup_attendance_pct": round(followup_attendance, 1),
                    "return_to_crisis_pct": round(return_to_crisis, 1),
                    "mortality_count": random.randint(0, 5)
                },
                "90_day": {
                    "treatment_engagement_pct": random.uniform(62, 78),
                    "housing_stability_pct": random.uniform(55, 72),
                    "new_arrests_per_100": random.uniform(8, 18),
                    "substance_treatment_engagement_pct": random.uniform(48, 68),
                    "repeated_hospitalization_pct": random.uniform(15, 28)
                },
                "12_month": {
                    "recovery_outcome_score": random.uniform(3.2, 4.5),  # Scale 1-5
                    "employment_education_pct": random.uniform(38, 58),
                    "permanent_housing_pct": random.uniform(62, 82),
                    "quality_of_life_score": random.uniform(3.5, 4.3)  # Scale 1-5
                }
            },

            "quality_metrics": {
                "clinical_quality": {
                    "risk_assessment_completion_pct": round(risk_assessment_completion, 1),
                    "safety_plan_completion_pct": round(safety_plan_completion, 1),
                    "medication_reconciliation_pct": random.uniform(88, 97),
                    "discharge_planning_completion_pct": random.uniform(92, 99),
                    "evidence_based_practice_utilization_pct": random.uniform(78, 92)
                },
                "service_quality": {
                    "client_satisfaction_score": round(client_satisfaction, 1),
                    "family_satisfaction_score": random.uniform(75, 88),
                    "complaint_rate_per_1000": random.uniform(2, 8),
                    "adverse_events_count": random.randint(1, 8),
                    "staff_satisfaction_score": round(staff_satisfaction, 1)
                },
                "system_quality": {
                    "warm_handoff_pct": random.uniform(82, 94),
                    "information_sharing_pct": random.uniform(75, 90),
                    "continuity_of_care_gaps_pct": random.uniform(8, 18),
                    "language_concordance_pct": random.uniform(72, 88)
                }
            },

            "equity_metrics": {
                "demographics": demographics,
                "disparity_ratios": {
                    "access_disparity_index": random.uniform(0.85, 1.15),  # 1.0 = no disparity
                    "outcome_disparity_index": random.uniform(0.88, 1.12),
                    "quality_disparity_index": random.uniform(0.90, 1.10)
                },
                "disparity_notes": [
                    "Spanish language services expanded this quarter",
                    "Rural access gaps identified in northeast region",
                    "Youth services utilization below target"
                ]
            },

            "workforce_metrics": {
                "staffing": {
                    "total_fte": total_fte,
                    "clinicians": int(total_fte * random.uniform(0.35, 0.45)),
                    "peer_specialists": int(total_fte * random.uniform(0.10, 0.15)),
                    "support_staff": int(total_fte * random.uniform(0.40, 0.50)),
                    "vacancy_rate_pct": round(vacancy_rate, 1),
                    "time_to_hire_days": random.randint(45, 85),
                    "turnover_rate_pct": round(turnover_rate, 1)
                },
                "diversity": {
                    "staff_race_ethnicity": {
                        "White": random.uniform(40, 60),
                        "Hispanic/Latino": random.uniform(20, 35),
                        "Black/African American": random.uniform(8, 15),
                        "Asian": random.uniform(8, 15),
                        "Other": random.uniform(3, 8)
                    },
                    "bilingual_staff_pct": random.uniform(25, 45)
                },
                "training": {
                    "avg_training_hours_per_fte": random.uniform(15, 35),
                    "crisis_certification_pct": random.uniform(85, 98),
                    "cultural_competency_training_pct": random.uniform(90, 100),
                    "peer_specialist_certification_count": int(total_fte * random.uniform(0.10, 0.15))
                }
            },

            "financial_metrics": {
                "utilization": {
                    "total_crisis_events": total_crisis_events,
                    "cost_per_crisis_event": cost_per_crisis_event,
                    "cost_per_mobile_response": cost_per_mobile_response,
                    "cost_per_csu_day": cost_per_csu_day,
                    "total_expenditure": total_crisis_events * cost_per_crisis_event
                },
                "efficiency": {
                    "administrative_overhead_pct": random.uniform(12, 22),
                    "clients_per_fte": round(total_crisis_events / total_fte, 1),
                    "bed_utilization_pct": round(occupancy_rate, 1),
                    "no_show_rate_pct": random.uniform(12, 22)
                },
                "value": {
                    "ed_diversions_count": ed_diversions,
                    "ed_diversion_savings": ed_diversion_savings,
                    "hospital_days_avoided": random.randint(800, 2000),
                    "hospital_savings": random.randint(800000, 2000000),
                    "roi_ratio": random.uniform(1.4, 2.2)
                }
            },

            "narrative_highlights": [
                f"Total crisis events increased {random.randint(3, 12)}% compared to Q{quarter-1 if quarter > 1 else 4}",
                f"Mobile crisis response times improved by {random.randint(5, 15)}%",
                f"Client satisfaction scores reached {round(client_satisfaction, 1)}%, exceeding target",
                f"Workforce vacancy rate remains challenge at {round(vacancy_rate, 1)}%"
            ],

            "areas_for_improvement": [
                "Weekend crisis response times 20% higher than weekdays",
                f"Spanish language services need expansion (only {random.randint(70, 85)}% of demand met)",
                "Youth transition-age services underutilized",
                "Staff turnover in rural areas above county average"
            ],

            "action_plans": [
                {
                    "issue": "Weekend staffing gaps",
                    "action": "Hire 3 additional weekend crisis counselors",
                    "timeline": "Next quarter",
                    "budget": "$180,000 annually"
                },
                {
                    "issue": "Spanish language access",
                    "action": "Recruit 2 bilingual clinicians, expand interpreter pool",
                    "timeline": "6 months",
                    "budget": "$150,000"
                }
            ]
        }

        return report

    @staticmethod
    def generate_reports(count_per_county: int = 4) -> list:
        """Generate quarterly reports for multiple counties"""
        reports = []
        year = 2024
        quarters = [1, 2, 3, 4]

        for county in COUNTIES[:10]:  # Top 10 counties
            for quarter in quarters[:count_per_county]:
                reports.append(OutcomesGenerator.generate_quarterly_report(county, year, quarter))

        return reports

    @staticmethod
    def save_to_json(reports: list, output_path: str = "outcomes_data.json"):
        """Save reports to JSON"""
        with open(output_path, 'w') as f:
            json.dump(reports, f, indent=2)
        print(f"Generated {len(reports)} BHOATR quarterly reports")
        print(f"Saved to {output_path}")

        # Print summary
        total_events = sum(r['access_metrics']['crisis_hotline']['total_calls'] for r in reports)
        total_counties = len(set(r['county'] for r in reports))
        avg_satisfaction = sum(r['quality_metrics']['service_quality']['client_satisfaction_score'] for r in reports) / len(reports)

        print(f"\nTotal counties: {total_counties}")
        print(f"Total crisis events across all reports: {total_events:,}")
        print(f"Average client satisfaction: {avg_satisfaction:.1f}%")


if __name__ == "__main__":
    reports = OutcomesGenerator.generate_reports(count_per_county=4)
    OutcomesGenerator.save_to_json(reports)
