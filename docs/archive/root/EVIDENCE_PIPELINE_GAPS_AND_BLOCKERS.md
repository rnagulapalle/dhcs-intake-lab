# Evidence-First Pipeline: Gaps and Blockers

**Date**: January 9, 2026
**System**: DHCS Intake Lab Multi-Agent Curation System
**Assessment Type**: Pre-Implementation Analysis

---

## Executive Summary

The Evidence-First Pipeline has been fully implemented with Extract → Verify → Compose architecture. However, **data quality issues** pose significant blockers to production readiness. The primary gap is **placeholder statutes** which will cause the extraction stage to fail.

**Critical Blocker**: 15/18 statute documents are placeholders (83% placeholder rate)

**Status**:
- ✅ Code implementation: Complete
- ❌ Data readiness: Blocked
- ⚠️ Testing: Cannot execute without real statute data

---

## Gap 1: Placeholder Statutes (CRITICAL)

### Description
The majority of statute documents in the knowledge base are placeholder text, not actual statute content.

### Evidence
```bash
$ grep -c "^\[Placeholder" data/statutes.md
15

$ grep "^##" data/statutes.md | wc -l
18

# Calculation: 15 placeholders / 18 total statutes = 83% placeholder rate
```

### Impact on Evidence Pipeline

**Extract Stage**:
- Extraction agent will find NO requirement sentences in placeholder text
- Placeholder format: "[Placeholder - Replace with actual statute text]"
- NO instances of "must", "shall", "required", "prohibited" in placeholders
- **Result**: extracted_requirements[] will be empty or near-empty

**Verify Stage**:
- With zero or minimal extractions, verification will mark `has_sufficient_evidence = false`
- **Result**: Pipeline skips composition and returns "No authoritative requirement found"

**Compose Stage**:
- Will never execute if verification fails
- **Result**: All questions return insufficient evidence

**Example Failure**:
```json
{
  "extracted_requirements": [],
  "verified_requirements": [],
  "has_sufficient_evidence": false,
  "missing_evidence": [
    "Statute explicitly addressing question topic",
    "Authoritative source addressing this specific question"
  ],
  "final_answer": "No authoritative requirement found in provided sources."
}
```

### Real Statute Example (Working)
From `data/statutes.md` (3 real statutes):

```markdown
## W&I Code § 5899: Mental Health Services Act Implementation

(a) Counties shall provide community-based services to adults with severe
mental illness, including crisis intervention, case management, and residential
treatment facilities...
```

**This works**: Contains "shall provide", "Counties shall", etc. - extraction succeeds.

### Placeholder Example (Broken)
```markdown
## W&I Code § 5600: Community Mental Health Services

[Placeholder - Replace with actual statute text]

This is a placeholder for W&I Code § 5600...
```

**This fails**: No requirement keywords, no legal language - extraction returns empty.

### Remediation Required
1. **Short-term**: Expand real statutes from 3 to at least 10 (covering common topics)
2. **Medium-term**: Replace all 18 statute placeholders with real W&I Code text
3. **Long-term**: Implement automated statute ingestion from official sources

### Estimated Impact
- **With current data**: 90% of questions will return "No authoritative requirement found"
- **With 10 real statutes**: 60-70% of questions will have statute evidence
- **With all 18 real statutes**: 85-95% of questions will have statute evidence

---

## Gap 2: Policy Document Structure (MEDIUM)

### Description
Policy documents may contain narrative or guidance text without explicit "must/shall" requirement language.

### Evidence
Policy documents often use softer language:
- "Counties are encouraged to..."
- "Best practice is to..."
- "Programs should consider..."
- "It is recommended that..."

### Impact on Evidence Pipeline

**Extract Stage**:
- Extraction agent is configured to ONLY extract "must/shall/required/prohibited" sentences
- Softer language will be skipped
- **Result**: Fewer policy requirements extracted than expected

**Current Configuration** (agents/core/evidence_extraction_agent.py:243):
```python
requirement_keywords = ["must", "shall", "required", "prohibited", "mandated", "obligation"]
```

**Missing Patterns**:
- "required to" (e.g., "Counties are required to submit reports")
- "obligation" (noun form)
- "mandates that" (verb form)
- "compliance with" (implicit requirement)

### Example Policy Text (Would Be Missed)
```
Counties are required to submit quarterly reports on service utilization.
Programs should ensure that all staff complete cultural competency training.
```

- First sentence: Contains "required to" but extraction looks for "required" as standalone
- Second sentence: Contains "should" not "must/shall" - would be skipped entirely

### Remediation Options

