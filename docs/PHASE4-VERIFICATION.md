# Phase 4 Verification Guide

This guide explains how to verify that Phase 4 (Ingestion Pipeline) is working correctly once Phase 2 & 3 implementations from Codex are merged.

## Prerequisites

Before running Phase 4 verification, ensure you have:

1. **Services Running Locally**:
   - Ollama running on `http://localhost:11434`
   - Qdrant running on `http://localhost:6333`

2. **Ollama Models Deployed**:
   - Embedding model: `nomic-embed-text-v2-moe`
   - Generation model: `qwen3.5:2b` (for later phases)

3. **Python Environment**:
   ```bash
   uv sync
   ```

## Verification Steps

### Step 1: Verify Environment & Dependencies

```bash
# Check Python version
python --version
# Should be Python 3.11.x

# Verify dependencies installed
python -c "import aiohttp; import qdrant_client; print('Dependencies OK')"

# Check that services are healthy
python -c "
import asyncio
from app.config import get_settings
from app.infrastructure.ollama_client import OllamaClient
from app.infrastructure.qdrant_client import QdrantClient

async def check():
    settings = get_settings()
    ollama = OllamaClient(settings)
    qdrant = QdrantClient(settings)

    ollama_ok = await ollama.health_check()
    qdrant_ok = qdrant.health_check()

    print(f'Ollama: {\"✓\" if ollama_ok else \"✗\"}')
    print(f'Qdrant: {\"✓\" if qdrant_ok else \"✗\"}')

    await ollama.close()

asyncio.run(check())
"
```

### Step 2: Run Phase 4 Tests

```bash
# Run all Phase 4 tests
python -m pytest tests/test_ingestion_service.py tests/test_ingest_script.py -v

# Expected output: All tests pass
# ============================== 33 passed in X.XXs ==============================

# Run with coverage
python -m pytest tests/test_ingestion_service.py tests/test_ingest_script.py --cov=app --cov-report=term-missing
```

### Step 3: Run the Ingestion Script

```bash
# Basic ingestion with sample FAQ
python scripts/ingest.py

# With verbose logging
python scripts/ingest.py --verbose

# Custom FAQ file
python scripts/ingest.py --faq-file data/faq.json --verbose

# Expected output:
# ======================================================================
# Ingestion Result: 10/10 entries successfully ingested
# ======================================================================
#
# ✓ Ingestion completed successfully
```

### Step 4: Verify Data in Qdrant

```bash
# Connect to Qdrant and verify ingestion
python -c "
from app.config import get_settings
from app.infrastructure.qdrant_client import QdrantClient

settings = get_settings()
client = QdrantClient(settings)

# Check collection exists
exists = client.collection_exists()
print(f'Collection exists: {exists}')

# Try to retrieve a specific FAQ
point = client.get_point('faq_001')
if point:
    print(f'Successfully retrieved FAQ: {point[\"payload\"][\"faq_id\"]}')
    print(f'Question: {point[\"payload\"][\"question\"]}')
"
```

### Step 5: Test Re-ingestion (Idempotency)

```bash
# Run ingestion script twice
python scripts/ingest.py --verbose

# Second run
python scripts/ingest.py --verbose

# Expected: Both runs succeed with same result
# Should show "10/10 entries successfully ingested" both times
# No duplicates created in Qdrant
```

### Step 6: Verify Vector Embeddings

```bash
# Verify embedding dimensions
python -c "
import asyncio
from app.config import get_settings
from app.infrastructure.ollama_client import OllamaClient

async def check():
    settings = get_settings()
    client = OllamaClient(settings)

    dim = await client.get_embedding_dimension()
    print(f'Embedding dimension: {dim}')

    # Test embedding
    embedding = await client.embed_text('How do I reset my password?')
    print(f'Embedding vector length: {len(embedding)}')
    print(f'First 5 values: {embedding[:5]}')

    await client.close()

asyncio.run(check())
"

# Expected output:
# Embedding dimension: 384 (for nomic-embed-text-v2-moe)
# Embedding vector length: 384
# First 5 values: [0.xxx, 0.xxx, ...]
```

### Step 7: Test Phase 2 & 3 Integration

Once Phase 2 & 3 are merged, verify that the real implementations work:

```bash
# Check if Codex's implementations are present
python -c "
from app.domain.faq import FaqEntry
from app.repositories.faq_repository import FaqRepository
from app.infrastructure.ollama_client import OllamaClient
from app.infrastructure.qdrant_client import QdrantClient

print('✓ All Phase 2 & 3 implementations loaded')

# Check that they have the same interface
import inspect

print('FaqRepository.load_from_file signature:')
print(inspect.signature(FaqRepository.load_from_file))

print('OllamaClient.embed_text signature:')
print(inspect.signature(OllamaClient.embed_text))
"
```

