# Evidence-First Pipeline Design

**Date**: January 9, 2026
**Objective**: Replace free-form summarization with auditable Extract → Verify → Compose pipeline

---

## Current Architecture (Baseline)

```
Retrieval → Statute Analysis → Policy Analysis → Synthesis → Quality Review → Finalize
             (free-form)        (free-form)      (free-form)   (scoring)
```

**Issues**:
- Agents generate free-form summaries without explicit evidence grounding
- No audit trail linking statements to source chunks
- Quality reviewer scores outputs but doesn't verify grounding
- Difficult to defend claims to auditors

---

## New Architecture (Evidence-First)

```
Retrieval → Extract → Verify → Compose → Quality Review → Finalize
            (verbatim) (gate)   (grounded) (scoring)
```

**Key Changes**:
1. **Extract**: Replace free-form analysis with structured verbatim extraction
2. **Verify**: Add grounding gate to validate evidence explicitly addresses question
3. **Compose**: Generate summaries ONLY from verified evidence with explicit references

---

## Pipeline Stages (Detailed)

### Stage 1: Retrieval (Unchanged)
**Agent**: RetrievalAgent
**Input**: Question, topic, sub_section, category
**Output**: statute_chunks[], policy_chunks[]
**Function**: Vector search + metadata filtering

---

### Stage 2: Extract (NEW - Evidence Stage)

**Agent**: EvidenceExtractionAgent
**Input**: Question + statute_chunks + policy_chunks
**Output**: extracted_requirements[]

**Data Structure**:
```python
{
    "requirement_id": "REQ-S001",  # S=statute, P=policy
    "source_type": "statute" | "policy",
    "document_id": "W&I Code § 5899",
    "section_heading": "Mental Health Services Act",
    "exact_quote": "Counties shall provide community-based services to adults with severe mental illness.",  # 10-40 words, verbatim
    "chunk_id": "S1",  # Reference to original chunk
    "extraction_confidence": "high" | "medium" | "low"
}
```

**Rules**:
1. Extract ONLY requirement sentences (must/shall/required/prohibited)
2. Exact quotes only - NO paraphrasing or interpretation
3. Quote length: 10-40 words (excerpt if longer)
4. If no clear requirement exists in chunk, extract nothing
5. Each requirement gets unique ID (REQ-S001, REQ-S002, REQ-P001, etc.)

**LLM Prompt Structure**:
```
You are an evidence extraction specialist. Extract ONLY explicit requirement sentences.

Rules:
- Extract verbatim quotes (10-40 words)
- Only sentences with must/shall/required/prohibited/mandated
- NO interpretation or paraphrasing
- If unclear, skip

Input: [chunks]
Output: JSON array of extracted requirements
```

---

### Stage 3: Verify (NEW - Grounding Gate)

**Agent**: GroundingVerificationAgent
**Input**: Question + extracted_requirements[]
**Output**: verified_requirements[], rejected_requirements[]

**Verification Criteria**:
1. **Explicit addressing**: Does the requirement explicitly address the question?
   - ✅ Pass: Direct answer to question
   - ❌ Fail: Tangential, implied, or speculative

2. **Quote support**: Is the requirement fully supported by the exact quote?
   - ✅ Pass: Quote proves the requirement
   - ❌ Fail: Requires inference or external knowledge

3. **Completeness**: Is the quote self-contained or missing context?
   - ✅ Pass: Quote is understandable alone
   - ❌ Fail: Requires reading surrounding text

**Data Structure**:
```python
{
    "requirement_id": "REQ-S001",
    "verified": true | false,
    "rejection_reason": null | "does_not_address_question" | "requires_inference" | "incomplete_quote",
    "verification_rationale": "Explicitly requires counties to provide services, directly addresses question."
}
```

**Fail-Safe Logic**:
```python
if len(verified_requirements) == 0:
    return {
        "result": "NO_AUTHORITATIVE_EVIDENCE",
        "message": "No authoritative requirement found in provided sources.",
        "missing_evidence": ["Specific statute or policy addressing [question topic]"]
    }
```

**LLM Prompt Structure**:
```
You are a grounding verification specialist. Validate that extracted requirements:
1. Explicitly address the question (no inference)
2. Are fully supported by the quoted text
3. Do not require external context

For each requirement, output: verified (true/false), rejection_reason, rationale

Question: [question]
Extracted Requirements: [requirements]
Output: JSON verification results
```

---

### Stage 4: Compose (NEW - Evidence-Based Composition)

**Agent**: EvidenceCompositionAgent
**Input**: Question + verified_requirements[]
**Output**: final_answer, requirement_references[]

