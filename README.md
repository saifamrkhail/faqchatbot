# FAQ Chatbot

A local, terminal-based FAQ RAG chatbot with **Textual** UI, **Ollama** (embeddings & generation), and **Qdrant** (vector store).

The bot answers questions **only from FAQ context** and returns a deterministic fallback message when confidence is low.

---

## Quick Start (Docker) 🐳

### Prerequisites
- **Docker** & **Docker Compose** (v2.0+)
- ~5 GB disk space (for models)
- Internet connection (first run downloads models)

### 1. Start Services
```bash
docker compose up --build app
```
This starts Ollama, Qdrant, and downloads models (~1-2 min on first run).

### 2. Ingest FAQ Data
```bash
# In another terminal
docker compose run --rm ingest
```

### 3. Chat
```bash
docker compose up app
```

Enter questions like: *"Welche IT-Dienstleistungen bieten Sie an?"*

---

## What's Inside

| Component | Purpose |
|-----------|---------|
| **Ingestion** | Load FAQ → Generate embeddings → Store in Qdrant |
| **Retrieval** | Embed user question → Semantic search → Score threshold |
| **Generation** | Grounded answer from FAQ context or fallback |
| **TUI** | Rich terminal interface with Textual |

**Models:**
- Generation: `qwen3.5:2b`
- Embedding: `nomic-embed-text-v2-moe`

---

## Common Commands

```bash
# Help
make help

# Start app
make up
make ingest
make chat

# Run tests
make test

# Docker logs
make logs

# Ingest FAQ data
make ingest

# Clean up
make clean

# Full rebuild
make rebuild
```

See `Makefile` for all commands.

---

## Project Structure

```
app/
  ├── config.py          # Configuration from env vars
  ├── domain/            # Data models (FAQ, Results, Responses)
  ├── repositories/      # FAQ JSON loading
  ├── services/          # Business logic (Ingestion, Retrieval, Generation, Chat)
  ├── infrastructure/    # Ollama & Qdrant clients
  └── ui/                # Textual TUI

scripts/
  └── ingest.py          # Standalone ingestion script

data/
  └── faq.json           # Sample FAQ (10 German entries)

tests/                   # 149 tests (all passing ✓)
docs/                    # Detailed documentation
```

---

## Tests

```bash
# All tests
pytest

# By phase
pytest tests/test_config.py          # Phase 1
pytest tests/test_ingestion*.py      # Phase 4
pytest tests/test_retriever.py       # Phase 5
pytest tests/test_answer*.py         # Phase 6
pytest tests/test_chat_service.py    # Phase 7
pytest tests/test_ui*.py             # Phase 8
```

**Status**: 149 tests passing ✓

---

## Architecture Rules

1. **UI is thin** — no business logic in TUI
2. **Ingestion is separate** — not part of chat startup
3. **Retrieval before generation** — threshold decides match
4. **Same embedding model** — for both ingestion and queries
5. **Configurable models** — generate and embedding models separate
6. **Deterministic fallback** — always the same message
7. **Centralized config** — no scattered env reads
8. **Backend → user messages** — errors translated to user-friendly text

---

## Configuration

Set via `FAQ_CHATBOT_*` environment variables:

```bash
FAQ_CHATBOT_OLLAMA_BASE_URL=http://localhost:11434
FAQ_CHATBOT_OLLAMA_GENERATE_MODEL=qwen3.5:2b
FAQ_CHATBOT_OLLAMA_EMBEDDING_MODEL=nomic-embed-text-v2-moe
FAQ_CHATBOT_QDRANT_URL=http://localhost:6333
FAQ_CHATBOT_TOP_K=3
FAQ_CHATBOT_SCORE_THRESHOLD=0.70
FAQ_CHATBOT_FALLBACK_MESSAGE="Leider konnte ich Ihre Frage nicht verstehen."
```

See `.env.example` for defaults.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Ollama timeout | `docker compose logs ollama` / `docker compose restart ollama` |
| Qdrant refused | `curl http://localhost:6333/health` / restart services |
| Model not found | `docker exec faqchatbot-claude-ollama-1 ollama list` |
| Local deps fail | `uv sync --force` |

---

## Documentation

- **`docs/PROJECT-DEFINITION.md`** — What & why
- **`docs/IMPLEMENTATION-PLAN.md`** — How (10 phases)
- **`docs/RUNTIME-DEPLOYMENT.md`** — Deployment guide
- **`docs/modules/`** — Detailed module specs
- **`CLAUDE.md`** — Development instructions

---

## Status

✅ **Phases 1–8 complete**
- Foundation & Configuration
- FAQ Domain & Repository
- Ollama & Qdrant Clients
- Ingestion Pipeline
- Retrieval Engine
- Answer Generation
- Chat Application Service
- Terminal UI (Textual)

149 tests passing. Production-ready.

---

**Next**: `docker compose up --build app` 🚀
