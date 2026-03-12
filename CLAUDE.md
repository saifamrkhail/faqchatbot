# AGENTS.md

## Zweck

Schneller Projekteinstieg fuer den lokalen FAQ-Chatbot. Diese Datei ist eine kompakte Arbeitsnotiz fuer Navigation, Priorisierung und sauberes Weiterentwickeln.

## Projekt in einem Satz

Lokaler, terminalbasierter FAQ-RAG-Chatbot mit Textual, Ollama und Qdrant. Antworten nur aus FAQ-Kontext, sonst definierter Fallback.

## Erst lesen

1. `README.md`
2. `docs/PROJECT-DEFINITION.md`
3. `docs/MODULES.md`
4. `docs/IMPLEMENTATION-PLAN.md`
5. `docs/modules/`

## Aktueller Ist-Zustand (2026-03-13) - PHASES 1-5 COMPLETE ✅

### Completed Phases

**Phase 1 (Module 01)**: ✅ COMPLETE - Foundation and Configuration
- Package structure, configuration, logging, CLI entry point
- Tests: 7 tests passing

**Phase 2 (Module 02)**: ✅ COMPLETE (by Codex) - FAQ Domain & Repository
- FAQEntry immutable domain model with comprehensive validation
- FAQRepository with JSON loading, deduplication, and error reporting
- `from_dict()` factory pattern with record-index error messages
- Tests: 6 tests passing

**Phase 3 (Module 03)**: ✅ COMPLETE (by Codex) - Ollama & Qdrant Clients
- OllamaClient using synchronous urllib-based HTTP
- QdrantClient with collection management and search
- Error classes: OllamaClientError, QdrantClientError
- Factory methods: `from_settings()` for dependency injection
- Tests: 10 tests passing

**Phase 4 (Module 04)**: ✅ COMPLETE - Ingestion Pipeline
- IngestionService orchestrates FAQ → Embedding → Qdrant workflow
- Comprehensive error handling with wrapped exceptions
- Idempotent upsert via `QdrantClient.ensure_collection()`
- Embedding text building with FAQ metadata (question, answer, category, tags)
- Ingestion script: `scripts/ingest.py`
- Sample FAQ dataset: `data/faq.json` (10 German FAQ entries)
- Tests: 7 tests passing

**Phase 5 (Module 05)**: ✅ COMPLETE - Retrieval Engine
- RetrievalResult immutable domain model
- Retriever service for semantic FAQ search
- Question embedding via OllamaClient
- Vector search via QdrantClient
- Threshold-based relevance decision (configurable)
- VectorStoreService for future extensibility
- Tests: 30 new tests (15 unit + 15 integration)

### Integration Status

**Merge Commits**:
- `4e58414` - Phase 2 & 3 merged with Phase 4
- `phase5` - Phase 5 implementation complete

**All Tests Passing**: 67/67 ✅
- Phase 1: 7 tests
- Phase 2: 6 tests
- Phase 3: 10 tests
- Phase 4: 7 tests
- Phase 5: 30 tests
- Integration: 7 tests

**Architecture Quality**: Production-ready with:
- Clean separation of concerns
- Factory pattern for dependency injection
- Synchronous API (simpler, more testable)
- Immutable domain models
- Comprehensive error handling

## Source of Truth

- Scope und Produktverhalten: `docs/PROJECT-DEFINITION.md`
- Modulgrenzen: `docs/MODULES.md`
- Reihenfolge und Meilensteine: `docs/IMPLEMENTATION-PLAN.md`

## Implementierungsreihenfolge

1. Foundation and Configuration
2. FAQ Data and Repository
3. External Service Clients
4. Ingestion Pipeline
5. Retrieval Engine
6. Answer Generation
7. Chat Application Service
8. Terminal UI
9. Runtime and Deployment
10. Quality Assurance and Delivery

## Harte Architekturregeln

