"""
Test Evidence-First Pipeline
Runs a single question through Extract → Verify → Compose pipeline and outputs audit trail.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment before imports
import os
os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

from agents.core.curation_orchestrator import CurationOrchestrator

def test_evidence_pipeline():
    """
    Test evidence-first pipeline with a single question.

    This generates a complete audit trail showing:
    1. Retrieved chunks
    2. Extracted requirements (verbatim quotes)
    3. Verified requirements (grounding gate)
    4. Rejected requirements (with reasons)
    5. Final composed answer (with requirement references)
    """
    print("="*80)
    print("EVIDENCE-FIRST PIPELINE TEST")
    print("="*80)

    # Test question
    test_question = {
        "question": "What are the documentation requirements for client assessments?",
        "topic": "County Behavioral Health System Overview",
        "sub_section": "Assessment Standards",
        "category": "compliance"
    }

    print(f"\nQuestion: {test_question['question']}")
    print(f"Topic: {test_question['topic']}")
    print("="*80)

    # Initialize orchestrator with evidence-first pipeline
    print("\n[1/6] Initializing Evidence-First Pipeline...")
    orchestrator = CurationOrchestrator(use_evidence_pipeline=True)

    # Execute workflow
    print("[2/6] Executing workflow...\n")
    result = orchestrator.execute(test_question)

    # Check success
    if not result.get("success"):
        print(f"❌ ERROR: {result.get('error')}")
        return None

    print("✅ Workflow completed successfully\n")

    # Print audit trail
    print("="*80)
    print("EVIDENCE AUDIT TRAIL")
    print("="*80)

    audit_trail = result.get("evidence_audit_trail", {})

    # Retrieval stage
    retrieval = audit_trail.get("retrieval_stage", {})
    print(f"\n[RETRIEVAL]")
    print(f"  Statute chunks: {retrieval.get('statute_chunks_retrieved', 0)}")
    print(f"  Policy chunks: {retrieval.get('policy_chunks_retrieved', 0)}")
    print(f"  Total chunks: {retrieval.get('total_chunks', 0)}")

    # Extraction stage
    extraction = audit_trail.get("extraction_stage", {})
    print(f"\n[EXTRACTION]")
    print(f"  Requirements extracted: {extraction.get('total_requirements_extracted', 0)}")
    print(f"    - Statute requirements: {extraction.get('statute_requirements', 0)}")
    print(f"    - Policy requirements: {extraction.get('policy_requirements', 0)}")

    # Verification stage
    verification = audit_trail.get("verification_stage", {})
    print(f"\n[VERIFICATION]")
    print(f"  Requirements passed: {verification.get('requirements_passed', 0)}")
    print(f"  Requirements rejected: {verification.get('requirements_rejected', 0)}")
    print(f"  Pass rate: {verification.get('verification_pass_rate', 0):.1%}")
    print(f"  Sufficient evidence: {'✅ Yes' if verification.get('has_sufficient_evidence') else '❌ No'}")

    if verification.get('rejection_reasons'):
        print(f"  Rejection reasons: {verification.get('rejection_reasons')}")

    if verification.get('missing_evidence'):
        print(f"  Missing evidence:")
        for missing in verification.get('missing_evidence', []):
            print(f"    - {missing}")

    # Composition stage
    composition = audit_trail.get("composition_stage", {})
    print(f"\n[COMPOSITION]")
    print(f"  Requirements used: {composition.get('requirements_used', 0)}")
    print(f"  Requirements unused: {composition.get('requirements_unused', 0)}")
    print(f"  Confidence: {composition.get('composition_confidence', 'unknown')}")
    print(f"  Has references: {'✅ Yes' if composition.get('has_requirement_references') else '❌ No'}")

    # Overall
    overall = audit_trail.get("overall", {})
    print(f"\n[OVERALL]")
    print(f"  Pipeline type: {overall.get('pipeline_type', 'unknown')}")
    print(f"  Grounding confidence: {overall.get('grounding_confidence', 'unknown')}")
    print(f"  Quality score: {overall.get('quality_score', 0):.1f}/10")
    print(f"  Passes review: {'✅ Yes' if overall.get('passes_review') else '❌ No'}")

    # Print sample extracted requirements
    extracted = result.get("extracted_requirements", [])
    if extracted:
        print("\n" + "="*80)
        print(f"SAMPLE EXTRACTED REQUIREMENTS ({len(extracted)} total)")
        print("="*80)
        for i, req in enumerate(extracted[:3], 1):  # Show first 3
            print(f"\n[{req.get('requirement_id')}]")
            print(f"  Source: {req.get('source_type')} - {req.get('document_id')}")
            print(f"  Quote: \"{req.get('exact_quote', '')}\"")
            print(f"  Confidence: {req.get('extraction_confidence', 'unknown')}")

    # Print verified requirements
    verified = result.get("verified_requirements", [])
    if verified:
        print("\n" + "="*80)
        print(f"VERIFIED REQUIREMENTS ({len(verified)} passed verification)")
        print("="*80)
        for i, req in enumerate(verified[:3], 1):  # Show first 3
            print(f"\n[{req.get('requirement_id')}]")
            print(f"  Source: {req.get('source_type')} - {req.get('document_id')}")
            print(f"  Quote: \"{req.get('exact_quote', '')}\"")
            print(f"  Rationale: {req.get('verification_rationale', '')}")

    # Print rejected requirements
    rejected = result.get("rejected_requirements", [])
    if rejected:
        print("\n" + "="*80)
        print(f"REJECTED REQUIREMENTS ({len(rejected)} failed verification)")
        print("="*80)
        for i, req in enumerate(rejected[:3], 1):  # Show first 3
            print(f"\n[{req.get('requirement_id')}]")
            print(f"  Source: {req.get('source_type')} - {req.get('document_id')}")
            print(f"  Quote: \"{req.get('exact_quote', '')}\"")
            print(f"  Rejection reason: {req.get('rejection_reason', '')}")
            print(f"  Rationale: {req.get('rejection_rationale', '')}")

    # Print final answer
    final_answer = result.get("final_answer", "")
    print("\n" + "="*80)
    print("FINAL ANSWER (with requirement references)")
    print("="*80)
    print(f"\n{final_answer}\n")

    # Save full result to file
    output_dir = Path(__file__).parent.parent / "benchmark_results" / "evidence_pipeline_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"test_result_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print("="*80)
    print(f"Full result saved to: {output_file}")
    print("="*80)

    return result


if __name__ == "__main__":
    result = test_evidence_pipeline()

    if result and result.get("success"):
        print("\n✅ Evidence-First Pipeline Test PASSED")
        sys.exit(0)
    else:
        print("\n❌ Evidence-First Pipeline Test FAILED")
        sys.exit(1)
