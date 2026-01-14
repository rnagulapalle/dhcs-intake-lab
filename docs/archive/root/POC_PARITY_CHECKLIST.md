# POC Parity Checklist: Rishi POC vs Intake-Lab Multi-Agent System

**Date**: January 9, 2026
**Purpose**: Evidence-based audit of functional parity between POC and production system

---

## 1. Input Schema Parity

### POC Behavior (Baseline)
- **Reads**: PreProcessRubric_v0.csv rows
- **Required fields**: IP Question, IP Section, IP Sub-Section, topic_name
- **File**: `data/PreProcessRubric_v0.csv` (392 questions)

### Intake-Lab Status
- **API endpoint**: `POST /curation/process` ([api/main.py:306-346](api/main.py))
- **Request schema** ([api/main.py:114-118](api/main.py)):
  ```python
  class CurationRequest(BaseModel):
      question: str         # ✅ Maps to IP Question
      topic: str           # ✅ Maps to IP Section
      sub_section: str     # ✅ Maps to IP Sub-Section
      category: str        # ✅ Maps to topic_name
  ```

**Status**: ✅ **PARITY ACHIEVED**
**Evidence**: API accepts all 4 POC fields with direct name mapping

---

## 2. Retrieval Parity

### POC Behavior (Baseline)
- **Separate retrieval**: statute_chunks + policy_chunks from ChromaDB
- **Similarity threshold**: Applied during retrieval
- **Chunk counts**: Configurable top_k parameter
- **Two queries**: One for statutes, one for policies

### Intake-Lab Status
- **Retrieval agent**: [agents/core/retrieval_agent.py](agents/core/retrieval_agent.py)
- **Dual query enhancement** (lines 92-94):
  ```python
  enhanced_statute_query = self._enhance_statute_query(question, topic)
  enhanced_policy_query = self._enhance_policy_query(question, topic)
  ```
- **Separate collections** (lines 102, 108):
  - `_retrieve_statutes()` → statute collection
  - `_retrieve_policies()` → policy collection
- **Top-k parameter** (line 88): `top_k = input_data.get("top_k", 10)` (default 10)
- **No explicit similarity threshold**: ChromaDB returns top_k by similarity, but no threshold filtering

**Status**: ⚠️ **PARTIAL PARITY** (similarity threshold missing)
**Gap**: No similarity_score_threshold filtering. POC likely filtered by threshold; intake-lab only uses top_k.
**Evidence**: `rg "similarity_threshold|score.*threshold" agents/core/retrieval_agent.py` returns no matches

---

## 3. Prompt Parity (3-Stage Summarization)

### POC Behavior (Baseline)
- **Stage 1**: statute_summary (identify relevant W&I statutes + requirements from statute_chunks)
- **Stage 2**: policy_summary (extract requirements from policy_chunks)
- **Stage 3**: final_summary (synthesize from statute_summary + policy_summary)

### Intake-Lab Status

#### Stage 1: Statute Analysis
- **Agent**: StatuteAnalystAgent ([agents/core/statute_analyst_agent.py:40-109](agents/core/statute_analyst_agent.py))
- **Output field**: `statute_analysis` (NOT statute_summary)
- **Prompt** (lines 149-202):
  - Identifies relevant W&I Code sections
  - Extracts specific legal requirements
  - Cites statute sections precisely
  - Few-shot examples included
  - Temperature: 0.1
- **Format**: Structured list with Citation + Relevance + Key Requirement
- **INSUFFICIENT EVIDENCE handling** (line 168): "**No directly applicable statutes found in the provided list.**"

#### Stage 2: Policy Analysis
- **Agent**: PolicyAnalystAgent ([agents/core/policy_analyst_agent.py:41-113](agents/core/policy_analyst_agent.py))
- **Output field**: `policy_analysis` (NOT policy_summary)
- **Prompt** (lines 156-220):
  - Markdown-structured output with 5 sections:
    - Key Requirements (mandatory)
    - Recommended Practices (optional)
    - Compliance Guidance
    - Related Policy Sections
    - Ambiguities/Open Questions
  - Temperature: 0.2
  - Max 400 words
- **Extracts** (lines 248-268, 269-288):
  - `key_requirements: List[str]` from "### Key Requirements" section
  - `recommendations: List[str]` from "### Recommended Practices" section

#### Stage 3: Synthesis
- **Agent**: SynthesisAgent ([agents/core/synthesis_agent.py:39-112](agents/core/synthesis_agent.py))
- **Output field**: `final_summary`
- **Prompt** (lines 134-199):
  - Synthesizes statute_analysis + policy_analysis
  - Structured markdown with 5 sections:
    - Bottom Line (1-2 sentence executive summary)
    - Statutory Basis
    - Policy Guidance
    - Action Items for County (2-5 items)
    - Open Questions/Ambiguities
  - Temperature: 0.3
  - Max 300 words
- **Extracts** (lines 237-256):
  - `action_items: List[str]` from "### Action Items for County" section
  - `priority: str` (High/Medium/Low) based on term frequency

