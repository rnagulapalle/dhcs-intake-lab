# BHT Platform Phase 2 - Retrieval Service

## Overview

Phase 2 upgrades the Phase 0 retrieval shim to a centralized RetrievalService with canonical citations and full instrumentation.

**Key Changes in Phase 2:**
- **Canonical Citation Schema**: Stable contract for all retrieval results
- **Centralized Service**: Unified search API with singleton pattern
- **Full Instrumentation**: latency_ms, cache_hit, n_results in all audit logs
- **Backward Compatible**: Raw results still available, citations additive

## Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `BHT_RETRIEVAL_CACHE_ENABLED` | `false` | Enable result caching |
| `BHT_RETRIEVAL_CACHE_TTL` | `300` | Cache TTL in seconds |
| `BHT_RETRIEVAL_TOP_K` | `5` | Default number of results |

## Citation Schema

The canonical Citation schema provides a stable contract for all retrieval results:

```python
@dataclass
class Citation:
    source_id: str      # Unique identifier for source document
    source_name: str    # Human-readable name (e.g., "DHCS Policy Manual")
    doc_uri: str        # Document URI or path
    chunk_id: str       # Unique identifier for this chunk
    snippet: str        # The actual text content retrieved
    score: float        # Similarity score (0.0-1.0, higher is better)
    metadata: Dict      # Additional source-specific metadata
```

### Example Citation

```json
{
  "source_id": "dhcs_policy_manual_v2024",
  "source_name": "DHCS Behavioral Health Policy Manual",
  "doc_uri": "/docs/policy/bht_manual_2024.pdf",
  "chunk_id": "988_protocol_chunk_3",
  "snippet": "Mobile crisis teams must respond within 60 minutes...",
  "score": 0.89,
  "metadata": {
    "section": "Crisis Response Protocol",
    "category": "protocol",
    "version": "2024.1"
  }
}
```

## Usage

### Basic Search with Citations

```python
from platform.retrieval_service import get_default_retrieval_service

# Get singleton service
service = get_default_retrieval_service()

# Search with citations
result = service.search("mobile crisis response time", n_results=5)

# Access canonical citations (Phase 2)
for citation in result.citations:
    print(f"{citation.source_name}: {citation.snippet[:100]}...")
    print(f"  Score: {citation.score:.2f}")
    print(f"  Source: {citation.doc_uri}")

# Or access raw results (backward compatibility)
for doc in result.results:
    print(doc["content"])
```

### Search with Filtering

```python
# Search with similarity threshold
result = service.search(
    "staffing requirements",
    n_results=10,
    similarity_threshold=0.6  # Only results with score >= 0.6
)

# Search statutes only
statute_result = service.search_statutes(
    "documentation requirements",
    n_results=10,
    similarity_threshold=0.5
)

# Search policies (excludes Table of Contents by default)
policy_result = service.search_policies(
    "crisis intervention",
    n_results=10,
    exclude_toc=True
)
```

### Audit Context Integration

```python
from platform.audit_context import AuditContext

# Create audit context
with AuditContext.create(workflow_id="curation", tenant_id="county_la") as ctx:
    result = service.search("language access", audit_context=ctx)

    # Audit trail includes retrieval logs
    for entry in ctx.get_audit_trail():
        if entry["type"] == "retrieval":
            print(f"Query: {entry['query_length']} chars")
            print(f"Results: {entry['n_results']}")
            print(f"Latency: {entry['latency_ms']:.2f}ms")
```

## Instrumentation

All retrieval operations are automatically instrumented:

```json
{
  "type": "retrieval",
  "trace_id": "abc-123",
  "request_id": "def-456",
  "workflow_id": "curation",
  "query_length": 45,
  "n_results": 8,
  "latency_ms": 125.5,
  "strategy": "semantic",
  "cache_hit": false,
  "success": true
}
```

## Files Changed

### Modified

| File | Changes |
|------|---------|
| [platform/retrieval_service.py](../platform/retrieval_service.py) | Full Phase 2 implementation with Citation schema |
| [tests/platform/test_retrieval_service.py](../tests/platform/test_retrieval_service.py) | Updated tests for Citation and contract verification |

## Validation

### Run Tests

```bash
# Run retrieval service tests
pytest tests/platform/test_retrieval_service.py -v

# Run all platform tests
pytest tests/platform/ -v
```

### Verify Citation Contract

```python
from platform.retrieval_service import Citation
import json

# Create citation
citation = Citation(
    source_id="test",
    source_name="Test",
    doc_uri="/test",
    chunk_id="c1",
    snippet="Test content",
    score=0.9
)

# Verify JSON serializable
json_str = json.dumps(citation.to_dict())
assert json_str is not None

# Verify all fields present
d = citation.to_dict()
assert all(k in d for k in ["source_id", "source_name", "doc_uri", "chunk_id", "snippet", "score", "metadata"])
```

### Verify Backward Compatibility

```python
from platform.retrieval_service import RetrievalServiceShim, RetrievalService

# RetrievalServiceShim is an alias for RetrievalService
assert RetrievalServiceShim is RetrievalService

# Old code using RetrievalServiceShim continues to work
service = RetrievalServiceShim()
result = service.search("test")

# results field still available (Phase 0 compatibility)
for doc in result.results:
    print(doc["content"])
```

## Rollback

Phase 2 is fully backward compatible. To disable new features:

1. **Use raw results instead of citations** (no code change needed)
2. **Disable caching** (already disabled by default)

## Risks

### Low Risk (Default Behavior)
- Citations are additive metadata
- Raw results unchanged
- Caching disabled by default
- No behavior change to search ranking

### Mitigation
- Extensive test coverage for Citation schema
- JSON serialization verified in contract tests
- Backward compatibility aliases maintained

## Next Steps

- Phase 3: Add model routing and budget enforcement
- Phase 4: Add kill switches and degradation modes
- Future: Hybrid search (semantic + keyword) strategy
