# Development Guide

## Current Status (2026-03-16)

**All phases complete and production-ready** ✅

- Phases 1–8: Core features, streaming UI, evaluation framework
- Grid search: all 6 combinations score 1.000 with `qwen3.5:9b`
- 161 tests passing, 100% evaluation metrics
- Optimal defaults set: `top_k=3`, `threshold=0.60`, `temp=0.20`

## Starting a New Phase

1. **Read these first:**
   - `README.md` — Quick start and key commands
   - `docs/PROJECT-DEFINITION.md` — Scope and goals
   - `docs/MODULES.md` — Module boundaries
   - `docs/IMPLEMENTATION-PLAN.md` — 10-phase overview

2. **Check current state:**
   - `git status --short` — uncommitted changes?
   - `make test` — do tests pass?
   - `make health` — are Ollama and Qdrant reachable?

3. **Make changes:**
   - Understand existing patterns in `app/` (config → domain → services → UI)
   - Write tests first, then implementation
   - Commit frequently with clear messages

## Architecture Rules (Never Break)

1. UI stays thin — no business logic
2. Ingestion is separate — not coupled to chat startup
3. Retrieval before generation — threshold decides
4. Same embedding model for ingestion and queries
5. Generate and embedding models separately configurable
6. Fallback is deterministic
7. Config is centralized (no scattered env reads)
8. Backend errors → user-friendly messages

## Key Files

| Path | Purpose |
|------|---------|
| `app/config.py` | Centralized configuration |
| `app/domain/` | Immutable data models |
| `app/repositories/` | Data loading (FAQ JSON) |
| `app/infrastructure/` | External service clients (Ollama, Qdrant) |
| `app/services/` | Business logic (ingestion, retrieval, generation, chat) |
| `app/ui/` | Terminal chat interface |
| `data/faq.json` | 15 German FAQ entries with alt_questions |
| `tests/` | 161 unit + integration tests |
| `scripts/ingest.py` | Offline FAQ ingestion |

## Common Tasks

```bash
# Development
make test
make test-watch
make run-local        # Run chatbot locally
make ingest-local     # Ingest FAQ locally

# Docker deployment
make up               # Start Qdrant
make ingest           # Embed FAQ and load into Qdrant
make chat             # Run chatbot in Docker

# Evaluation
make eval             # Run evaluation suite (requires live services)
make grid-search      # Run parameter grid search
```

## Next Steps for Future Work

### P7 — Soft Threshold Zone (deferred, LOW priority)

With 100% paraphrase recall post-P2a, the soft-zone logic (score 0.50–0.70 → graceful partial answers)
adds complexity without measurable benefit. Only revisit if new FAQ entries show paraphrase gaps after re-evaluation.

### P8+ — Beyond Scope

Possible future improvements:
- Multi-language support (already bilingual FAQ with English alt_questions)
- User feedback loop (log questions → identify gaps)
- A/B testing framework (compare retrieval/generation approaches)
- Model fine-tuning on domain-specific FAQ corpus
- Conversation history (multi-turn chat)

## Important Notes

- **Re-ingestion required** after `data/faq.json` changes: `make ingest`
- **Host Ollama required** — app expects `http://localhost:11434` on the host
- **External Qdrant support** — use `make up USE_EXTERNAL_QDRANT=true` to skip starting the Docker container
- **160+ tests** provide confidence for refactoring — keep them passing
- **Config defaults** reflect grid search results — don't change without re-evaluating

---

**Ready to start?** Pick a task, write a test, then implement. See `docs/` for detailed module specs.
