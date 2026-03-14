# FAQ Chatbot

A local, terminal-based FAQ RAG chatbot with plain **Terminal UI**, **Ollama** (embeddings & generation), and **Qdrant** (vector store).

The bot answers questions **only from FAQ context** and returns a deterministic fallback message when confidence is low.

---

## Quick Start 🚀

### Prerequisites
- **Docker** & **Docker Compose** (v2.0+) — OR —
- **Python 3.11+** and **uv** for local development
- ~5 GB disk space (for models)
- Internet connection (first run downloads models)

---

## Setup & Run (Docker) 🐳

### 1. Start Services
```bash
make up
```

This starts Ollama, Qdrant, and the app (~30 seconds).

### 2. Pull Ollama Models (in another terminal)
Models must be pulled **inside** the Ollama container:

```bash
make pull-models
```

This pulls into the container:
- `nomic-embed-text-v2-moe` (embedding)
- `qwen3.5:2b` (generation)

Verify with:
```bash
make models
```

### 3. Ingest FAQ Data
```bash
make ingest
```

Expected output:
```
✓ Loaded 10 FAQ entries
✓ Generated 10 embeddings
✓ Stored vectors in Qdrant
```

### 4. Start the Chat
```bash
make chat
```

Enter questions like:
- *"Welche IT-Dienstleistungen bieten Sie an?"*
- *"Wie kann ich Support kontaktieren?"*

Press **Ctrl+C** to exit.

### Useful Commands
```bash
make logs          # View app logs
make logs-ollama   # View Ollama logs
make logs-qdrant   # View Qdrant logs
make ps            # Show container status
make down          # Stop all services
make health        # Check service health
```

---

## Setup & Run (Local Development) 💻

For local development against Docker services:

### 1. Install Dependencies
```bash
cd faqchatbot-claude
uv sync
```

### 2. Start Services (Docker)
```bash
docker compose up -d ollama qdrant
```

### 3. Pull Models into Ollama Container
```bash
docker compose exec ollama ollama pull nomic-embed-text-v2-moe
docker compose exec ollama ollama pull qwen3.5:2b
```

### 4. Ingest FAQ Data Locally
```bash
make ingest-local
```

### 5. Run Tests
```bash
make test
```

Result: **147 passed, 0 skipped** ✓

### 6. Start the Chat Locally
```bash
make run-local
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Model not found (404)** | Pull into container: `make pull-models` |
| **Qdrant connection refused** | Start services: `make up` |
| **Ingest fails with timeout** | Check logs: `make logs-ollama` |
| **Check available models** | `make models` |
| **Tests fail locally** | Reset deps: `uv sync --force` |
| **Need shell in Ollama container** | `make shell-ollama` |

---

## What's Inside

| Component | Purpose |
|-----------|---------|
| **Ingestion** | Load FAQ → Generate embeddings → Store in Qdrant |
| **Retrieval** | Embed user question → Semantic search → Score threshold |
| **Generation** | Grounded answer from FAQ context or fallback |
| **UI** | Terminal chat loop with Rich formatting |

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

tests/                   # 147 tests (all passing ✓)
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
- Terminal UI (Rich-based chat loop)

147 tests passing. Production-ready.

---

**Next**: `docker compose up --build app` 🚀