**Composition Rules**:
1. **Every statement** must reference at least one verified requirement ID
2. NO new facts, interpretations, or conclusions beyond verified evidence
3. If conflicting requirements, present both with requirement IDs
4. Use requirement IDs inline: "Counties must provide services [REQ-S001, REQ-P003]"

**Data Structure**:
```python
{
    "final_answer": "Counties must provide community-based services [REQ-S001] and ensure 24/7 crisis access [REQ-P002]...",
    "requirement_references": [
        {
            "requirement_id": "REQ-S001",
            "used_in_answer": true,
            "statement": "Counties must provide community-based services"
        },
        {
            "requirement_id": "REQ-P002",
            "used_in_answer": true,
            "statement": "Ensure 24/7 crisis access"
        }
    ],
    "unused_requirements": [],  # Verified but not relevant to compose final answer
    "confidence": "high"  # Based on evidence quantity and quality
}
```

**LLM Prompt Structure**:
```
You are a compliance summary writer. Generate a readable answer using ONLY verified requirements.

Rules:
- Every statement must reference requirement IDs
- NO interpretation beyond what's quoted
- Format: "Statement [REQ-ID1, REQ-ID2]"
- If evidence conflicts, present both views

Question: [question]
Verified Requirements: [requirements with IDs and quotes]
Output: Final answer with inline requirement references
```

---

### Stage 5: Quality Review (MODIFIED)

**Agent**: QualityReviewerAgent (enhanced)
**Additional Checks**:
1. **Grounding check**: Every statement has requirement ID reference?
2. **Evidence integrity**: All requirement IDs exist in verified_requirements?
3. **No hallucination**: No claims beyond verified evidence?

**Failure conditions**:
- Any statement without requirement ID → FAIL
- Requirement ID not in verified list → FAIL
- Claims beyond evidence → FAIL

---

## Updated State Schema

```python
class CurationState(TypedDict):
    # Existing fields
    question: str
    statute_chunks: List[Dict]
    policy_chunks: List[Dict]

    # NEW: Evidence extraction
    extracted_requirements: List[Dict]  # All verbatim extracts
    extraction_metadata: Dict  # Counts, confidence stats

    # NEW: Verification
    verified_requirements: List[Dict]  # Passed grounding gate
    rejected_requirements: List[Dict]  # Failed grounding gate
    verification_metadata: Dict  # Pass rate, rejection reasons

    # NEW: Composition
    final_answer: str  # With inline [REQ-ID] references
    requirement_references: List[Dict]  # Which requirements used
    missing_evidence: List[str]  # What evidence is missing

    # NEW: Audit trail
    evidence_audit_trail: Dict  # Full lineage from chunks → answer
    grounding_confidence: str  # "high" | "medium" | "low" | "insufficient"

    # Existing outputs (for backward compatibility)
    statute_summary: str  # Generated from verified statute requirements
    policy_summary: str   # Generated from verified policy requirements
    final_summary: str    # Same as final_answer
```

---

## Workflow Integration (LangGraph)

**New workflow graph**:
```python
workflow.add_node("retrieval", self._run_retrieval)
workflow.add_node("extract_evidence", self._run_evidence_extraction)  # NEW
workflow.add_node("verify_grounding", self._run_grounding_verification)  # NEW
workflow.add_node("compose_answer", self._run_evidence_composition)  # NEW
workflow.add_node("quality_review", self._run_quality_review)  # MODIFIED
workflow.add_node("finalize", self._finalize_response)

workflow.set_entry_point("retrieval")
workflow.add_edge("retrieval", "extract_evidence")
workflow.add_edge("extract_evidence", "verify_grounding")

# Conditional: If no verified evidence, skip composition
workflow.add_conditional_edges(
    "verify_grounding",
    self._has_verified_evidence,
    {
        "compose": "compose_answer",
        "no_evidence": "finalize"  # Return "No authoritative evidence" message
    }
)

workflow.add_edge("compose_answer", "quality_review")
workflow.add_conditional_edges(
    "quality_review",
    self._should_revise,
    {
        "revise": "compose_answer",  # Retry composition if quality fails
        "finalize": "finalize"
    }
)
workflow.add_edge("finalize", END)
```

---

## Example Audit Trail (JSON Output)