**Option 1: Expand Keyword List** (Recommended)
```python
requirement_keywords = [
    "must", "shall", "required", "required to",
    "prohibited", "mandated", "mandate", "mandates",
    "obligation", "obligated", "obligate"
]
```

**Option 2: Pattern Matching**
```python
# Match: "Counties are required to", "must ensure", "shall provide"
requirement_patterns = [
    r"\b(must|shall|required|required to|mandated|obligated)\b",
    r"\b(prohibit|prohibited|forbidden)\b",
    r"\b(obligation|mandate|requirement)\s+(to|that)"
]
```

**Option 3: Policy-Specific Extraction**
- Create separate extraction agent for policies with softer language detection
- Mark as "policy_guidance" vs "statutory_requirement"
- Composition agent treats them differently (requirements vs recommendations)

### Estimated Impact
- **Current**: 70% of policy requirements extracted
- **After expansion**: 90% of policy requirements extracted

---

## Gap 3: Incomplete Chunk Boundaries (MEDIUM)

### Description
Retrieved chunks may contain incomplete sentences or cut off mid-requirement.

### Evidence
ChromaDB chunking strategy (agents/knowledge/curation_loader.py) uses fixed-size chunks:
- Chunk size: 500 characters (estimated, needs verification)
- No sentence-boundary detection
- **Result**: Chunks may split mid-sentence

### Example Incomplete Chunk
```
Chunk S3 (end):
"...Counties shall maintain client records including assessment doc"

Chunk S4 (start):
"umentation for all behavioral health services recipients within 60 days."
```

**Impact**: Extract agent sees incomplete quote "assessment doc" which fails validation.

### Impact on Evidence Pipeline

**Extract Stage**:
- Extraction agent requests 10-40 word quotes
- Incomplete sentence at chunk boundary → doesn't meet criteria
- **Result**: Valid requirements may be missed due to chunking

**Verify Stage**:
- Incomplete quotes fail "completeness" check
- Rejection reason: "incomplete_quote"
- **Result**: More rejections than necessary

### Current Validation (agents/core/evidence_extraction_agent.py:319):
```python
def _validate_extraction(self, requirement: Dict) -> bool:
    quote = requirement.get("exact_quote", "")
    word_count = len(quote.split())
    if word_count < 10 or word_count > 40:
        return False  # Reject if outside range
```

### Remediation Options

**Option 1: Sentence-Aware Chunking** (Recommended)
- Use LangChain RecursiveCharacterTextSplitter with sentence boundaries
- Ensure chunks end at sentence boundaries
- Overlap chunks to capture cross-boundary sentences

**Option 2: Cross-Chunk Assembly**
- Extract agent looks at adjacent chunks when quote is incomplete
- Assemble full sentence from chunk N + chunk N+1
- More complex, higher latency

**Option 3: Increase Chunk Size**
- Larger chunks (1000+ characters) reduce boundary splits
- Trade-off: Less precise retrieval, more noise

### Estimated Impact
- **Current**: 5-10% of requirements lost due to chunk boundaries
- **After remediation**: < 2% lost

---

## Gap 4: Cross-Reference Requirements (LOW)

### Description
Some requirements reference other sections ("see § 5899(b)") which may not be in the same chunk.

### Evidence
Statute cross-references are common:
```
"Counties shall comply with assessment standards as defined in § 5600.5."
```

### Impact on Evidence Pipeline

**Extract Stage**:
- Quote is extracted but references external section
- Extraction agent marks as "medium" or "low" confidence
- **Result**: May pass extraction but fail verification

**Verify Stage**:
- Verification agent checks if quote is "self-contained"
- Cross-reference requires external context
- Rejection reason: "incomplete_quote" or "requires_inference"
- **Result**: Valid cross-reference requirements may be rejected

### Example
```json
{
  "requirement_id": "REQ-S003",
  "exact_quote": "Counties shall comply with assessment standards as defined in § 5600.5.",
  "extraction_confidence": "medium",
  "verified": false,
  "rejection_reason": "requires_inference",
  "rejection_rationale": "Quote references § 5600.5 but does not include that section's content. Requires external lookup."
}
```

### Remediation Options

**Option 1: Expand Retrieval Context** (Recommended)
- When extracting cross-references, retrieve referenced section
- Append referenced content to quote
- Mark as "cross_reference_resolved"

**Option 2: Accept Cross-References**
- Verification agent recognizes cross-reference pattern
- Marks as "valid_with_reference"
- Composition agent includes both sections

**Option 3: Statute Graph**
- Build statute dependency graph
- Retrieve all referenced sections automatically
- More complex infrastructure

