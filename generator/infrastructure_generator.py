"""
Infrastructure Project Data Generator
Generates synthetic Prop 1 and SB 326 infrastructure project data
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

PROJECT_TYPES = [
    "Crisis Stabilization Unit",
    "Residential Treatment Facility",
    "Supportive Housing",
    "Mobile Crisis Infrastructure",
    "Crisis Residential Program",
    "Psychiatric Health Facility",
    "Wellness Center",
    "Youth Crisis Center"
]

PROJECT_STATUSES = ["Planning", "Design", "Permitting", "Construction", "Completion", "Operational"]

FUNDING_SOURCES = ["Proposition 1", "SB 326", "County Match", "MHSA", "Federal Grant"]


class InfrastructureGenerator:
    """Generate infrastructure project data"""

    @staticmethod
    def generate_project() -> dict:
        """Generate a single infrastructure project"""
        project_type = random.choice(PROJECT_TYPES)
        county = random.choice(COUNTIES)
        status = random.choices(
            PROJECT_STATUSES,
            weights=[10, 15, 10, 30, 20, 15]
        )[0]

        # Generate capacity based on project type
        if "Housing" in project_type:
            capacity = random.randint(20, 150)
            capacity_unit = "units"
        elif "Mobile" in project_type:
            capacity = random.randint(2, 8)
            capacity_unit = "teams"
        else:
            capacity = random.randint(16, 50)
            capacity_unit = "beds"

        # Generate budget based on project type and capacity
        if "Housing" in project_type:
            budget = capacity * random.randint(400000, 600000)
        elif "Mobile" in project_type:
            budget = capacity * random.randint(300000, 500000)
        else:
            budget = capacity * random.randint(450000, 650000)

        # Calculate dates based on status
        start_date = datetime.now() - timedelta(days=random.randint(90, 730))
        if status == "Planning":
            completion_percentage = random.randint(10, 30)
            expected_completion = datetime.now() + timedelta(days=random.randint(180, 540))
        elif status == "Design":
            completion_percentage = random.randint(25, 50)
            expected_completion = datetime.now() + timedelta(days=random.randint(120, 450))
        elif status == "Permitting":
            completion_percentage = random.randint(40, 60)
            expected_completion = datetime.now() + timedelta(days=random.randint(90, 360))
        elif status == "Construction":
            completion_percentage = random.randint(55, 85)
            expected_completion = datetime.now() + timedelta(days=random.randint(60, 270))
        elif status == "Completion":
            completion_percentage = random.randint(90, 99)
            expected_completion = datetime.now() + timedelta(days=random.randint(14, 60))
        else:  # Operational
            completion_percentage = 100
            expected_completion = datetime.now() - timedelta(days=random.randint(30, 365))

        # Determine if project is on schedule
        original_timeline = random.randint(18, 36)  # months
        current_month = (datetime.now() - start_date).days / 30
        expected_progress = (current_month / original_timeline) * 100
        is_delayed = completion_percentage < (expected_progress - 10)
        is_ahead = completion_percentage > (expected_progress + 10)

        if is_delayed:
            timeline_status = "Delayed"
        elif is_ahead:
            timeline_status = "Ahead of Schedule"
        else:
            timeline_status = "On Schedule"

        # Budget utilization
        budget_spent = int(budget * (completion_percentage / 100) * random.uniform(0.9, 1.15))
        budget_variance = ((budget_spent - (budget * completion_percentage / 100)) / budget) * 100

        # Funding breakdown
        funding_breakdown = {}
        remaining_budget = budget
        for source in random.sample(FUNDING_SOURCES, k=random.randint(2, 4)):
            if source == FUNDING_SOURCES[-1]:  # Last source gets remainder
                funding_breakdown[source] = remaining_budget
            else:
                amount = int(remaining_budget * random.uniform(0.2, 0.6))
                funding_breakdown[source] = amount
                remaining_budget -= amount

        project = {
            "project_id": str(uuid.uuid4()),
            "project_name": f"{county} {project_type}",
            "project_type": project_type,
            "county": county,
            "status": status,
            "timeline_status": timeline_status,

            "capacity": capacity,
            "capacity_unit": capacity_unit,

            "budget_total": budget,
            "budget_spent": budget_spent,
            "budget_remaining": budget - budget_spent,
            "budget_variance_percent": round(budget_variance, 2),
            "funding_breakdown": funding_breakdown,

            "start_date": start_date.strftime("%Y-%m-%d"),
            "expected_completion_date": expected_completion.strftime("%Y-%m-%d"),
            "completion_percentage": completion_percentage,
            "original_timeline_months": original_timeline,

            "address": fake.street_address(),
            "city": county,  # Simplified
            "zip_code": fake.zipcode(),

            "project_manager": fake.name(),
            "contractor": fake.company() if status in ["Construction", "Completion", "Operational"] else None,

            "permits_status": "Approved" if status not in ["Planning", "Design"] else "Pending",
            "environmental_review": "Complete" if status not in ["Planning"] else "In Progress",

            "jobs_created": random.randint(15, 100) if status in ["Construction", "Completion", "Operational"] else 0,
            "local_hire_percentage": random.randint(30, 70) if status in ["Construction"] else None,

            "community_benefits": [
                f"{capacity} {capacity_unit} of behavioral health capacity",
                f"Estimated {random.randint(50, 500)} individuals served annually",
                f"{random.randint(15, 80)} permanent jobs created"
            ],

            "risks": [],
            "milestones_completed": [],
            "next_milestones": []
        }

        # Add status-specific details
        if is_delayed:
            project["risks"].extend([
                "Behind schedule - permitting delays",
                "Potential budget overrun",
                f"{random.randint(30, 90)} day delay estimated"
            ])

        if status == "Construction":
            project["milestones_completed"].extend([
                "Site preparation complete",
                "Foundation poured",
                "Framing in progress"
            ])
            project["next_milestones"].extend([
                "Framing completion",
                "MEP installation",
                "Interior finishes"
            ])
        elif status == "Completion":
            project["milestones_completed"].extend([
                "Construction complete",
                "Final inspections passed",
                "Certificate of occupancy received"
            ])
            project["next_milestones"].extend([
                "Staff hiring",
                "Licensing application",
                "Service launch"
            ])
        elif status == "Operational":
            project["operational_metrics"] = {
                "months_operational": random.randint(1, 12),
                "current_occupancy_rate": random.randint(60, 95),
                "individuals_served_mtd": random.randint(20, 200),
                "staff_hired": random.randint(15, 80),
                "vacancy_rate": random.randint(5, 25)
            }

        return project

    @staticmethod
    def generate_projects(count: int = 100) -> list:
        """Generate multiple projects"""
        projects = []
        for _ in range(count):
            projects.append(InfrastructureGenerator.generate_project())
        return projects

    @staticmethod
    def save_to_json(projects: list, output_path: str = "infrastructure_projects.json"):
        """Save projects to JSON"""
        with open(output_path, 'w') as f:
            json.dump(projects, f, indent=2)
        print(f"Generated {len(projects)} infrastructure projects")
        print(f"Saved to {output_path}")

        # Print summary
        by_status = {}
        by_type = {}
        total_budget = 0
        total_capacity = 0

        for project in projects:
            status = project['status']
            ptype = project['project_type']
            by_status[status] = by_status.get(status, 0) + 1
            by_type[ptype] = by_type.get(ptype, 0) + 1
            total_budget += project['budget_total']
            total_capacity += project['capacity']

        print("\nProjects by status:")
        for status, count in sorted(by_status.items()):
            print(f"  {status}: {count}")

        print("\nProjects by type:")
        for ptype, count in sorted(by_type.items()):
            print(f"  {ptype}: {count}")

        print(f"\nTotal budget: ${total_budget:,}")
        print(f"Total capacity: {total_capacity} beds/units")


if __name__ == "__main__":
    projects = InfrastructureGenerator.generate_projects(100)
    InfrastructureGenerator.save_to_json(projects)