```json
{
  "question": "What are the documentation requirements for client assessments?",
  "grounding_confidence": "high",
  "extracted_requirements": [
    {
      "requirement_id": "REQ-S001",
      "source_type": "statute",
      "document_id": "W&I Code § 5600.5",
      "section_heading": "Client Records",
      "exact_quote": "Counties shall maintain client records including assessment documentation for all behavioral health services recipients.",
      "chunk_id": "S1",
      "extraction_confidence": "high"
    },
    {
      "requirement_id": "REQ-P001",
      "source_type": "policy",
      "document_id": "Policy Manual Section 4.2.1",
      "section_heading": "Assessment Standards",
      "exact_quote": "All assessments must be documented within 60 days of initial contact.",
      "chunk_id": "P1",
      "extraction_confidence": "high"
    }
  ],
  "verified_requirements": [
    {
      "requirement_id": "REQ-S001",
      "verified": true,
      "rejection_reason": null,
      "verification_rationale": "Explicitly requires assessment documentation, directly addresses question."
    },
    {
      "requirement_id": "REQ-P001",
      "verified": true,
      "rejection_reason": null,
      "verification_rationale": "Specifies documentation timeline requirement, directly addresses question."
    }
  ],
  "rejected_requirements": [],
  "final_answer": "Counties must maintain client records including assessment documentation [REQ-S001]. All assessments must be documented within 60 days of initial contact [REQ-P001].",
  "requirement_references": [
    {
      "requirement_id": "REQ-S001",
      "used_in_answer": true,
      "statement": "Counties must maintain assessment documentation"
    },
    {
      "requirement_id": "REQ-P001",
      "used_in_answer": true,
      "statement": "Document within 60 days"
    }
  ],
  "missing_evidence": [],
  "evidence_audit_trail": {
    "total_chunks_retrieved": 10,
    "total_requirements_extracted": 2,
    "total_requirements_verified": 2,
    "verification_pass_rate": 1.0,
    "composition_confidence": "high"
  }
}
```

---

## Implementation Plan

### Phase 1: Create New Agents (3 files)
1. `agents/core/evidence_extraction_agent.py` - Extract verbatim requirements
2. `agents/core/grounding_verification_agent.py` - Validate evidence grounding
3. `agents/core/evidence_composition_agent.py` - Compose from verified evidence

### Phase 2: Update State Schema
1. `agents/core/curation_orchestrator.py` - Add new state fields
2. Update CurationState TypedDict with evidence fields

### Phase 3: Update Orchestrator Workflow
1. Add new nodes to LangGraph workflow
2. Update edges and conditional logic
3. Add fail-safe path for no evidence

### Phase 4: Modify Quality Reviewer
1. Add grounding checks to quality review
2. Validate requirement ID references
3. Detect hallucination beyond evidence

### Phase 5: Testing & Validation
1. Run single-question test with full audit trail
2. Validate JSON output structure
3. Document gaps and blockers

---

## Known Gaps & Blockers

### 1. Placeholder Statutes (CRITICAL)
**Issue**: 15/18 statutes are placeholders (verified in previous session)
**Impact**: Extract stage will find minimal statute evidence
**Evidence**: `grep -c "^\[Placeholder" data/statutes.md` returns 15
**Mitigation**: Document as "missing evidence" in audit trail

### 2. Chunk Quality (MEDIUM)
**Issue**: Some chunks may not contain complete requirement sentences
**Impact**: Extract stage may truncate mid-sentence
**Mitigation**: Validate chunk boundaries during data migration

### 3. Policy Document Structure (MEDIUM)
**Issue**: Policies may have narrative text without explicit "must/shall"
**Impact**: Extract stage may miss implicit requirements
**Mitigation**: Expand extraction patterns to include "counties are required to"

### 4. Cross-Reference Requirements (LOW)
**Issue**: Some requirements reference other sections ("see § 5899(b)")
**Impact**: Extracted quotes may be incomplete without context
**Mitigation**: Mark as low extraction confidence, flag in verification

---

## Quality Bar

**Auditor-Defensible Criteria**:
1. ✅ Every statement has explicit evidence reference
2. ✅ All evidence is verbatim from source documents
3. ✅ Verification logic is transparent (pass/fail with reasons)
4. ✅ No hallucination beyond verified evidence
5. ✅ Complete audit trail from chunks to final answer

**Fail-Safe Guarantee**:
- If evidence is insufficient → Return "No authoritative requirement found"
- If grounding fails → Reject requirement with explicit reason
- If composition lacks references → Quality review FAILS

**Confidence Levels**:
- **High**: 5+ verified requirements, all explicitly address question
- **Medium**: 2-4 verified requirements, some tangential
- **Low**: 1 verified requirement, or requires inference
- **Insufficient**: 0 verified requirements → Fail safe

---

**Next Step**: Implement Phase 1 (Create 3 new agents)