**Status**: ⚠️ **FUNCTIONAL PARITY, SCHEMA GAP**
**Gap 1 (naming)**: POC uses `statute_summary`, `policy_summary`; intake-lab uses `statute_analysis`, `policy_analysis`
**Gap 2 (structure)**: POC summaries likely plain text; intake-lab uses structured markdown with sub-sections
**Gap 3 (extras)**: Intake-lab extracts additional fields (key_requirements, recommendations, action_items, priority) not in POC
**Evidence**: Prompt templates in statute_analyst_agent.py:149-202, policy_analyst_agent.py:156-220, synthesis_agent.py:134-199

---

## 4. Output Parity

### POC Behavior (Baseline)
- **Output fields**: statute_summary, policy_summary, final_summary
- **Format**: CSV-based artifact with text columns

### Intake-Lab Status
- **API response** ([api/main.py:333-342](api/main.py)):
  ```python
  return {
      "success": result["success"],
      "final_summary": result["final_summary"],        # ✅ POC parity
      "final_response": result["final_response"],      # ❌ Not in POC
      "action_items": result["action_items"],          # ❌ Not in POC
      "priority": result["priority"],                  # ❌ Not in POC
      "quality_score": result["quality_score"],        # ❌ Not in POC
      "passes_review": result["passes_review"],        # ❌ Not in POC
      "metadata": result["metadata"]                   # ❌ Not in POC
  }
  ```
- **Orchestrator state fields** ([agents/core/curation_orchestrator.py:33-48](agents/core/curation_orchestrator.py)):
  ```python
  statute_analysis: str           # ❌ Different name (was statute_summary)
  policy_analysis: str            # ❌ Different name (was policy_summary)
  final_summary: str              # ✅ POC parity
  action_items: List[str]         # ❌ Not in POC
  priority: str                   # ❌ Not in POC
  quality_score: float            # ❌ Not in POC
  passes_review: bool             # ❌ Not in POC
  ```

**Status**: ❌ **SCHEMA MISMATCH**
**Gap 1**: Missing POC fields `statute_summary`, `policy_summary` (renamed to `statute_analysis`, `policy_analysis`)
**Gap 2**: Extra fields not in POC (action_items, priority, quality_score, passes_review)
**Evidence**: API response schema at api/main.py:333-342, state definition at curation_orchestrator.py:33-48

---

## 5. Grounding (Chunk Citations)

### POC Behavior (Baseline)
- **Expected**: Chunk-ID citations in summaries (e.g., S1, S2, S3 for statute chunks; P1, P2, P3 for policy chunks)
- **Purpose**: Traceability to source documents

### Intake-Lab Status
- **Statute formatting** ([agents/core/statute_analyst_agent.py:111-130](agents/core/statute_analyst_agent.py)):
  ```python
  formatted = f"**Statute Reference {i}** (Relevance: {score:.2f})\n"
  formatted += f"Source: {source}\n"
  formatted += f"Content:\n{content}\n"
  ```
  - Labels chunks as "Statute Reference 1", "Statute Reference 2", etc.
  - **NOT** labeled as S1, S2, S3
- **Policy formatting** ([agents/core/policy_analyst_agent.py:115-139](agents/core/policy_analyst_agent.py)):
  ```python
  formatted = f"**Policy Reference {i}** (Relevance: {score:.2f})\n"
  formatted += f"Source: {source}"
  formatted += f"\nSection: {section}\n"
  formatted += f"Content:\n{content}\n"
  ```
  - Labels chunks as "Policy Reference 1", "Policy Reference 2", etc.
  - **NOT** labeled as P1, P2, P3
- **LLM outputs**: Prompts instruct LLMs to cite statute sections (e.g., "W&I Code § 5899"), but **NO instruction to reference S1/P1 chunk IDs**

