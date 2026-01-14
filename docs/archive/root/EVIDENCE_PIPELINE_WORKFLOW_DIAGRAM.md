# Evidence-First Pipeline Workflow Diagram

**Date**: January 9, 2026
**Architecture**: Extract → Verify → Compose Pattern

---

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EVIDENCE-FIRST PIPELINE                               │
│                                                                               │
│  Input Question → Retrieval → Extract → Verify → Compose → Quality → Output │
│                                  ↓        ↓        ↓                         │
│                              Verbatim  Gate    Grounded                      │
│                               Quotes   Check    Answer                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Workflow (LangGraph)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: RETRIEVAL                                                           │
│ Agent: RetrievalAgent                                                         │
│ Input: Question, topic, sub_section, category                                │
│ Output: statute_chunks[], policy_chunks[]                                    │
│                                                                               │
│ • Vector search in ChromaDB                                                  │
│ • Metadata filtering (statute vs policy)                                     │
│ • Similarity threshold filtering (>= 0.5)                                    │
│ • Top-k = 10 per type                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: EVIDENCE EXTRACTION                                                 │
│ Agent: EvidenceExtractionAgent                                               │
│ Input: Question + statute_chunks + policy_chunks                             │
│ Output: extracted_requirements[]                                             │
│                                                                               │
│ RULES (STRICT):                                                              │
│ • Extract ONLY verbatim quotes (10-40 words)                                 │
│ • Only sentences with must/shall/required/prohibited                         │
│ • NO paraphrasing or interpretation                                          │
│ • Each requirement gets unique ID (REQ-S001, REQ-P001, etc.)                 │
│ • If no clear requirement → extract nothing                                  │
│                                                                               │
│ Data Structure:                                                              │
│   {                                                                          │
│     requirement_id: "REQ-S001",                                              │
│     source_type: "statute" | "policy",                                       │
│     document_id: "W&I Code § 5899",                                          │
│     section_heading: "Mental Health Services Act",                           │
│     exact_quote: "Counties shall provide...",  # 10-40 words verbatim       │
│     chunk_id: "S1",                                                          │
│     extraction_confidence: "high" | "medium" | "low"                         │
│   }                                                                          │
│                                                                               │
│ LLM: Claude Sonnet with temperature=0.0 (deterministic)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: GROUNDING VERIFICATION (GATE)                                       │
│ Agent: GroundingVerificationAgent                                            │
│ Input: Question + extracted_requirements[]                                   │
│ Output: verified_requirements[], rejected_requirements[]                     │
│                                                                               │
│ VERIFICATION CRITERIA (ALL must pass):                                       │
│ 1. Explicit Addressing: Does requirement explicitly address question?        │
│    ✅ Pass: Direct answer                                                    │
│    ❌ Fail: Tangential, implied, speculative                                 │
│                                                                               │
│ 2. Quote Support: Is requirement fully supported by exact quote?             │
│    ✅ Pass: Quote proves requirement (no inference needed)                   │
│    ❌ Fail: Requires interpretation or external knowledge                    │
│                                                                               │
│ 3. Completeness: Is quote self-contained?                                    │
│    ✅ Pass: Understandable without context                                   │
│    ❌ Fail: Missing context or fragmentary                                   │
│                                                                               │
│ REJECTION REASONS:                                                           │
│ • does_not_address_question                                                  │
│ • requires_inference                                                         │
│ • incomplete_quote                                                           │
│                                                                               │
│ FAIL-SAFE LOGIC:                                                             │
│ if len(verified_requirements) == 0:                                          │
│     return "No authoritative requirement found in provided sources."         │
│     + missing_evidence list                                                  │
│                                                                               │
│ LLM: Claude Sonnet with temperature=0.0 (deterministic)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
                          ┌──────────────────────┐
                          │ Has Verified         │
                          │ Evidence?            │
                          └──────────────────────┘
                                 /        \
                            YES /          \ NO
                               ↓            ↓
                          [COMPOSE]    [FINALIZE]
                                         (No evidence
                                          message)
                               ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: EVIDENCE COMPOSITION                                                │
│ Agent: EvidenceCompositionAgent                                              │
│ Input: Question + verified_requirements[]                                    │
│ Output: final_answer, requirement_references[]                               │
│                                                                               │
│ COMPOSITION RULES (STRICT):                                                  │
│ • EVERY statement must reference requirement ID(s)                           │
│ • NO new facts beyond verified evidence                                      │
│ • If conflicting requirements → present both with IDs                        │
│ • Format: "Statement [REQ-S001, REQ-P002]"                                   │
│                                                                               │
│ Output Format:                                                               │
│   final_answer: "Counties must maintain records [REQ-S001]..."              │
│   requirement_references: [                                                  │
│     {                                                                        │
│       requirement_id: "REQ-S001",                                            │
│       used_in_answer: true,                                                  │
│       statement_context: "Record maintenance requirement"                    │
│     }                                                                        │
│   ]                                                                          │
│                                                                               │
│ CONFIDENCE LEVELS:                                                           │
│ • high: 5+ verified requirements, most used                                  │
│ • medium: 2-4 verified requirements                                          │
│ • low: 1 verified requirement                                                │
│ • insufficient: 0 verified requirements (should not reach here)              │
│                                                                               │
│ LLM: Claude Sonnet with temperature=0.2 (low creativity)                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 5: QUALITY REVIEW (ENHANCED)                                           │
│ Agent: QualityReviewerAgent                                                  │
│ Input: final_answer + verified_requirements                                  │
│ Output: quality_score, passes_review                                         │
│                                                                               │
│ ADDITIONAL CHECKS (Evidence-First):                                          │
│ 1. Grounding Check: Every statement has requirement ID?                      │
│ 2. Evidence Integrity: All referenced IDs exist in verified list?            │
│ 3. No Hallucination: No claims beyond verified evidence?                     │
│                                                                               │
│ FAILURE CONDITIONS:                                                          │
│ • Any statement without requirement ID → FAIL                                │
│ • Referenced ID not in verified list → FAIL                                  │
│ • Claims beyond verified evidence → FAIL                                     │
│                                                                               │
│ Threshold: quality_score >= 7.0 to pass                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
                          ┌──────────────────────┐
                          │ Passes Review?       │
                          │ (score >= 7.0)       │
                          └──────────────────────┘
                                 /        \
                           PASS /          \ FAIL
                               ↓            ↓ (if revision_count < 2)
                          [FINALIZE]    [REVISE]
                                         → Back to COMPOSE
                               ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 6: FINALIZE                                                            │