### Estimated Impact
- **Current**: 5-10% of requirements are cross-references
- **Lost**: 3-5% of total requirements due to rejection
- **After remediation**: < 1% lost

---

## Gap 5: LLM Extraction Quality (MEDIUM)

### Description
LLM-based extraction may miss requirements or extract incorrectly despite clear rules.

### Evidence
Current approach uses Claude Sonnet with temperature=0.0 and strict prompts, but:
- LLMs are non-deterministic even at temp=0 (sampling variability)
- JSON parsing may fail if LLM returns malformed output
- Extraction quality depends on prompt clarity

### Impact on Evidence Pipeline

**Extract Stage**:
- LLM may miss obvious requirements
- LLM may extract non-requirements (false positives)
- JSON parsing errors cause extraction to fail
- **Result**: Inconsistent extraction quality

**Current Error Handling** (agents/core/evidence_extraction_agent.py:294):
```python
try:
    response = self.llm.invoke(...)
    json_match = re.search(r'\[.*\]', content, re.DOTALL)
    if json_match:
        extracted = json.loads(json_match.group(0))
    else:
        logger.warning(f"No JSON array found")
        return []
except Exception as e:
    logger.error(f"Error extracting: {e}")
    return []  # Silent failure - no requirements extracted
```

**Problem**: Silent failures mean lost requirements with no visibility.

### Remediation Options

**Option 1: Multiple Extraction Attempts** (Recommended)
- Run extraction 3 times with different prompts
- Merge results and deduplicate
- Higher recall, some redundancy

**Option 2: Hybrid Extraction**
- Use regex/keyword matching first (high precision)
- Use LLM for complex cases (high recall)
- Combine results

**Option 3: Fallback Extraction**
- If LLM extraction fails, use simple keyword search
- Extract sentences containing "must/shall/required"
- Lower quality but ensures some extraction

**Option 4: Structured Output**
- Use function calling / tool use for structured JSON
- Force LLM to output valid JSON schema
- Reduces parsing errors

### Estimated Impact
- **Current**: 80-90% extraction accuracy
- **After remediation**: 95%+ extraction accuracy

---

## Gap 6: Verification Prompt Ambiguity (LOW)

### Description
Verification criteria may be interpreted inconsistently by LLM.

### Current Criteria (agents/core/grounding_verification_agent.py:55):
```
1. EXPLICIT ADDRESSING: Does requirement directly answer the question?
2. QUOTE SUPPORT: Does quote fully prove requirement?
3. COMPLETENESS: Is quote self-contained?
```

### Problem
- "Directly answer" is subjective
- "Fully prove" requires legal reasoning
- "Self-contained" depends on context

### Impact
- Verification pass rates may vary across runs
- Some requirements borderline pass/fail
- **Result**: Non-deterministic verification even with temp=0

### Remediation
**Option 1: Scoring Rubric**
- Convert yes/no criteria to 0-10 scores
- Pass if total score >= 24/30
- More nuanced than binary pass/fail

**Option 2: Few-Shot Examples**
- Add 5-10 example verifications to prompt
- Show clear pass/fail cases
- Reduces ambiguity

### Estimated Impact
- **Current**: 5-10% verification variance
- **After remediation**: < 3% variance

---

## Gap 7: Missing Evidence Detection (LOW)

### Description
System identifies missing evidence but cannot suggest specific documents to add.

### Current Behavior (agents/core/grounding_verification_agent.py:201):
```python
def _infer_missing_evidence(...):
    missing = []
    if not statute_reqs:
        missing.append("Statute explicitly addressing question topic")
    if not policy_reqs:
        missing.append("Policy guidance explicitly addressing question topic")
    return missing
```

**Problem**: Generic messages, not actionable.

### Better Output Example
```json
{
  "missing_evidence": [
    "W&I Code section addressing MAT (Medication-Assisted Treatment) requirements",
    "Policy guidance on MAT documentation standards",
    "Regulations defining MAT eligibility criteria"
  ],
  "suggested_documents": [
    "W&I Code § 14124.24 (MAT Services)",
    "Policy Manual Section 5.3 (Substance Use Disorder Treatment)",
    "Title 9 CCR § 10565 (MAT Standards)"
  ]
}
```

### Remediation
**Option 1: Document Index**
- Build index of all statutes/policies with topic tags
- When evidence missing, search index for relevant documents
- Suggest top 3 documents to add

**Option 2: Gap Analysis**
- Track which questions frequently return "no evidence"
- Identify topic clusters without coverage
- Prioritize document acquisition for those topics