**Status**: ❌ **NO PARITY**
**Gap**: No chunk-ID citations (S#, P#) in final summaries. LLMs cite statute sections but not retrieved chunk IDs.
**Evidence**: Grep for `S1|S2|P1|P2|chunk.*id|citation.*chunk` in agent prompts returns no matches

---

## 6. Failure Modes (INSUFFICIENT EVIDENCE)

### POC Behavior (Baseline)
- **Expected**: If retrieval returns no relevant chunks (or low similarity), output "INSUFFICIENT EVIDENCE" instead of hallucinating

### Intake-Lab Status

#### Statute Analysis
- **Explicit handling** ([agents/core/statute_analyst_agent.py:168](agents/core/statute_analyst_agent.py)):
  ```python
  If no statutes are clearly relevant:
  "**No directly applicable statutes found in the provided list.**"
  ```
- **Context formatting** (line 113-114):
  ```python
  if not statute_chunks:
      return "No statute documents retrieved."
  ```

#### Policy Analysis
- **Context formatting** ([agents/core/policy_analyst_agent.py:117-118](agents/core/policy_analyst_agent.py)):
  ```python
  if not policy_chunks:
      return "No policy documents retrieved."
  ```
- **No explicit prompt instruction** for INSUFFICIENT EVIDENCE output

#### Synthesis
- **No explicit handling**: Prompt does not instruct LLM to output "INSUFFICIENT EVIDENCE" if inputs are empty

**Status**: ⚠️ **PARTIAL PARITY**
**Gap**: Statute agent has explicit INSUFFICIENT EVIDENCE handling; policy and synthesis agents do not.
**Evidence**: statute_analyst_agent.py:168, policy_analyst_agent.py:117-118, synthesis_agent.py (no empty-input handling)

---

## 7. Batch Mode (N Questions)

### POC Behavior (Baseline)
- **Expected**: Process N questions from CSV in sequence, output N rows with summaries

### Intake-Lab Status
- **Batch endpoint exists** ([api/main.py:349-404](api/main.py)):
  ```python
  @app.post("/curation/batch")
  async def process_curation_batch(request: CurationBatchRequest):
  ```
- **Input schema** (line 122):
  ```python
  class CurationBatchRequest(BaseModel):
      questions: list[Dict[str, str]]
  ```
- **Implementation** (lines 368-395):
  - Loops through questions
  - Calls orchestrator.execute() for each
  - Returns list of results
- **No CSV I/O**: Accepts JSON, returns JSON (no direct CSV reading/writing)

**Status**: ✅ **FUNCTIONAL PARITY** (JSON-based batch processing)
**Note**: Different format (JSON vs CSV) but same N-question capability
**Evidence**: api/main.py:349-404

---

## 8. Determinism (Temperature, Seeds, Stability)

### POC Behavior (Baseline)
- **Expected**: Same question → same output (deterministic for testing)
- **Likely**: temperature=0 or low, random seed set

### Intake-Lab Status
- **Agent temperatures** (verified in agent __init__ methods):
  - RetrievalAgent: No temperature (vector search is deterministic)
  - StatuteAnalystAgent: temperature=0.1 ([statute_analyst_agent.py:35](agents/core/statute_analyst_agent.py))
  - PolicyAnalystAgent: temperature=0.2 ([policy_analyst_agent.py:36](agents/core/policy_analyst_agent.py))
  - SynthesisAgent: temperature=0.3 ([synthesis_agent.py:34](agents/core/synthesis_agent.py))
  - QualityReviewerAgent: temperature=0.2 ([quality_reviewer_agent.py:33](agents/core/quality_reviewer_agent.py))
- **Temperatures > 0**: Outputs are **NOT deterministic** even with same inputs
- **No seed setting**: No `random.seed()` or model seed parameter found

**Status**: ❌ **NO PARITY**
**Gap**: Non-zero temperatures mean non-deterministic outputs. POC likely used temperature=0 for reproducibility.
**Evidence**: Agent temperature values in __init__ methods (0.1, 0.2, 0.3)

---

## Summary of Gaps (Priority Order)

| # | Gap | Severity | Evidence | Impact |
|---|-----|----------|----------|--------|
| 1 | **Missing output fields**: statute_summary, policy_summary | HIGH | curation_orchestrator.py:33-48 | API returns different schema than POC |
| 2 | **No chunk citations (S#, P#)** in summaries | HIGH | statute_analyst_agent.py:111-130, policy_analyst_agent.py:115-139 | No traceability to source chunks |
| 3 | **No similarity threshold** filtering in retrieval | MEDIUM | retrieval_agent.py (no threshold logic) | May retrieve low-relevance chunks |
| 4 | **Non-deterministic outputs** (temp > 0) | MEDIUM | All agent __init__ methods | Cannot reproduce exact outputs |
| 5 | **Incomplete INSUFFICIENT EVIDENCE** handling | LOW | synthesis_agent.py (no empty-input check) | May hallucinate with no inputs |

---

## Next Steps (Implementation Plan)

### Gap 1: Add POC Output Fields (statute_summary, policy_summary)
**Implementation**:
1. Add fields to CurationState ([agents/core/curation_orchestrator.py:21-61](agents/core/curation_orchestrator.py))
2. Map statute_analysis → statute_summary, policy_analysis → policy_summary
3. Update API response to include both fields ([api/main.py:333-342](api/main.py))

### Gap 2: Add Chunk Citations (S1..Sn, P1..Pn)
**Implementation**:
1. Modify statute/policy chunk formatting to use S1/P1 labels
2. Update prompts to instruct LLMs to reference chunk IDs
3. Validate citations appear in final outputs

### Gap 3: Add Similarity Threshold Filtering
**Implementation**:
1. Add `similarity_threshold` parameter to retrieval_agent.py:_retrieve_statutes/policies
2. Filter results: `[c for c in chunks if c['similarity_score'] >= threshold]`
3. Default threshold: 0.5 (to be tuned)

---

**Checklist Status**: 8/8 items completed
**Overall Parity**: ⚠️ **PARTIAL** (3 HIGH/MEDIUM gaps identified)
**Next Action**: Implement top 3 gaps
