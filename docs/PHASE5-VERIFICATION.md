# Phase 5 Verification Guide - Retrieval Engine

This guide provides step-by-step verification of the Phase 5 (Retrieval Engine) implementation.

## Pre-Verification Checklist

Before verification, ensure:
- [ ] All Phase 1-4 implementations are in place
- [ ] `pytest` is available: `python -m pytest --version`
- [ ] FAQ data exists at `data/faq.json`
- [ ] Ollama is accessible at configured URL (for integration testing)
- [ ] Qdrant is accessible at configured URL (for integration testing)

## Test Execution

### Step 1: Run Unit Tests

```bash
# Run only Phase 5 unit tests
python -m pytest tests/test_retriever.py -v

# Expected output:
# ===== 15 passed in X.XXs =====
```

**What's Tested**:
- Question embedding
- Vector search
- Threshold evaluation
- Error handling
- End-to-end pipeline

### Step 2: Run Integration Tests

```bash
# Run Phase 5 integration tests
python -m pytest tests/test_retrieval_integration.py -v

# Expected output:
# ===== 15 passed in X.XXs =====
```

**What's Tested**:
- Real FAQ data loading
- Configuration variations
- Data flow correctness
- Semantic behavior

### Step 3: Run All Project Tests

```bash
# Run all tests (Phase 1-5)
python -m pytest tests/ -v

# Expected output:
# ===== 67 passed in X.XXs =====
```

**Coverage**:
- Phase 1 (Foundation): 7 tests
- Phase 2 (FAQ Domain): 6 tests
- Phase 3 (Clients): 10 tests
- Phase 4 (Ingestion): 7 tests
- Phase 5 (Retrieval): 30 tests
- **Total: 67 tests**

### Step 4: Check Test Coverage

```bash
# Run tests with coverage report
python -m pytest tests/ --cov=app --cov-report=term-missing

# Expected: High coverage on:
# app/domain/retrieval_result.py
# app/services/retriever.py
# app/services/vector_store_service.py
```

## Functional Verification

### Step 5: Test Retriever Factory

```python
#!/usr/bin/env python
"""Test Retriever.from_settings() factory."""

from app.config import get_settings
from app.services import Retriever

settings = get_settings()
retriever = Retriever.from_settings(settings)

print("✓ Retriever created successfully")
print(f"  - Top-K: {retriever.top_k}")
print(f"  - Threshold: {retriever.score_threshold}")
print(f"  - Ollama client: {retriever.ollama_client is not None}")
print(f"  - Qdrant client: {retriever.qdrant_client is not None}")
```

**Expected Output**:
```
✓ Retriever created successfully
  - Top-K: 3
  - Threshold: 0.7
  - Ollama client: True
  - Qdrant client: True
```

### Step 6: Test RetrievalResult Domain Model

```python
#!/usr/bin/env python
"""Test RetrievalResult structure."""

from app.domain import FAQEntry, RetrievalResult

# Create a sample FAQ
faq = FAQEntry(
    id="test-001",
    question="How do I reset my password?",
    answer="Click 'Forgot Password' on the login page.",
    tags=("password", "account"),
    category="Account Management"
)

# Create a successful retrieval result
result = RetrievalResult(
    matched_entry=faq,
    score=0.85,
    top_k_results=[(faq, 0.85)],
    retrieved=True
)

print("✓ Successful retrieval result:")
print(f"  - Matched entry ID: {result.matched_entry.id}")
print(f"  - Score: {result.score}")
print(f"  - Retrieved: {result.retrieved}")
print(f"  - Top-K results count: {len(result.top_k_results)}")

# Create a fallback result
fallback = RetrievalResult(
    matched_entry=None,
    score=0.45,
    top_k_results=[(faq, 0.45)],
    retrieved=False
)

print("\n✓ Fallback retrieval result:")
print(f"  - Matched entry: {fallback.matched_entry}")
print(f"  - Score: {fallback.score}")
print(f"  - Retrieved: {fallback.retrieved}")
```

**Expected Output**:
```
✓ Successful retrieval result:
  - Matched entry ID: test-001
  - Score: 0.85
  - Retrieved: True
  - Top-K results count: 1

✓ Fallback retrieval result:
  - Matched entry: None
  - Score: 0.45
  - Retrieved: False
```

### Step 7: Test Error Handling

