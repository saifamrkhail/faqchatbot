# Phase 6 Verification Guide - Answer Generation

This guide provides step-by-step verification of the Phase 6 (Answer Generation) implementation.

## Pre-Verification Checklist

Before verification, ensure:
- [ ] All Phase 1-5 implementations are in place
- [ ] `pytest` is available: `python -m pytest --version`
- [ ] FAQ data exists at `data/faq.json`
- [ ] Ollama is accessible at configured URL (for testing)

## Test Execution

### Step 1: Run Unit Tests

```bash
# Run only Phase 6 unit tests
python -m pytest tests/test_answer_generator.py -v

# Expected output:
# ===== 16 passed in X.XXs =====
```

**What's Tested**:
- Prompt building with FAQ
- Answer generation
- Fallback behavior
- Error handling

### Step 2: Run Integration Tests

```bash
# Run Phase 6 integration tests
python -m pytest tests/test_answer_generation_integration.py -v

# Expected output:
# ===== 16 passed in X.XXs =====
```

**What's Tested**:
- Real FAQ data loading
- Prompt building variations
- Response model structure
- Semantic behavior

### Step 3: Run All Project Tests

```bash
# Run all tests (Phase 1-6)
python -m pytest tests/ -v

# Expected output:
# ===== 99 passed in X.XXs =====
```

**Coverage**:
- Phase 1-5: 67 tests
- Phase 6: 32 tests (16 unit + 16 integration)
- **Total: 99 tests**

## Functional Verification

### Step 4: Test AnswerGenerator Factory

```python
#!/usr/bin/env python
"""Test AnswerGenerator.from_settings() factory."""

from app.config import get_settings
from app.services import AnswerGenerator

settings = get_settings()
generator = AnswerGenerator.from_settings(settings)

print("✓ AnswerGenerator created successfully")
print(f"  - Ollama client: {generator.ollama_client is not None}")
print(f"  - Prompt template: {generator.prompt_template is not None}")
print(f"  - Fallback message: {generator.fallback_message}")
```

**Expected Output**:
```
✓ AnswerGenerator created successfully
  - Ollama client: True
  - Prompt template: True
  - Fallback message: Leider konnte ich Ihre Frage nicht verstehen.
```

### Step 5: Test PromptTemplate

```python
#!/usr/bin/env python
"""Test PromptTemplate prompt building."""

from app.domain import FAQEntry, PromptTemplate

template = PromptTemplate()
faq = FAQEntry(
    id="test-001",
    question="How do I reset my password?",
    answer="Click 'Forgot Password' on the login page.",
    tags=("password", "account"),
    category="Account Management"
)

prompt = template.build("How do I reset my password?", faq)

print("✓ Prompt built successfully")
print(f"  - Contains question: {'How do I reset' in prompt}")
print(f"  - Contains FAQ question: {faq.question in prompt}")
print(f"  - Contains FAQ answer: {faq.answer in prompt}")
print(f"  - Contains category: {'Account Management' in prompt}")
print(f"  - Contains tags: {'password' in prompt}")

# Print first 200 chars of prompt
print(f"\nPrompt preview:\n{prompt[:200]}...")
```

**Expected Output**:
```
✓ Prompt built successfully
  - Contains question: True
  - Contains FAQ question: True
  - Contains FAQ answer: True
  - Contains category: True
  - Contains tags: True

Prompt preview:
You are a helpful FAQ assistant. Answer the user's question using ONLY
the provided FAQ context. Be concise, factual, and helpful...
```

### Step 6: Test AnswerResponse Structure

```python
#!/usr/bin/env python
"""Test AnswerResponse structure."""

from app.domain import AnswerResponse, FAQEntry

# Create a successful answer response
response = AnswerResponse(
    answer="Generated answer from FAQ",
    confidence=0.85,
    source_faq_id="faq-001",
    is_fallback=False,
    used_retrieval=True
)

print("✓ Retrieved answer response:")
print(f"  - Answer: {response.answer[:30]}...")
print(f"  - Confidence: {response.confidence}")
print(f"  - Source FAQ: {response.source_faq_id}")
print(f"  - Is fallback: {response.is_fallback}")
print(f"  - Used retrieval: {response.used_retrieval}")

# Create a fallback response
fallback = AnswerResponse(
    answer="Leider konnte ich Ihre Frage nicht verstehen.",
    confidence=0.35,
    source_faq_id=None,
    is_fallback=True,
    used_retrieval=False
)

print("\n✓ Fallback response:")
print(f"  - Answer: {fallback.answer}")
print(f"  - Confidence: {fallback.confidence}")
print(f"  - Source FAQ: {fallback.source_faq_id}")
print(f"  - Is fallback: {fallback.is_fallback}")
print(f"  - Used retrieval: {fallback.used_retrieval}")
```

**Expected Output**:
```
✓ Retrieved answer response:
  - Answer: Generated answer from FAQ...
  - Confidence: 0.85
  - Source FAQ: faq-001
  - Is fallback: False
  - Used retrieval: True

✓ Fallback response:
  - Answer: Leider konnte ich Ihre Frage nicht verstehen.
  - Confidence: 0.35
  - Source FAQ: None
  - Is fallback: True
  - Used retrieval: False
```

### Step 7: Test Error Handling