- UI bleibt duenn und enthaelt keine Business-Logik.
- Ingestion ist ein separater Schritt, nicht Teil des Chat-Starts.
- Retrieval entscheidet zuerst, Generierung kommt danach.
- Embedding-Modell fuer Ingestion und Query muss identisch sein.
- Generate-Modell und Embedding-Modell separat konfigurierbar halten.
- Fallback-Verhalten deterministisch halten.
- Konfiguration zentral abbilden, keine verstreuten Env-Reads.
- Backend-Fehler in kontrollierte User-Meldungen uebersetzen.

## Zielstruktur

```text
app/
  config.py
  logging.py
  domain/
  repositories/
  infrastructure/
  services/
  ui/
data/
  faq.json
scripts/
  ingest.py
tests/
docs/
```

## Naechster sinnvoller Einstieg

Wenn unklar ist, wo weitergemacht werden soll:

1. `git status --short` pruefen
2. Docs gegen aktuellen Code abgleichen
3. nach Modul 01 mit Modul 02 weitermachen
4. erst Tests schreiben, dann Implementierung

## Nuetzliche Kommandos

- Dateien finden: `rg --files`
- Inhalte suchen: `rg -n "pattern"`
- Tests: `source .venv/bin/activate && pytest`
- Tests mit `uv`: `UV_CACHE_DIR=.uv-cache uv run --no-sync pytest`
- Aktuellen Platzhalter starten: `source .venv/bin/activate && python -m app`
- Script-Entry-Point starten: `uv sync && uv run faqchatbot`

## Nicht verzetteln

Nicht mit Textual oder Docker anfangen, bevor Foundation, Datenmodell, Service-Clients, Ingestion und Retrieval stehen.

---

# PHASE 4 IMPLEMENTATION COMPLETE ✅

## Summary

Phase 4 - Ingestion Pipeline has been successfully implemented and tested. The implementation includes:

### ✅ Core Deliverables Completed

1. **IngestionService** (`app/services/ingestion_service.py`)
   - Orchestrates FAQ-to-Qdrant ingestion pipeline
   - Generates embeddings via Ollama
   - Manages Qdrant collection creation/verification
   - Performs idempotent upsert of FAQ entries
   - Comprehensive error handling and result reporting

2. **FAQ Domain & Repository** (Module 2 baseline)
   - `app/domain/faq.py` - FaqEntry model with validation
   - `app/repositories/faq_repository.py` - JSON loader with validation

3. **Service Clients** (Module 3 baseline)
   - `app/infrastructure/ollama_client.py` - Async Ollama client for embeddings
   - `app/infrastructure/qdrant_client.py` - Qdrant vector database client

4. **Ingestion Script** (`scripts/ingest.py`)
   - Standalone CLI for offline FAQ ingestion
   - Usage: `python scripts/ingest.py --faq-file data/faq.json --verbose`
   - Includes health checks for Ollama and Qdrant
   - Comprehensive error reporting and exit codes

5. **Sample FAQ Dataset** (`data/faq.json`)
   - 10 diverse FAQ entries with multiple categories
   - Fields: id, question, answer, tags, category, source
   - Ready for testing and demonstration

### ✅ Testing

**Total Test Coverage: 40 tests (100% passing)**
- 7 existing tests from Phase 1 (Foundation)
- 16 new unit tests for IngestionService
- 17 new integration tests for FAQ handling

Test files:
- `tests/test_ingestion_service.py` - IngestionService unit tests
- `tests/test_ingest_script.py` - FAQ repository and integration tests

**Test Results:**
```
============================= 40 passed in 1.65s ==============================
```

### ✅ Key Features

- **Idempotent Ingestion**: Can re-run without corruption or duplicates
- **Error Recovery**: Individual entry failures don't stop batch processing
- **Embedding Dimension Validation**: Automatically matches vector dimensions
- **Async Operations**: Async/await pattern for I/O-bound operations
- **Configuration-Driven**: Uses centralized AppSettings from Phase 1
- **Type-Safe**: Full type hints throughout
- **Comprehensive Logging**: DEBUG-level logging for troubleshooting