## Troubleshooting

### Issue: Ollama Connection Error

```
RuntimeError: Ollama connection error: ...
```

**Solution:**
1. Check Ollama is running: `ollama serve`
2. Verify URL: `curl http://localhost:11434/`
3. Check embedding model: `ollama list`
4. Pull if needed: `ollama pull nomic-embed-text`

### Issue: Qdrant Connection Error

```
RuntimeError: Failed to create collection ...
```

**Solution:**
1. Check Qdrant is running
2. Verify URL: `curl http://localhost:6333/health`
3. Check if collection exists: `curl http://localhost:6333/collections`
4. Delete old collection if needed: `curl -X DELETE http://localhost:6333/collections/faq_entries`

### Issue: Embedding Dimension Mismatch

```
Vector dimensions do not match ...
```

**Solution:**
1. Check configured embedding model matches deployed model
2. Verify Ollama model is correct: `OLLAMA_EMBEDDING_MODEL=nomic-embed-text-v2-moe`
3. If changed, delete and recreate collection in Qdrant

### Issue: FAQ Validation Error

```
Invalid FAQ entry at index X: ...
```

**Solution:**
1. Check FAQ JSON file format
2. Verify all required fields present: id, question, answer
3. Ensure no empty required fields
4. Validate JSON syntax: `python -m json.tool data/faq.json`

## Manual Integration Test

If you want to verify the complete pipeline manually:

```python
import asyncio
import json
from pathlib import Path

from app.config import get_settings
from app.repositories.faq_repository import FaqRepository
from app.infrastructure.ollama_client import OllamaClient
from app.infrastructure.qdrant_client import QdrantClient
from app.services.ingestion_service import IngestionService

async def manual_test():
    # 1. Load settings
    settings = get_settings()
    print(f"Config loaded: {settings.qdrant_collection_name}")

    # 2. Load FAQ entries
    repo = FaqRepository()
    entries = repo.load_from_file("data/faq.json")
    print(f"Loaded {len(entries)} FAQ entries")

    # 3. Create service clients
    ollama = OllamaClient(settings)
    qdrant = QdrantClient(settings)

    # 4. Health checks
    ollama_ok = await ollama.health_check()
    qdrant_ok = qdrant.health_check()
    print(f"Ollama health: {ollama_ok}")
    print(f"Qdrant health: {qdrant_ok}")

    # 5. Run ingestion
    service = IngestionService(ollama, qdrant)
    result = await service.ingest_faq_entries(entries)

    # 6. Print results
    print(f"Ingestion result: {result}")
    print(f"Success: {result.success}")

    # 7. Verify in Qdrant
    for entry in entries[:3]:
        point = qdrant.get_point(entry.id)
        if point:
            print(f"✓ Found FAQ {entry.id} in Qdrant")

    await ollama.close()

asyncio.run(manual_test())
```

## Expected Results

### All Tests Pass
```
============================== 40 passed in X.XXs ==============================
```

### Ingestion Script Output
```
======================================================================
Ingestion Result: 10/10 entries successfully ingested
======================================================================

✓ Ingestion completed successfully
```

### Qdrant Collection Verified
```
Collection exists: True
Successfully retrieved FAQ: faq_001
Question: How do I reset my password?
```

### Embedding Verified
```
Embedding dimension: 384
Embedding vector length: 384
First 5 values: [0.123, -0.456, 0.789, ...]
```

## Checklist for Phase 4 Verification

- [ ] All dependencies installed (`uv sync`)
- [ ] Ollama running and healthy
- [ ] Qdrant running and healthy
- [ ] Required Ollama models deployed
- [ ] All Phase 4 tests pass (33 tests)
- [ ] Ingestion script runs successfully
- [ ] FAQ entries visible in Qdrant
- [ ] Vector embeddings correct dimension
- [ ] Re-ingestion works (idempotency)
- [ ] Phase 2 & 3 implementations loaded
- [ ] No integration issues between phases

## Next Steps

Once Phase 4 is verified:

1. **Phase 5 (Retrieval Engine)** - Query embedding and semantic search
2. **Phase 6 (Answer Generation)** - Grounded prompt and response generation
3. **Phase 7 (Chat Service)** - Orchestration layer
4. **Phase 8 (Terminal UI)** - Textual interface
5. **Phase 9 (Deployment)** - Docker and runtime configuration
6. **Phase 10 (Quality Assurance)** - Final tests and documentation

Each phase depends on Phase 4's ingestion working correctly.
