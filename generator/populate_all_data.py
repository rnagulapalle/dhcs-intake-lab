"""
Master Script to Generate All Synthetic Data and Populate Vector DB
Runs all generators and initializes ChromaDB with comprehensive policy documents
"""
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from policy_documents_generator import PolicyDocumentsGenerator
from infrastructure_generator import InfrastructureGenerator
from licensing_generator import LicensingGenerator
from outcomes_generator import OutcomesGenerator

# Import agents modules for vector DB population
from agents.knowledge.knowledge_base import DHCSKnowledgeBase


def generate_all_synthetic_data():
    """Generate all synthetic data files"""
    print("=" * 80)
    print("GENERATING ALL SYNTHETIC DATA")
    print("=" * 80)
    print()

    # 1. Policy Documents
    print("1. Generating Policy Documents...")
    print("-" * 80)
    policy_generator = PolicyDocumentsGenerator()
    policy_docs = policy_generator.generate_all_documents()

    with open("policy_documents.json", 'w') as f:
        import json
        json.dump(policy_docs, f, indent=2)
    print(f"✓ Generated {len(policy_docs)} policy documents")
    print(f"✓ Saved to policy_documents.json")
    print()

    # 2. Infrastructure Projects
    print("2. Generating Infrastructure Projects...")
    print("-" * 80)
    projects = InfrastructureGenerator.generate_projects(100)
    InfrastructureGenerator.save_to_json(projects, "infrastructure_projects.json")
    print()

    # 3. Licensing Applications
    print("3. Generating Licensing Applications...")
    print("-" * 80)
    applications = LicensingGenerator.generate_applications(50)
    LicensingGenerator.save_to_json(applications, "licensing_applications.json")
    print()

    # 4. BHOATR Outcomes Reports
    print("4. Generating BHOATR Outcomes Reports...")
    print("-" * 80)
    reports = OutcomesGenerator.generate_reports(count_per_county=4)
    OutcomesGenerator.save_to_json(reports, "outcomes_data.json")
    print()

    print("=" * 80)
    print("ALL SYNTHETIC DATA GENERATED SUCCESSFULLY")
    print("=" * 80)
    print()

    return {
        "policy_docs": policy_docs,
        "projects": projects,
        "applications": applications,
        "reports": reports
    }


def populate_vector_db(policy_docs):
    """Populate ChromaDB with policy documents"""
    print("=" * 80)
    print("POPULATING VECTOR DATABASE (ChromaDB)")
    print("=" * 80)
    print()

    try:
        # Initialize knowledge base
        print("Initializing ChromaDB knowledge base...")
        kb = DHCSKnowledgeBase()

        # Reset to start fresh
        print("Resetting existing collection...")
        kb.reset()

        # Add policy documents
        print(f"Adding {len(policy_docs)} policy documents to vector store...")
        kb.add_documents(policy_docs)

        print()
        print("✓ Vector database populated successfully")
        print(f"✓ Total documents in knowledge base: {kb.collection.count()}")
        print()

        # Test the vector DB with sample queries
        print("Testing Vector DB with sample queries...")
        print("-" * 80)

        test_queries = [
            "What are crisis stabilization unit requirements?",
            "How do I apply for a facility license?",
            "What are Prop 1 funding requirements?",
            "What are mobile crisis team standards?",
            "What metrics are required for BHOATR reporting?"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\nTest Query {i}: {query}")
            results = kb.search(query, n_results=2)
            if results:
                print(f"  ✓ Found {len(results)} relevant results")
                print(f"  Top result: {results[0]['metadata'].get('source', 'Unknown')}")
            else:
                print(f"  ✗ No results found")

        print()
        print("=" * 80)
        print("VECTOR DATABASE READY")
        print("=" * 80)
        print()

        return kb

    except Exception as e:
        print(f"✗ Error populating vector database: {str(e)}")
        print(f"  Make sure the agent-api service is running or OPENAI_API_KEY is set")
        print()
        return None


def print_summary(data):
    """Print comprehensive summary of generated data"""
    print("=" * 80)
    print("DATA GENERATION SUMMARY")
    print("=" * 80)
    print()

    print("📊 Generated Data Files:")
    print("-" * 80)
    print(f"1. policy_documents.json          - {len(data['policy_docs'])} documents")
    print(f"2. infrastructure_projects.json   - {len(data['projects'])} projects")
    print(f"3. licensing_applications.json    - {len(data['applications'])} applications")
    print(f"4. outcomes_data.json             - {len(data['reports'])} quarterly reports")
    print()

    print("🎯 Use Case Coverage:")
    print("-" * 80)
    print("✓ Crisis Triage          - Existing crisis event generator (Kafka)")
    print("✓ Policy Q&A             - 20+ comprehensive policy documents in vector DB")
    print("✓ BHOATR Reporting       - 40 quarterly outcome reports with full metrics")
    print("✓ Licensing Assistant    - 50 facility licensing applications")
    print("✓ IP Compliance          - Integrated Plan requirements in policy docs")
    print("✓ Infrastructure         - 100 Prop 1/SB 326 projects with status tracking")
    print("✓ Population Analytics   - Demographics in outcomes data + policy guidance")
    print("✓ Resource Allocation    - Budget data in projects + allocation framework")
    print()

    print("💾 Data Statistics:")
    print("-" * 80)

    # Projects stats
    total_project_budget = sum(p['budget_total'] for p in data['projects'])
    total_capacity = sum(p['capacity'] for p in data['projects'])
    print(f"Infrastructure Projects:")
    print(f"  Total budget: ${total_project_budget:,}")
    print(f"  Total capacity: {total_capacity} beds/units")
    print()

    # Applications stats
    total_app_capacity = sum(a['capacity'] for a in data['applications'])
    licensed_count = len([a for a in data['applications'] if a['license_status'] == 'Full License Issued'])
    print(f"Licensing Applications:")
    print(f"  Total capacity: {total_app_capacity} beds/clients")
    print(f"  Fully licensed: {licensed_count}")
    print()

    # Outcomes stats
    total_crisis_events = sum(r['access_metrics']['crisis_hotline']['total_calls'] for r in data['reports'])
    counties_covered = len(set(r['county'] for r in data['reports']))
    print(f"BHOATR Outcomes:")
    print(f"  Counties covered: {counties_covered}")
    print(f"  Total crisis events tracked: {total_crisis_events:,}")
    print()

    print("🚀 Next Steps:")
    print("-" * 80)
    print("1. Start the full stack: docker-compose up -d")
    print("2. Verify API is running: curl http://localhost:8000/health")
    print("3. Test Policy Q&A: curl http://localhost:8000/knowledge/search?query='Prop 1 requirements'")
    print("4. Open dashboard: http://localhost:8501")
    print("5. Try different use cases in the dashboard UI")
    print()

    print("📚 Policy Documents in Vector DB:")
    print("-" * 80)
    categories = {}
    for doc in data['policy_docs']:
        cat = doc['metadata'].get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} documents")
    print()

    print("=" * 80)
    print("✓ ALL DATA GENERATED AND READY FOR USE")
    print("=" * 80)


def main():
    """Main execution"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  DHCS BHT Multi-Agent System - Comprehensive Data Generator".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Generate all data
    data = generate_all_synthetic_data()

    # Populate vector DB
    kb = populate_vector_db(data['policy_docs'])

    # Print summary
    print_summary(data)

    if kb:
        print("✓ Success! All data generated and vector database populated.")
    else:
        print("⚠ Data generated successfully, but vector database population failed.")
        print("  You can run this script again after starting the API service.")

    print()


if __name__ == "__main__":
    main()