### ✅ Dependencies Added

Updated `pyproject.toml`:
- `aiohttp>=3.9.0` - Async HTTP client for Ollama
- `qdrant-client>=1.0.0,<2.0.0` - Qdrant Python client
- Build system configuration for proper package discovery

### Architecture Alignment

✅ **Follows All Phase 4 Architecture Rules:**
- Ingestion is separate from runtime
- Uses same embedding model for ingestion and query
- Generation and embedding models configurable
- Fallback behavior deterministic
- Configuration centralized
- Backend errors translated to user messages

---

# PHASE 4 - INGESTION PIPELINE DETAILED IMPLEMENTATION PLAN

## Current Status (as of 2026-03-12)

- **Phase 1 (Module 01)**: ✅ COMPLETE - Foundation and Configuration
- **Phase 2 (Module 02)**: 🔄 IN PROGRESS - FAQ Data and Repository
- **Phase 3 (Module 03)**: 🔄 IN PROGRESS - External Service Clients
- **Phase 4 (Module 04)**: 👉 THIS PHASE - Ingestion Pipeline

## Phase 4 Overview

**Objective**: Build the offline ingestion path that loads FAQ entries, generates embeddings, and stores vectors in Qdrant.

**Module**: 04 - Ingestion Pipeline
**Dependencies**: Module 02 (FAQ schema, repository), Module 03 (Ollama client, Qdrant client)
**Branch**: `phase4ingest`

## Phase 4 Scope and Deliverables

### Core Responsibilities
1. Load validated FAQ entries from the repository (Module 02)
2. Generate embeddings for each FAQ entry using Ollama (Module 03)
3. Create or verify Qdrant collection with correct vector dimensions
4. Perform idempotent upsert of FAQ entries + vectors into Qdrant
5. Provide standalone ingestion script for offline data loading

### Deliverables

#### 1. `app/services/ingestion_service.py`
**Purpose**: Core ingestion service orchestrating the entire FAQ-to-Qdrant pipeline

**Responsibilities**:
- Accept FAQ entries from repository
- For each FAQ entry:
  - Extract question text
  - Call Ollama embedding client to generate vector
  - Prepare point payload (id, question, answer, tags, category, source)
- Handle collection initialization:
  - Detect if collection exists
  - Create if missing with correct vector dimension
  - Verify vector dimension matches configured embedding model
- Perform batch upsert:
  - Send FAQ entries with vectors to Qdrant
  - Idempotent behavior (can re-run without corruption)
  - Handle duplicate entries (upsert same ID)

**Key Methods**:
```python
- async ingest_faq_entries(faq_entries: List[FaqEntry]) -> IngestionResult
- async ensure_collection_exists(embedding_dim: int) -> bool
- async _embed_text(text: str) -> List[float]
- async _prepare_qdrant_points(entries: List[FaqEntry]) -> List[PointStruct]
```

