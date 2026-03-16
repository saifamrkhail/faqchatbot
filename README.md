# FAQ Chatbot

A local, terminal-based FAQ RAG chatbot with plain **Terminal UI**, **Ollama** (embeddings & generation), and **Qdrant** (vector store).

The bot answers questions **only from FAQ context** and returns a deterministic fallback message when confidence is low.

---

## Quick Start 🚀

### Prerequisites
- **Docker** & **Docker Compose** (v2.0+)
- **Python 3.11+** and **uv** for local development
- **Ollama** latest version
- qwen3.5:9b and nomic-embed-text-v2-moe models (pull these models with ollama)
- Internet connection (first run downloads models)

---

## Start the Chatbot — Complete Guide 🚀

### **Step 0: Prerequisites**

Make sure you have:
- **Docker & Docker Compose** (v2.0+)
- ~5 GB free disk space
- Internet connection (first run only)

### **Step 1: Clone & Navigate**

```bash
git clone https://github.com/saifamrkhail/faqchatbot.git
cd faqchatbot
```

### **Step 2: Start Core Services**

**Open Terminal 1:**

```bash
make up
```

**What happens:**
- Starts **Ollama** (embeddings & generation engine) on `http://localhost:11434`
- Starts **Qdrant** (vector database) on `http://localhost:6333`
- Runs in **background** (-d flag) so you can use Terminal 2

**Wait 10-15 seconds** for services to be ready. You'll see confirmation messages.

### **Step 3: Pull AI Models**

**Open Terminal 2** (while Terminal 1 keeps services running):

```bash
make pull-models
```

**What happens:**
- Downloads `nomic-embed-text-v2-moe` (embedding model)
- Downloads `qwen3.5:9b` (generation model)
- Stores them inside the Ollama container

⏱️ **This takes 2–5 minutes on first run** (~2 GB download)

**Verify models installed:**
```bash
make models
```

You should see both models listed.

### **Step 4: Ingest FAQ Data**

```bash
make ingest
```

**What happens:**
- Loads 10 sample German FAQ entries from `data/faq.json`
- Generates embeddings for each entry (semantic search vectors)
- Stores them in Qdrant (ready to be searched)

**Expected output:**
```
✓ Loaded 10 FAQ entries
✓ Generated 10 embeddings
✓ Stored vectors in Qdrant
Ingestion complete: 10 entries, 0 errors
```

### **Step 5: Start the Chatbot**

```bash
make chat
```

**What happens:**
- Opens an interactive terminal chat loop
- You can now ask questions in German

**Example interaction:**
```
────────────────────────────────────────────────────────────
  faqchatbot  |  'exit' oder Ctrl+C zum Beenden
────────────────────────────────────────────────────────────
Willkommen! Stelle eine Frage zu unseren FAQ.

Sie: Welche IT-Dienstleistungen bieten Sie an?
...
Bot: Wir bieten eine breite Palette von IT-Dienstleistungen an,
     darunter Netzwerkmanagement, IT-Support, Cloud-Lösungen...

Sie: exit
Tschüss!
```

**Exit with:** `exit` or `Ctrl+C`

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `make up` | Start Ollama, Qdrant, App |
| `make pull-models` | Download AI models (~2-5 min) |
| `make ingest` | Load FAQ data into Qdrant |
| `make chat` | Run interactive chatbot |
| `make test` | Run 149 tests |
| `make logs` | View app logs |
| `make ps` | Show container status |
| `make down` | Stop all services |
| `make clean` | Stop & delete all data |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Models not found (404)** | Run `make pull-models` in Terminal 2 |
| **Chatbot won't take input** | Make sure you're in Terminal 2, not logged into container |
| **"Port 6333 already in use"** | Run `make clean && make up` |
| **Qdrant connection refused** | Wait longer for services (check `make logs-qdrant`) |
| **Tests fail** | Run `uv sync --force` |
| **Image out of date** | Run `docker compose build app` |

---

## Local Development 💻

To run the chatbot **locally** (not in Docker):

```bash
# 1. Install dependencies
uv sync

# 2. Start just Ollama & Qdrant in Docker
docker compose up -d ollama qdrant

# 3. Pull models (same as Step 3 above)
make pull-models

# 4. Ingest data
make ingest-local

# 5. Run tests
make test

# 6. Start chatbot locally
make run-local
```

---

## From-Scratch Example (Copy & Paste)

```bash
# Terminal 1
git clone <repo>
cd faqchatbot-claude
make up

# Terminal 2 (while Terminal 1 runs)
make pull-models      # Wait ~3 minutes for downloads
make ingest          # ~30 seconds
make chat            # Start chatting!
```

---

## Architecture

| Component | Purpose |
|-----------|---------|
| **Ingestion** | Load FAQ → Generate embeddings → Store in Qdrant |
| **Retrieval** | Embed user question → Semantic search → Score threshold |
| **Generation** | Grounded answer from FAQ context or fallback |
| **UI** | Terminal chat loop (plain input/output, no external dependencies) |

**Models:**
- **Generation:** `qwen3.5:9b` (LLM for answer generation)
- **Embedding:** `nomic-embed-text-v2-moe` (for semantic search)
- **Vector Store:** Qdrant (distributed vector database)
- **Ingestion:** `faqchatbot` (loads and embeds FAQ data)

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
  └── ui/                # Terminal chat interface

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

1. **UI is thin** — plain terminal interface, no external dependencies
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
FAQ_CHATBOT_OLLAMA_GENERATE_MODEL=qwen3.5:9b
FAQ_CHATBOT_OLLAMA_EMBEDDING_MODEL=nomic-embed-text-v2-moe
FAQ_CHATBOT_QDRANT_URL=http://localhost:6333
FAQ_CHATBOT_TOP_K=3
FAQ_CHATBOT_SCORE_THRESHOLD=0.50
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
- Terminal UI (plain terminal interface)

149 tests passing. Production-ready.

---

**Get started**: See [Quick Start](#start-the-chatbot--complete-guide-) above 🚀
