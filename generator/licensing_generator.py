"""
Licensing and Facility Data Generator
Generates synthetic facility licensing applications and status data
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

FACILITY_TYPES = [
    "Crisis Stabilization Unit",
    "Residential Treatment Facility",
    "Crisis Residential Program",
    "Partial Hospitalization Program",
    "Intensive Outpatient Program",
    "Mental Health Clinic",
    "Psychiatric Health Facility"
]

LICENSE_STATUSES = [
    "Pre-Application",
    "Application Submitted",
    "Under Review",
    "Deficiencies Identified",
    "Inspection Scheduled",
    "Inspection Complete",
    "Conditional License Issued",
    "Full License Issued",
    "Renewal Pending"
]

DEFICIENCY_TYPES = [
    "Incomplete floor plans",
    "Insufficient staffing plan",
    "Missing emergency protocols",
    "Inadequate medication storage design",
    "ADA compliance issues",
    "Fire safety violations",
    "Missing staff credentials",
    "Incomplete financial documentation",
    "Unclear admission criteria",
    "Missing quality improvement plan"
]


class LicensingGenerator:
    """Generate licensing application data"""

    @staticmethod
    def generate_application() -> dict:
        """Generate a single licensing application"""
        facility_type = random.choice(FACILITY_TYPES)
        county = random.choice(COUNTIES)
        status = random.choice(LICENSE_STATUSES)

        # Generate capacity
        if "Clinic" in facility_type or "IOP" in facility_type or "PHP" in facility_type:
            capacity = random.randint(20, 60)
            capacity_unit = "clients"
        else:
            capacity = random.randint(8, 50)
            capacity_unit = "beds"

        # Generate dates
        submission_date = datetime.now() - timedelta(days=random.randint(1, 365))

        # Estimated timeline based on status and facility type
        base_timeline = {
            "Crisis Stabilization Unit": 20,
            "Residential Treatment Facility": 26,
            "Crisis Residential Program": 16,
            "Partial Hospitalization Program": 14,
            "Intensive Outpatient Program": 12,
            "Mental Health Clinic": 10,
            "Psychiatric Health Facility": 24
        }

        timeline_weeks = base_timeline.get(facility_type, 16)
        expected_completion = submission_date + timedelta(weeks=timeline_weeks)

        # Status-based progress
        status_progress = {
            "Pre-Application": 5,
            "Application Submitted": 15,
            "Under Review": 35,
            "Deficiencies Identified": 50,
            "Inspection Scheduled": 70,
            "Inspection Complete": 85,
            "Conditional License Issued": 95,
            "Full License Issued": 100,
            "Renewal Pending": 100
        }

        progress = status_progress.get(status, 50)

        # Deficiencies
        deficiencies = []
        if status in ["Deficiencies Identified", "Under Review"]:
            deficiencies = random.sample(DEFICIENCY_TYPES, k=random.randint(2, 5))

        # Staffing plan
        staffing = {
            "administrator": 1,
            "medical_director": 1 if "Psychiatric" in facility_type or "Crisis Stabilization" in facility_type else 0,
            "psychiatrists": random.randint(1, 3) if capacity_unit == "beds" else random.randint(0, 1),
            "psychiatric_nps": random.randint(1, 3),
            "licensed_clinicians": random.randint(2, 8),
            "nurses": random.randint(2, 10) if capacity_unit == "beds" else random.randint(0, 2),
            "psychiatric_technicians": random.randint(3, 12) if capacity_unit == "beds" else 0,
            "peer_specialists": random.randint(1, 4),
            "support_staff": random.randint(2, 8)
        }

        total_staff = sum(staffing.values())

        # Budget estimates
        if capacity_unit == "beds":
            construction_budget = capacity * random.randint(400000, 650000)
            annual_operating = capacity * random.randint(75000, 125000)
        else:
            construction_budget = random.randint(500000, 2000000)
            annual_operating = random.randint(300000, 1200000)

        application = {
            "application_id": str(uuid.uuid4()),
            "facility_name": f"{fake.company()} {facility_type}",
            "facility_type": facility_type,
            "applicant_name": fake.name(),
            "applicant_organization": fake.company(),
            "applicant_email": fake.email(),
            "applicant_phone": fake.phone_number(),

            "county": county,
            "address": fake.street_address(),
            "city": county,  # Simplified
            "zip_code": fake.zipcode(),

            "capacity": capacity,
            "capacity_unit": capacity_unit,

            "license_status": status,
            "progress_percentage": progress,
            "submission_date": submission_date.strftime("%Y-%m-%d"),
            "expected_completion_date": expected_completion.strftime("%Y-%m-%d"),
            "estimated_timeline_weeks": timeline_weeks,

            "staffing_plan": staffing,
            "total_staff": total_staff,
            "staff_to_capacity_ratio": round(total_staff / capacity, 2),

            "construction_budget": construction_budget if status == "Pre-Application" else None,
            "annual_operating_budget": annual_operating,
            "funding_sources": random.sample([
                "Proposition 1", "SB 326", "County Funds",
                "Private Investment", "MHSA", "Philanthropy"
            ], k=random.randint(2, 4)),

            "target_populations": random.sample([
                "Adults with serious mental illness",
                "Transition-age youth (16-25)",
                "Justice-involved individuals",
                "Individuals experiencing homelessness",
                "Co-occurring disorders",
                "Geriatric population"
            ], k=random.randint(2, 4)),

            "services_offered": [],
            "deficiencies": deficiencies,
            "deficiencies_resolved": len(deficiencies) if status not in ["Deficiencies Identified"] else 0,

            "permits_required": {
                "building_permit": status not in ["Pre-Application"],
                "zoning_approval": status not in ["Pre-Application", "Application Submitted"],
                "fire_safety_clearance": status in ["Inspection Complete", "Conditional License Issued", "Full License Issued"],
                "health_department_approval": status in ["Inspection Complete", "Conditional License Issued", "Full License Issued"]
            },

            "inspections": [],
            "inspector_notes": "",

            "next_steps": [],
            "estimated_launch_date": None,

            "contact_dhcs_liaison": fake.name(),
            "liaison_email": fake.email(),
            "liaison_phone": fake.phone_number()
        }

        # Add services based on facility type
        if "Crisis" in facility_type:
            application["services_offered"].extend([
                "24/7 crisis assessment",
                "Short-term stabilization",
                "Medication management",
                "Individual and group therapy",
                "Discharge planning",
                "Crisis intervention"
            ])
        elif "Residential" in facility_type:
            application["services_offered"].extend([
                "Residential treatment",
                "Individual therapy",
                "Group therapy",
                "Medication management",
                "Life skills training",
                "Discharge planning"
            ])
        elif "Outpatient" in facility_type or "Clinic" in facility_type:
            application["services_offered"].extend([
                "Individual therapy",
                "Group therapy",
                "Medication management",
                "Case management",
                "Peer support",
                "Family therapy"
            ])

        # Add status-specific details
        if status == "Pre-Application":
            application["next_steps"] = [
                "Complete pre-application consultation",
                "Secure facility location",
                "Obtain zoning approval",
                "Submit full application"
            ]
        elif status == "Application Submitted":
            application["next_steps"] = [
                "DHCS completeness review (5 business days)",
                "Technical review (4-6 weeks)",
                "Respond to any deficiencies"
            ]
        elif status == "Deficiencies Identified":
            application["next_steps"] = [
                f"Correct {len(deficiencies)} identified deficiencies",
                "Resubmit corrected documents (30 days)",
                "DHCS re-review (2-3 weeks)"
            ]
        elif status == "Inspection Scheduled":
            inspection_date = datetime.now() + timedelta(days=random.randint(7, 30))
            application["next_steps"] = [
                f"Site inspection scheduled for {inspection_date.strftime('%Y-%m-%d')}",
                "Ensure facility ready for inspection",
                "All staff credentials available for review"
            ]
            application["inspections"].append({
                "inspection_type": "Initial License Inspection",
                "scheduled_date": inspection_date.strftime("%Y-%m-%d"),
                "inspector": fake.name()
            })
        elif status == "Inspection Complete":
            application["inspections"].append({
                "inspection_type": "Initial License Inspection",
                "completed_date": (datetime.now() - timedelta(days=random.randint(3, 14))).strftime("%Y-%m-%d"),
                "inspector": fake.name(),
                "result": "Passed" if random.random() > 0.3 else "Passed with minor corrections"
            })
            application["next_steps"] = [
                "Await conditional license issuance (1-2 weeks)",
                "Begin staff hiring and training",
                "Prepare for service launch"
            ]
        elif status == "Conditional License Issued":
            license_date = datetime.now() - timedelta(days=random.randint(7, 60))
            application["license_issue_date"] = license_date.strftime("%Y-%m-%d")
            application["license_expiration_date"] = (license_date + timedelta(days=180)).strftime("%Y-%m-%d")
            application["estimated_launch_date"] = (datetime.now() + timedelta(days=random.randint(30, 90))).strftime("%Y-%m-%d")
            application["next_steps"] = [
                "Begin operations",
                "6-month operational review for full license",
                "Submit quarterly reports to DHCS"
            ]
        elif status == "Full License Issued":
            license_date = datetime.now() - timedelta(days=random.randint(180, 730))
            application["license_issue_date"] = license_date.strftime("%Y-%m-%d")
            application["license_expiration_date"] = (license_date + timedelta(days=365)).strftime("%Y-%m-%d")
            application["estimated_launch_date"] = license_date.strftime("%Y-%m-%d")
            application["operational_since"] = license_date.strftime("%Y-%m-%d")
            application["next_steps"] = [
                "Annual license renewal",
                "Ongoing compliance monitoring",
                "Continue quality improvement"
            ]

        return application

    @staticmethod
    def generate_applications(count: int = 50) -> list:
        """Generate multiple applications"""
        applications = []
        for _ in range(count):
            applications.append(LicensingGenerator.generate_application())
        return applications

    @staticmethod
    def save_to_json(applications: list, output_path: str = "licensing_applications.json"):
        """Save applications to JSON"""
        with open(output_path, 'w') as f:
            json.dump(applications, f, indent=2)
        print(f"Generated {len(applications)} licensing applications")
        print(f"Saved to {output_path}")

        # Print summary
        by_status = {}
        by_type = {}
        total_capacity = 0

        for app in applications:
            status = app['license_status']
            ftype = app['facility_type']
            by_status[status] = by_status.get(status, 0) + 1
            by_type[ftype] = by_type.get(ftype, 0) + 1
            total_capacity += app['capacity']

        print("\nApplications by status:")
        for status, count in sorted(by_status.items()):
            print(f"  {status}: {count}")

        print("\nApplications by facility type:")
        for ftype, count in sorted(by_type.items()):
            print(f"  {ftype}: {count}")

        print(f"\nTotal capacity: {total_capacity} beds/clients")


if __name__ == "__main__":
    applications = LicensingGenerator.generate_applications(50)
    LicensingGenerator.save_to_json(applications)