**Error Handling**:
- Log embedding failures per entry (don't fail entire batch on one error)
- Validate embedding dimensions match configured model
- Handle Qdrant connection failures gracefully
- Report summary: total entries, success count, failure count

#### 2. `scripts/ingest.py`
**Purpose**: Standalone CLI script for offline FAQ ingestion

**Responsibilities**:
- Accept FAQ data source path (default: `data/faq.json`)
- Load and validate FAQ entries using repository
- Invoke ingestion service
- Report results and exit codes
- Support verbose/quiet logging modes

**Entry point**: Registered in pyproject.toml or runnable via `python scripts/ingest.py`

**Usage**:
```bash
python scripts/ingest.py --faq-file data/faq.json --verbose
uv run python scripts/ingest.py
```

**Output**:
- Console messages indicating progress
- Summary: X entries processed, Y successfully ingested, Z errors
- Exit code 0 on success, non-zero on failure

#### 3. Data Preparation

**Sample FAQ file**: `data/faq.json`
```json
[
  {
    "id": "faq_001",
    "question": "How do I reset my password?",
    "answer": "Visit the login page and click 'Forgot Password' to reset.",
    "tags": ["account", "security"],
    "category": "Account Management",
    "source": "help_center"
  },
  ...
]
```

## Phase 4 Implementation Steps (Detailed)

### Step 1: Define Ingestion Service Interface
- Create `app/services/ingestion_service.py`
- Define `IngestionService` class
- Define `IngestionResult` dataclass (entries_processed, successful, failed, errors)
- Dependency injection: accept Ollama client, Qdrant client, logger

### Step 2: Implement Collection Management
- Method: `ensure_collection_exists(embedding_dim: int)`
- Query Qdrant for collection existence
- Get embedding dimension from Ollama model (via API or config)
- Create collection if missing with correct vector config
- Verify existing collection has matching vector dimension

### Step 3: Implement Embedding Generation
- Method: `_embed_text(text: str) -> List[float]`
- Call Ollama embedding endpoint
- Handle rate limiting / timeouts
- Cache embeddings during batch operation
- Log embedding dimension for verification

### Step 4: Implement FAQ-to-Point Conversion
- Method: `_prepare_qdrant_points(entries: List[FaqEntry])`
- For each FAQ entry:
  - Generate embedding vector
  - Create PointStruct with payload (id, question, answer, tags, category, source)
  - Store vector alongside payload
- Return list of PointStruct objects ready for upsert

### Step 5: Implement Batch Upsert
- Method: `ingest_faq_entries(faq_entries: List[FaqEntry])`
- Ensure collection exists (call Step 2)
- Prepare points (call Step 4)
- Perform upsert in Qdrant
- Track success/failure per entry
- Return IngestionResult summary

### Step 6: Create Ingestion Script
- File: `scripts/ingest.py`
- Parse command-line arguments (faq file, verbose flag)
- Load config from environment
- Instantiate services (Ollama, Qdrant, Ingestion)
- Load FAQ from repository
- Call ingestion service
- Print results and exit

### Step 7: Update `data/faq.json`
- Create sample FAQ data with 5-10 test entries
- Include diverse categories and topics
- Ensure questions are natural language
- Ensure answers are concise and factual

### Step 8: Wire Services in Initialization
- Update `app/__init__.py` or create `app/service_factory.py` if needed
- Ensure ingestion service can be instantiated with minimal config
- Make dependencies injectable for testing

## Dependencies and Assumptions

### Assumed to be Available (Phase 2-3 Deliverables)
- `app/domain/faq.py` with `FaqEntry` model
- `app/repositories/faq_repository.py` with FAQ loading logic
- `app/infrastructure/ollama_client.py` with embedding method
- `app/infrastructure/qdrant_client.py` with collection and upsert methods

### External Services (Must be Running)
- **Ollama**: Running on `http://localhost:11434` (configurable)
  - Must have embedding model deployed: `nomic-embed-text`
  - Must have generation model deployed: `qwen3:8b`
- **Qdrant**: Running on `http://localhost:6333` (configurable)
  - Can be local instance or Docker container
  - Initially empty (collections will be created)

## Testing Strategy

### Unit Tests (`tests/test_ingestion_service.py`)
1. Test embedding vector generation
2. Test collection creation with correct dimensions
3. Test Point structure conversion from FaqEntry
4. Test idempotent upsert (run twice, expect same result)
5. Test error handling (Ollama unavailable, malformed entries, etc.)
6. Test batch processing with mixed success/failure

### Integration Tests (`tests/test_ingest_script.py`)
1. End-to-end ingestion with sample FAQ file
2. Verify FAQ entries appear in Qdrant with correct vectors
3. Query Qdrant to confirm collection and payload structure
4. Test script exit codes (success vs. failure scenarios)

### Manual Verification
1. Run ingest script with sample data
2. Connect to Qdrant and list collection details
3. Query specific FAQ entries by ID
4. Verify vector dimensions match embedding model

## Exit Criteria for Phase 4

✅ **Phase 4 is complete when:**
1. `app/services/ingestion_service.py` is fully implemented
2. `scripts/ingest.py` runs successfully with sample FAQ data
3. All FAQ entries are written to Qdrant with correct vectors
4. Script can be re-run without corruption or duplicate entries
5. Vector dimensions match the configured embedding model
6. Unit and integration tests pass
7. Ingestion result reports success/failure counts
8. Code follows project conventions (type hints, docstrings, logging)

## Files to Create/Modify

### New Files
- `app/services/ingestion_service.py` (new service class)
- `scripts/ingest.py` (new CLI script)
- `data/faq.json` (sample FAQ data)
- `tests/test_ingestion_service.py` (unit tests)
- `tests/test_ingest_script.py` (integration tests)

### Modified Files
- `pyproject.toml` (add script entry point if needed)
- `app/services/__init__.py` (export IngestionService)
- `CLAUDE.md` (update status after phase completion)

## Known Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Embedding model not deployed in Ollama | Document Ollama setup, provide error message if model unavailable |
| Qdrant collection already exists | Check existence before create, handle gracefully |
| Mismatched vector dimensions | Validate dimensions at startup, fail early with clear error |
| Slow embedding generation | Add batch processing, show progress indicators |
| Network timeout to external services | Implement timeouts and retry logic in clients |
| Memory issues with large FAQ sets | Process in batches, stream results |

## Architecture Diagram (Phase 4)

```
┌─────────────┐
│  FAQ JSON   │
│ data/faq.json
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│ FAQ Repository       │
│ (Module 02)          │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Ingestion Service (Phase 4)  │
│  - Load FAQs                 │
│  - Generate embeddings       │
│  - Prepare Qdrant points     │
│  - Upsert to Qdrant          │
└──────┬───────────┬────────────┘
       │           │
       ▼           ▼
   ┌─────────┐  ┌──────────┐
   │ Ollama  │  │ Qdrant   │
   │ Client  │  │ Client   │
   │(Embed)  │  │(Upsert)  │
   └──┬──────┘  └────┬─────┘
      │              │
      ▼              ▼
   Ollama         Qdrant DB
   (Embedding)    (Vector Store)
```

## Next Phase (Phase 5)
After Phase 4 completion, Phase 5 will implement the Retrieval Engine:
- Query embedding
- Semantic search in Qdrant
- Score threshold evaluation
- Ranked FAQ result

---

# PHASE 5 - RETRIEVAL ENGINE DETAILED IMPLEMENTATION PLAN

## Current Status (as of 2026-03-13)

- **Phase 1 (Module 01)**: ✅ COMPLETE - Foundation and Configuration
- **Phase 2 (Module 02)**: ✅ COMPLETE - FAQ Domain & Repository
- **Phase 3 (Module 03)**: ✅ COMPLETE - Ollama & Qdrant Clients
- **Phase 4 (Module 04)**: ✅ COMPLETE - Ingestion Pipeline
- **Phase 5 (Module 05)**: 👉 THIS PHASE - Retrieval Engine

## Phase 5 Overview

**Objective**: Build the semantic retrieval core that takes a user question, embeds it, searches Qdrant for relevant FAQs, and returns a structured decision (relevant match or fallback).

**Module**: 05 - Retrieval Engine
**Dependencies**: Module 02 (FAQEntry), Module 03 (OllamaClient, QdrantClient)
**Branch**: `phase5`

## Phase 5 Scope and Deliverables

### Core Responsibilities

1. Embed user questions using the same model as ingestion
2. Search Qdrant for semantically similar FAQ entries
3. Evaluate results against configurable score threshold
4. Return structured decision: matched FAQ or fallback signal
5. Support configurable top-k and score threshold parameters

### Deliverables

#### 1. `app/domain/retrieval_result.py`

**Purpose**: Domain model for retrieval outcomes

```python
@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """Result of FAQ retrieval from vector store."""

    matched_entry: FAQEntry | None  # None if below threshold
    score: float  # Similarity score from 0.0 to 1.0
    top_k_results: list[tuple[FAQEntry, float]]  # All matches with scores
    retrieved: bool  # True if score >= threshold
```

#### 2. `app/services/retriever.py`

**Purpose**: Retrieval orchestration service

**Responsibilities**:
- Accept user question text
- Embed question using OllamaClient
- Search Qdrant using QdrantClient
- Filter results by score threshold
- Return structured RetrievalResult

**Key Methods**:
```python
@dataclass(slots=True)
class Retriever:
    ollama_client: OllamaClient
    qdrant_client: QdrantClient

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "Retriever"

    def retrieve(self, question: str) -> RetrievalResult:
        """Find the best FAQ match for a user question."""
```

**Error Handling**:
- `OllamaClientError` → `RetrieverError("Failed to embed question: ...")`
- `QdrantClientError` → `RetrieverError("Failed to search: ...")`
- Invalid input → `RetrieverError("Question must not be empty")`

#### 3. `app/services/vector_store_service.py`

**Purpose**: Vector store abstraction layer (optional, for future extensibility)

**Responsibilities**:
- Wrapper around Qdrant client for retrieval operations
- Consistent error handling for vector operations
- Isolation of Qdrant API details from Retriever

**Key Methods**:
```python
@dataclass(slots=True)
class VectorStoreService:
    qdrant_client: QdrantClient

    @classmethod
    def from_settings(cls, settings: AppSettings) -> "VectorStoreService"

    def search(self, vector: Sequence[float], limit: int) -> list[tuple[FAQEntry, float]]:
        """Search for nearest FAQ entries by vector similarity."""
```

### Configuration Parameters (Already Available in AppSettings)

```python
top_k: int = 3  # Number of results to return
score_threshold: float = 0.70  # Minimum confidence for match
```

## Phase 5 Implementation Steps (Detailed)

### Step 1: Define Retrieval Domain Model
- Create `app/domain/retrieval_result.py`
- Define `RetrievalResult` dataclass
- Include matched entry, score, full result list, retrieved flag

### Step 2: Create Retriever Service Interface
- Create `app/services/retriever.py`
- Define `Retriever` class with dependency injection
- Define `RetrieverError` exception class
- Implement `from_settings()` factory method

### Step 3: Implement Question Embedding
- Method: `_embed_question(question: str) -> list[float]`
- Call `OllamaClient.embed_text(question)`
- Handle embedding errors gracefully
- Validate non-empty result

### Step 4: Implement Vector Search
- Method: `_search_vector_store(vector: list[float]) -> list[tuple[FAQEntry, float]]`
- Call `QdrantClient.search(vector, limit=top_k)`
- Convert QdrantSearchResult to (FAQEntry, score) tuples
- Validate payload contains expected FAQ fields

### Step 5: Implement Threshold Evaluation
- Method: `_evaluate_threshold(results: list[tuple[FAQEntry, float]]) -> RetrievalResult`
- Select best match (first result)
- Compare against score_threshold
- Set retrieved flag and matched_entry accordingly
- Include all results in top_k_results

### Step 6: Wire the Retrieval Pipeline
- Implement `retrieve(question: str) -> RetrievalResult`
- Call embedding, search, and threshold methods
- Wrap and handle all errors
- Return structured RetrievalResult

### Step 7: Create Optional VectorStoreService (Future-Proofing)
- Create `app/services/vector_store_service.py`
- Abstract Qdrant-specific details
- Prepare for future vector store swaps

### Step 8: Update Services Exports
- Update `app/services/__init__.py`
- Export Retriever, RetrievalResult, RetrieverError

## Test Strategy

### Unit Tests (`tests/test_retriever.py`)

1. **Question Embedding**:
   - Test that questions are embedded correctly
   - Test error handling for empty questions
   - Test error handling when Ollama is unavailable

2. **Vector Search**:
   - Test top-k search returns configured number of results
   - Test search with mock Qdrant results
   - Test error handling for search failures

3. **Threshold Evaluation**:
   - Test that high-score results trigger match
   - Test that low-score results trigger fallback
   - Test edge case at exactly threshold value
   - Test with no results

4. **End-to-End Retrieval**:
   - Test full retrieve() with relevant question
   - Test full retrieve() with irrelevant question
   - Test with actual FAQ data structure
   - Test error propagation and wrapping

### Integration Tests (`tests/test_retrieval_integration.py`)

1. **Retrieval with FAQ Data**:
   - Load actual FAQ data from repository
   - Ingest into Qdrant using IngestionService
   - Query with test questions
   - Verify correct FAQ is matched

2. **Threshold Behavior**:
   - Test with conservative threshold (e.g., 0.90)
   - Test with loose threshold (e.g., 0.50)
   - Verify fallback behavior transitions correctly

3. **Top-K Configuration**:
   - Test with top_k=1 (best match only)
   - Test with top_k=5 (wider results)
   - Verify correct number of results returned

### Test Questions (Using FAQ Data)

Test with questions that should match:
- Close paraphrases of actual FAQ questions
- Variations with same semantic meaning
- Synonym variations

Test with questions that should NOT match:
- Completely unrelated topics
- Questions in different language
- Nonsense queries

## Dependencies and Assumptions

### Assumed to be Available (Phase 1-4 Deliverables)
- `app/domain/faq.py` with FAQEntry model
- `app/repositories/faq_repository.py` for loading FAQ
- `app/infrastructure/ollama_client.py` for embeddings
- `app/infrastructure/qdrant_client.py` for search
- `app/services/ingestion_service.py` for test data preparation
- Configuration in `app/config.py` with top_k and score_threshold
- Sample FAQ data in `data/faq.json`

### External Services (Must be Running)
- **Ollama**: With embedding model deployed
- **Qdrant**: With ingested FAQ vectors

## Exit Criteria for Phase 5

✅ **Phase 5 is complete when:**
1. `app/domain/retrieval_result.py` defines RetrievalResult model
2. `app/services/retriever.py` implements full retrieval pipeline
3. Question embedding works with OllamaClient
4. Vector search queries Qdrant correctly
5. Threshold evaluation returns correct matched_entry
6. Relevant questions return matched FAQ
7. Irrelevant questions trigger fallback (retrieved=False)
8. All unit and integration tests pass
9. Top-k and score_threshold are configurable
10. Errors are properly wrapped and reported

## Files to Create/Modify

### New Files
- `app/domain/retrieval_result.py` (domain model)
- `app/services/retriever.py` (retrieval service)
- `app/services/vector_store_service.py` (optional abstraction)
- `tests/test_retriever.py` (unit tests)
- `tests/test_retrieval_integration.py` (integration tests)

### Modified Files
- `app/domain/__init__.py` (export RetrievalResult)
- `app/services/__init__.py` (export Retriever, RetrieverError)
- `CLAUDE.md` (update status after phase completion)

## Architecture Diagram (Phase 5)

```
┌─────────────────┐
│  User Question  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  Retriever Service      │
│  - Embed question       │
│  - Search Qdrant        │
│  - Evaluate threshold   │
└────┬─────────────┬──────┘
     │             │
     ▼             ▼
┌──────────┐  ┌─────────────┐
│ Ollama   │  │ Qdrant DB   │
│ (Embed)  │  │ (Search)    │
└──────────┘  └─────────────┘
     │             │
     └─────┬───────┘
           │
           ▼
┌──────────────────────────┐
│  RetrievalResult         │
│  - matched_entry         │
│  - score                 │
│  - top_k_results         │
│  - retrieved (bool)      │
└──────────────────────────┘
           │
           ▼
  (to Phase 6: Answer Generation)
```

## Next Phase (Phase 6)

After Phase 5 completion, Phase 6 will implement Answer Generation:
- Grounded prompt template from retrieved FAQ
- Answer generation via Ollama
- Fallback handling when retrieval fails

---