```python
#!/usr/bin/env python
"""Test error handling."""

from app.services import Retriever, RetrieverError
from unittest.mock import MagicMock

# Create retriever with mock clients
ollama_mock = MagicMock()
qdrant_mock = MagicMock()

retriever = Retriever(
    ollama_client=ollama_mock,
    qdrant_client=qdrant_mock,
    top_k=3,
    score_threshold=0.70
)

# Test 1: Empty question rejection
print("Test 1: Empty question rejection")
try:
    retriever.retrieve("   ")
    print("  ✗ Should have raised RetrieverError")
except RetrieverError as e:
    print(f"  ✓ Correctly rejected: {e}")

# Test 2: Embedding error wrapping
print("\nTest 2: Embedding error wrapping")
from app.infrastructure import OllamaClientError
ollama_mock.embed_text.side_effect = OllamaClientError("Model not found")

try:
    retriever.retrieve("How do I reset my password?")
    print("  ✗ Should have raised RetrieverError")
except RetrieverError as e:
    if "Failed to embed question" in str(e):
        print(f"  ✓ Correctly wrapped: {e}")
    else:
        print(f"  ✗ Wrong error message: {e}")
```

**Expected Output**:
```
Test 1: Empty question rejection
  ✓ Correctly rejected: Question must not be empty

Test 2: Embedding error wrapping
  ✓ Correctly wrapped: Failed to embed question: Model not found
```

### Step 8: Test Configuration Variations

```python
#!/usr/bin/env python
"""Test different retriever configurations."""

from app.services import Retriever
from app.domain import FAQEntry, RetrievalResult
from unittest.mock import MagicMock

faq = FAQEntry(
    id="test-001",
    question="Test",
    answer="Test answer"
)

ollama = MagicMock()
qdrant = MagicMock()

# Test different thresholds
print("Testing threshold configurations:")

thresholds = [0.50, 0.70, 0.90]
for threshold in thresholds:
    retriever = Retriever(
        ollama_client=ollama,
        qdrant_client=qdrant,
        top_k=3,
        score_threshold=threshold
    )

    # Score at 0.75 should match for 0.50 and 0.70, but not 0.90
    score = 0.75
    result = retriever._evaluate_threshold([(faq, score)])

    expected_retrieved = score >= threshold
    print(f"  Score {score} vs Threshold {threshold}: retrieved={result.retrieved} (expected={expected_retrieved})")

    if result.retrieved == expected_retrieved:
        print(f"    ✓ Correct")
    else:
        print(f"    ✗ Incorrect")

# Test different top_k
print("\nTesting top-K configurations:")

faqs = [
    FAQEntry(id=f"faq-{i:03d}", question=f"Q{i}", answer=f"A{i}")
    for i in range(5)
]

top_k_values = [1, 3, 5]
for k in top_k_values:
    retriever = Retriever(
        ollama_client=ollama,
        qdrant_client=qdrant,
        top_k=k,
        score_threshold=0.70
    )
    print(f"  Top-K = {k}: retriever.top_k = {retriever.top_k} ✓")
```

**Expected Output**:
```
Testing threshold configurations:
  Score 0.75 vs Threshold 0.50: retrieved=True (expected=True)
    ✓ Correct
  Score 0.75 vs Threshold 0.70: retrieved=True (expected=True)
    ✓ Correct
  Score 0.75 vs Threshold 0.90: retrieved=False (expected=False)
    ✓ Correct

Testing top-K configurations:
  Top-K = 1: retriever.top_k = 1 ✓
  Top-K = 3: retriever.top_k = 3 ✓
  Top-K = 5: retriever.top_k = 5 ✓
```

## Integration Verification (Optional - requires Ollama + Qdrant)

### Step 9: Load Real FAQ Data

```python
#!/usr/bin/env python
"""Load and inspect real FAQ data."""

from app.repositories import FAQRepository
from app.config import get_settings

settings = get_settings()
repo = FAQRepository.from_settings(settings)
faqs = repo.list_entries()

print(f"✓ Loaded {len(faqs)} FAQ entries")
for i, faq in enumerate(faqs[:3], 1):
    print(f"\n  FAQ {i}:")
    print(f"    ID: {faq.id}")
    print(f"    Question: {faq.question[:50]}...")
    print(f"    Tags: {faq.tags}")
    print(f"    Category: {faq.category}")
```