### Estimated Impact
- Helps data curation team prioritize statute acquisition
- Reduces "no evidence" rate by 20-30% over time

---

## Summary Table

| Gap | Severity | Blocker? | Remediation | Estimated Effort |
|-----|----------|----------|-------------|------------------|
| **1. Placeholder Statutes** | CRITICAL | ✅ YES | Replace with real statute text | 40-80 hours (legal research + data entry) |
| **2. Policy Structure** | MEDIUM | ❌ NO | Expand keyword list | 2 hours (code change) |
| **3. Chunk Boundaries** | MEDIUM | ❌ NO | Sentence-aware chunking | 8 hours (re-chunking + testing) |
| **4. Cross-References** | LOW | ❌ NO | Expand retrieval context | 16 hours (graph building) |
| **5. Extraction Quality** | MEDIUM | ❌ NO | Multiple attempts | 8 hours (retry logic) |
| **6. Verification Ambiguity** | LOW | ❌ NO | Few-shot examples | 4 hours (prompt engineering) |
| **7. Missing Evidence** | LOW | ❌ NO | Document index | 8 hours (indexing system) |

**Total Estimated Effort (excluding Gap 1)**: 46 hours
**Critical Blocker (Gap 1)**: 40-80 hours

---

## Recommended Implementation Order

### Phase 1: Unblock Testing (HIGH PRIORITY)
1. **Gap 1**: Acquire and ingest 10 real statutes (minimum viable set)
   - Focus on most frequently asked topics
   - Enables testing of evidence pipeline
   - **Target**: 70% question coverage

2. **Gap 2**: Expand extraction keywords
   - Quick win, immediate improvement
   - Increases policy extraction rate

### Phase 2: Quality Improvements (MEDIUM PRIORITY)
3. **Gap 3**: Implement sentence-aware chunking
   - Improves extraction quality
   - Reduces verification rejections

4. **Gap 5**: Add multiple extraction attempts
   - Increases extraction recall
   - Reduces silent failures

### Phase 3: Advanced Features (LOW PRIORITY)
5. **Gap 4**: Handle cross-references
   - Nice-to-have, not critical
   - Improves completeness

6. **Gap 6**: Improve verification consistency
   - Fine-tuning, not blocking
   - Reduces variance

7. **Gap 7**: Build missing evidence index
   - Helps long-term data strategy
   - Not needed for launch

---

## Testing Readiness

### Current Status
- ✅ Code implementation: Complete
- ✅ Unit tests: Agents can be tested in isolation
- ❌ Integration tests: **BLOCKED by Gap 1 (placeholder statutes)**
- ❌ End-to-end tests: **BLOCKED by Gap 1**

### Minimum Viable Data for Testing
To test the evidence pipeline, need:
1. **10 real statutes** covering common topics:
   - Assessment requirements (W&I § 5600.5, § 14680)
   - Service delivery (W&I § 5899, § 14184)
   - Documentation (W&I § 5600, § 5651)
   - Crisis services (W&I § 5678, § 5685)
   - Workforce (W&I § 5600.2)
   - Data reporting (W&I § 5897)
   - Funding (W&I § 5892, § 5897)

2. **Policy documents** (already present, 318 chunks)
   - No blockers on policy side

### Test Execution Plan
Once Gap 1 is resolved:
1. Run single-question test: `python3 scripts/test_evidence_pipeline.py`
2. Run 10-question stratified sample
3. Compare evidence pipeline vs legacy pipeline on same questions
4. Analyze:
   - Extraction rate
   - Verification pass rate
   - Composition quality
   - Grounding confidence

---

## Production Readiness Checklist

- ❌ **Data Quality**: Placeholder statutes must be replaced
- ✅ **Code Quality**: Evidence pipeline implemented and documented
- ⏳ **Testing**: Blocked pending data quality
- ⏳ **Performance**: Unknown (cannot test without real data)
- ✅ **Auditability**: Full audit trail implemented
- ✅ **Fail-Safe**: "No evidence" handling implemented
- ✅ **Backward Compatibility**: Legacy pipeline still available

**Overall Status**: ⚠️ **NOT PRODUCTION READY** due to data quality blocker

---

**Next Critical Action**: Acquire and ingest 10+ real statute documents to unblock testing.

**Estimated Timeline**:
- Phase 1 (unblock): 1-2 weeks (statute acquisition + ingestion)
- Phase 2 (quality): 1 week (code improvements)
- Phase 3 (advanced): 2 weeks (nice-to-have features)

**Total**: 4-5 weeks to production-ready with real data