│ Agent: Orchestrator (internal)                                               │
│ Input: final_state with all evidence                                         │
│ Output: Complete response with audit trail                                   │
│                                                                               │
│ AUDIT TRAIL CONSTRUCTION:                                                    │
│ • retrieval_stage: Chunk counts                                              │
│ • extraction_stage: Requirements extracted, pass rates                       │
│ • verification_stage: Pass/fail counts, rejection reasons                    │
│ • composition_stage: Requirements used, confidence                           │
│ • overall: Pipeline type, grounding confidence, quality score                │
│                                                                               │
│ OUTPUT FIELDS:                                                               │
│ • final_answer (with [REQ-ID] references)                                    │
│ • statute_summary, policy_summary (POC compatibility)                        │
│ • extracted_requirements[]                                                   │
│ • verified_requirements[]                                                    │
│ • rejected_requirements[]                                                    │
│ • requirement_references[]                                                   │
│ • missing_evidence[]                                                         │
│ • evidence_audit_trail{}                                                     │
│ • composition_confidence                                                     │
│ • quality_score, passes_review                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
                               [END OUTPUT]
```

---

## Fail-Safe Paths

### Path 1: No Evidence Found After Extraction
```
Retrieval → Extract → [No requirements extracted]
                ↓
            Verify → has_sufficient_evidence = false
                ↓
            Finalize (skip composition)
                ↓
            Output: "No authoritative requirement found in provided sources."
                    + missing_evidence list
```

### Path 2: No Evidence Passes Verification
```
Retrieval → Extract → [Requirements extracted]
                ↓
            Verify → [All requirements rejected]
                ↓
            has_sufficient_evidence = false
                ↓
            Finalize (skip composition)
                ↓
            Output: "No authoritative requirement found in provided sources."
                    + rejection reasons
                    + missing_evidence list
```

### Path 3: Quality Review Fails
```
Compose → Quality Review → [score < 7.0]
            ↓
        revision_count < 2?
            ↓ YES
        Revise Composition
            ↓
        Quality Review again
            ↓
        If still fails after 2 revisions → Finalize with low score
```

---

## Data Lineage (Audit Trail)

```
Retrieved Chunks (20)
    ↓
    ├─ Statute Chunks (10) ──→ Extracted Statute Requirements (2)
    │                               ↓
    │                          Verified: 2 passed, 0 rejected
    │                               ↓
    │                          Used in Answer: 2
    │
    └─ Policy Chunks (10) ──→ Extracted Policy Requirements (3)
                                    ↓
                               Verified: 2 passed, 1 rejected
                                    ↓
                               Used in Answer: 2

Final Answer: 4 requirement references [REQ-S001, REQ-S002, REQ-P001, REQ-P002]
```

---

## Key Guarantees

1. **No Hallucination**: Every statement in final_answer references verified evidence
2. **Traceability**: Every requirement traces back to exact quote and chunk
3. **Auditability**: Complete lineage from retrieved chunks to final answer
4. **Fail-Safe**: System returns "No evidence" rather than hallucinate
5. **Determinism**: Extraction and verification use temperature=0.0
6. **Grounding**: All requirements pass explicit grounding verification

---

## Comparison: Evidence-First vs Legacy Pipeline

| Stage | Evidence-First | Legacy |
|-------|----------------|--------|
| **Stage 2** | Extract verbatim quotes | Free-form statute analysis |
| **Stage 3** | Verify grounding gate | Free-form policy analysis |
| **Stage 4** | Compose from verified evidence | Free-form synthesis |
| **Grounding** | Explicit with requirement IDs | Implicit (no references) |
| **Auditability** | Full audit trail with rejections | No rejection tracking |
| **Fail-Safe** | "No evidence" if verification fails | May hallucinate |
| **Traceability** | Requirement ID → Quote → Chunk | No explicit lineage |
| **Determinism** | High (temp=0.0 for extract/verify) | Low (temp=0.2-0.3) |

---

## Usage

### Enable Evidence-First Pipeline:
```python
orchestrator = CurationOrchestrator(use_evidence_pipeline=True)
result = orchestrator.execute(question_data)
```

### Enable Legacy Pipeline (backward compatibility):
```python
orchestrator = CurationOrchestrator(use_evidence_pipeline=False)
result = orchestrator.execute(question_data)
```

### API Integration:
The pipeline selection can be controlled via environment variable or API parameter.

---

**Workflow Status**: ✅ Implemented
**Test Script**: `scripts/test_evidence_pipeline.py`
**Example Output**: `EXAMPLE_AUDIT_TRAIL.json`