**Expected Output**:
```
✓ Loaded 10 FAQ entries

  FAQ 1:
    ID: faq-01-services-overview
    Question: Welche IT-Dienstleistungen bieten Sie an?...
    Tags: ('it-services', 'support', 'cloud', 'security')
    Category: services

  FAQ 2:
    ID: faq-02-support-response-times
    Question: Wie schnell reagiert Ihr Support-Team?...
    Tags: ('support', 'response-time')
    Category: support
    ...
```

### Step 10: Verify Data Flow (With Mock Clients)

```python
#!/usr/bin/env python
"""Verify complete data flow with mock clients."""

from app.services import Retriever
from app.domain import FAQEntry, RetrievalResult
from app.infrastructure import QdrantSearchResult
from unittest.mock import MagicMock

# Create mock clients
ollama_mock = MagicMock()
qdrant_mock = MagicMock()

# Create retriever
retriever = Retriever(
    ollama_client=ollama_mock,
    qdrant_client=qdrant_mock,
    top_k=3,
    score_threshold=0.70
)

# Setup mock return values
test_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
ollama_mock.embed_text.return_value = test_vector

faq = FAQEntry(
    id="faq-001",
    question="How do I reset my password?",
    answer="Click 'Forgot Password' on the login page."
)

search_result = QdrantSearchResult(
    id="faq-001",
    score=0.88,
    payload=faq.to_payload()
)
qdrant_mock.search.return_value = [search_result]

# Run retrieval
question = "How do I reset my password?"
result = retriever.retrieve(question)

# Verify data flow
print("✓ Complete retrieval pipeline executed")
print(f"  - Question: {question}")
print(f"  - Embedding vector length: {len(test_vector)}")
print(f"  - Qdrant search called: {qdrant_mock.search.called}")
print(f"  - Result matched: {result.matched_entry is not None}")
print(f"  - Result score: {result.score}")
print(f"  - Result retrieved: {result.retrieved}")

# Verify method calls
print("\n✓ Method calls verified:")
print(f"  - embed_text called: {ollama_mock.embed_text.called}")
print(f"  - search called: {qdrant_mock.search.called}")

if result.matched_entry and result.matched_entry.id == "faq-001":
    print("  ✓ Correct FAQ matched")
```

**Expected Output**:
```
✓ Complete retrieval pipeline executed
  - Question: How do I reset my password?
  - Embedding vector length: 5
  - Qdrant search called: True
  - Result matched: True
  - Result score: 0.88
  - Result retrieved: True

✓ Method calls verified:
  - embed_text called: True
  - search called: True
  ✓ Correct FAQ matched
```

## Checklist for Phase 5 Completion

- [ ] All 30 new tests pass
- [ ] All 67 total tests pass
- [ ] Retriever factory method works
- [ ] RetrievalResult immutability verified
- [ ] Error handling works correctly
- [ ] Threshold evaluation works at boundaries
- [ ] Configuration variations tested
- [ ] Real FAQ data loads correctly
- [ ] Complete data flow verified
- [ ] Documentation complete

## Troubleshooting

### Issue: Tests fail with import errors

**Solution**: Check that `app/domain/__init__.py` and `app/services/__init__.py` exports are correct:

```bash
python -c "from app.domain import RetrievalResult; print('OK')"
python -c "from app.services import Retriever, RetrieverError; print('OK')"
```

### Issue: Mocking doesn't work in tests

**Solution**: Ensure MagicMock is used properly:

```python
from unittest.mock import MagicMock

mock = MagicMock()
mock.method.return_value = [...]
mock.method.side_effect = Exception(...)
```

### Issue: RetrievalResult structure validation fails

**Solution**: Check that all required fields are provided:

```python
from app.domain import RetrievalResult, FAQEntry

result = RetrievalResult(
    matched_entry=faq,        # FAQEntry or None
    score=0.85,              # float
    top_k_results=[...],     # Sequence[tuple[FAQEntry, float]]
    retrieved=True           # bool
)
```

## Next Steps

After Phase 5 verification passes:

1. **Phase 6 (Answer Generation)**
   - Takes RetrievalResult from Phase 5
   - Builds grounded prompt from matched FAQ
   - Generates answer via OllamaClient
   - Handles fallback messages

2. **Phase 7 (Chat Application Service)**
   - Orchestrates retrieval and generation
   - Handles errors and timeouts
   - Returns structured response

3. **Phase 8 (Terminal UI)**
   - Displays retrieval results
   - Shows confidence scores
   - Handles fallback messaging

---

**Status**: Phase 5 Ready for Integration ✅
