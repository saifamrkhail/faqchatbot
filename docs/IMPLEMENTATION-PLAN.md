# Implementation Plan

## Overview

10-phase modular development plan for the FAQ chatbot. Each phase builds on previous phases and is independently testable.

## Current Status (2026-03-16)

✅ **All phases complete and production-ready**

| Phase | Modules | Objective | Status |
|-------|---------|-----------|--------|
| 1 | 01 | Foundation and Configuration | ✅ Complete |
| 2 | 02, 03 | FAQ Domain and External Service Clients | ✅ Complete |
| 3 | 04 | Ingestion Pipeline | ✅ Complete |
| 4 | 05 | Retrieval Engine | ✅ Complete |
| 5 | 06 | Answer Generation | ✅ Complete |
| 6 | 07 | Chat Application Service | ✅ Complete |
| 7 | 08 | Terminal UI | ✅ Complete |
| 8 | 09 | Runtime and Deployment | ✅ Complete |
| 9 | 10 | Quality Assurance and Delivery | ✅ Complete |

## Key Milestones

### Phase 1 (Foundation)
- Centralized configuration via `FAQ_CHATBOT_*` env vars
- Dependency injection patterns established
- CLI entry point: `uv run faqchatbot --tui`

### Phases 2–3 (Data & Clients)
- Immutable FAQ domain model with validation
- Ollama HTTP client (embeddings, generation)
- Qdrant HTTP client (collections, upsert, search)

### Phase 4 (Ingestion)
- Offline FAQ → embedding → Qdrant pipeline
- Idempotent upsert with deterministic UUIDs
- Standalone `python -m scripts.ingest` script

### Phases 5–6 (Retrieval & Generation)
- Semantic FAQ search with configurable threshold
- Grounded LLM answer generation
- Fallback messages for low confidence

### Phase 7 (Chat Service)
- Question validation and normalization
- Full orchestration: retrieval → generation
- Streaming token support via `generate_streaming()`

### Phase 8 (Terminal UI)
- Plain terminal chat loop (no external UI libraries)
- Token streaming for perceived latency reduction
- Error handling with user-friendly messages

### Phases 9–10 (Runtime & QA)
- Docker deployment (Qdrant container, Ollama on host)
- Comprehensive test coverage (161 tests)
- Grid search evaluation framework
- Production-ready defaults from evaluation

## Documentation Map

| File | Purpose |
|------|---------|
| `PROJECT-DEFINITION.md` | Scope, goals, constraints |
| `MODULES.md` | Module boundaries and responsibilities |
| `IMPROVEMENT-PLAN.md` | Evaluation results and improvements |
| `RUNTIME-DEPLOYMENT.md` | Docker setup and local development |
| `modules/` | Detailed specs for each module |

## Next Steps for Future Development

See `CLAUDE.md` for:
- Architecture rules (never break these)
- Starting a new phase (TDD approach)
- Deferred improvements (P7 soft threshold zone)

---

**All scope delivered. System is production-ready with 100% evaluation metrics.**