```python
#!/usr/bin/env python
"""Test error handling."""

from app.services import AnswerGenerator, AnswerGeneratorError
from app.domain import PromptTemplate, FAQEntry
from unittest.mock import MagicMock

# Create generator with mock clients
ollama_mock = MagicMock()
template = PromptTemplate()

generator = AnswerGenerator(
    ollama_client=ollama_mock,
    prompt_template=template,
    fallback_message="Fallback message"
)

# Test 1: Empty question rejection
print("Test 1: Empty question rejection")
from app.domain import RetrievalResult
try:
    retrieval = RetrievalResult(
        matched_entry=None,
        score=0.0,
        top_k_results=[],
        retrieved=False
    )
    generator.generate("   ", retrieval)
    print("  ✗ Should have raised AnswerGeneratorError")
except AnswerGeneratorError as e:
    print(f"  ✓ Correctly rejected: {e}")

# Test 2: Ollama error wrapping
print("\nTest 2: Ollama error wrapping")
from app.infrastructure import OllamaClientError
ollama_mock.generate.side_effect = OllamaClientError("Model not found")

faq = FAQEntry(id="test", question="Q", answer="A")
retrieval = RetrievalResult(
    matched_entry=faq,
    score=0.85,
    top_k_results=[(faq, 0.85)],
    retrieved=True
)

try:
    generator.generate("How do I...?", retrieval)
    print("  ✗ Should have raised AnswerGeneratorError")
except AnswerGeneratorError as e:
    if "Failed to generate answer" in str(e):
        print(f"  ✓ Correctly wrapped: {e}")
    else:
        print(f"  ✗ Wrong error message: {e}")

# Test 3: Fallback for non-retrieved
print("\nTest 3: Fallback for non-retrieved result")
retrieval_no_match = RetrievalResult(
    matched_entry=None,
    score=0.30,
    top_k_results=[],
    retrieved=False
)

result = generator.generate("Unrelated question?", retrieval_no_match)
print(f"  ✓ Fallback returned: is_fallback={result.is_fallback}")
print(f"  ✓ No source FAQ: source_faq_id={result.source_faq_id}")
```

**Expected Output**:
```
Test 1: Empty question rejection
  ✓ Correctly rejected: Question must not be empty

Test 2: Ollama error wrapping
  ✓ Correctly wrapped: Failed to generate answer: Model not found

Test 3: Fallback for non-retrieved result
  ✓ Fallback returned: is_fallback=True
  ✓ No source FAQ: source_faq_id=None
```

### Step 8: Test Real FAQ Data Integration

```python
#!/usr/bin/env python
"""Test with real FAQ data."""

from app.repositories import FAQRepository
from app.config import get_settings
from app.domain import PromptTemplate

settings = get_settings()
repo = FAQRepository.from_settings(settings)
faqs = repo.list_entries()

template = PromptTemplate()

print(f"✓ Loaded {len(faqs)} FAQ entries")

# Test prompt building with real data
for i, faq in enumerate(faqs[:2], 1):
    prompt = template.build("User question?", faq)
    print(f"\n✓ FAQ {i} prompt:")
    print(f"  - Length: {len(prompt)} chars")
    print(f"  - Contains question: {'User question?' in prompt}")
    print(f"  - Contains FAQ: {faq.question in prompt}")
```

**Expected Output**:
```
✓ Loaded 10 FAQ entries

✓ FAQ 1 prompt:
  - Length: XXX chars
  - Contains question: True
  - Contains FAQ: True

✓ FAQ 2 prompt:
  - Length: XXX chars
  - Contains question: True
  - Contains FAQ: True
```

## Checklist for Phase 6 Completion

- [ ] All 16 unit tests pass
- [ ] All 16 integration tests pass
- [ ] All 99 total tests pass
- [ ] AnswerGenerator factory works
- [ ] PromptTemplate builds correct prompts
- [ ] AnswerResponse structure correct
- [ ] Error handling works
- [ ] Fallback behavior works
- [ ] Real FAQ data integrates
- [ ] Documentation complete

## Troubleshooting

### Issue: Tests fail with import errors

**Solution**: Check that exports are correct:

```bash
python -c "from app.domain import AnswerResponse, PromptTemplate; print('OK')"
python -c "from app.services import AnswerGenerator, AnswerGeneratorError; print('OK')"
```

### Issue: Prompt building fails

**Solution**: Verify PromptTemplate receives proper FAQEntry:

```python
from app.domain import FAQEntry, PromptTemplate

faq = FAQEntry(
    id="test",
    question="Test Q",
    answer="Test A",
    tags=(),
    category=None
)
template = PromptTemplate()
prompt = template.build("User question", faq)
print(prompt[:100])
```

### Issue: AnswerResponse immutability fails

**Solution**: Response is frozen, cannot modify:

```python
from app.domain import AnswerResponse

response = AnswerResponse(
    answer="Answer",
    confidence=0.85,
    source_faq_id="faq-001",
    is_fallback=False,
    used_retrieval=True
)

# This should raise AttributeError
try:
    response.answer = "Modified"
except AttributeError as e:
    print(f"✓ Immutability working: {e}")
```

## Next Steps

After Phase 6 verification passes:

1. **Phase 7 (Chat Application Service)**
   - Orchestrates one full chat turn
   - Combines Retriever + AnswerGenerator
   - Returns structured ChatResponse

2. **Phase 8 (Terminal UI)**
   - Textual interface for user interaction
   - Displays answers with confidence

3. **Phase 9 (Runtime & Deployment)**
   - Docker setup
   - Service orchestration

---

**Status**: Phase 6 Ready for Integration ✅
