# FAQ Chatbot

A local, terminal-based FAQ RAG chatbot with plain **Terminal UI**, **Ollama** (embeddings & generation), and **Qdrant** (vector store).

The bot answers questions **only from FAQ context** and returns a deterministic fallback message when confidence is low.

---

## Quick Start 🚀

### Prerequisites
- **Docker** & **Docker Compose** (v2.0+)
- **Ollama** installed and running on the **host machine**
- Host Ollama must have `qwen3.5:9b` and `nomic-embed-text-v2-moe` available
- **Python 3.11+** and **uv** for local development

---

## Start the Chatbot — Complete Guide 🚀

### **Step 0: Prerequisites**

Make sure you have:
- **Docker & Docker Compose** (v2.0+)
- ~5 GB free disk space
- **Ollama running on the host machine**
- Internet connection (first model pull only)

### **Step 1: Clone & Navigate**

```bash
git clone https://github.com/saifamrkhail/faqchatbot.git
cd faqchatbot
```

### **Step 2: Pull the Required Ollama Models on the Host**

**Open Terminal 1:**

```bash
make pull-models
```

**What happens:**
- Runs `ollama pull qwen3.5:9b` on the host machine
- Runs `ollama pull nomic-embed-text-v2-moe` on the host machine
- Verifies the required models against the host Ollama instance

The helper script is [`scripts/pull_host_ollama_models.sh`](/home/saif/faqchatbot-codex/scripts/pull_host_ollama_models.sh).

⏱️ **This takes 2-5 minutes on first run** (~2 GB download)

**Verify models installed:**
```bash
make models
```

You should see both models listed on the host Ollama instance.

### **Step 3: Start Qdrant in Docker**

**Open Terminal 2:**

```bash
make up
```

**What happens:**
- Starts **Qdrant** (vector database) on `http://localhost:6333`
- Leaves **Ollama** on the host machine to avoid a second Ollama container
- Runs in **background** so you can keep using Terminal 2

**Wait 10-15 seconds** for Qdrant to become healthy.

### **Step 4: Ingest FAQ Data**

```bash
make ingest
```

**What happens:**
- Loads 10 sample German FAQ entries from `data/faq.json`
- Generates embeddings through **host Ollama**
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
- Starts the app inside Docker
- Connects to **Qdrant in Docker**
- Connects to **Ollama on the host machine**
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
| `make pull-models` | Pull `qwen3.5:9b` and `nomic-embed-text-v2-moe` on host Ollama |
| `make up` | Start Qdrant in Docker |
| `make ingest` | Load FAQ data into Qdrant |
| `make chat` | Run the app container against host Ollama |
| `make test` | Run the test suite |
| `make logs` | View app logs |
| `make ps` | Show container status |
| `make down` | Stop all services |
| `make clean` | Stop & delete all data |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Models not found (404)** | Run `make pull-models` on the host machine |
| **App container cannot reach Ollama** | Verify `curl http://localhost:11434/api/tags` works on the host. On Linux, restart Ollama with `OLLAMA_HOST=0.0.0.0:11434 ollama serve` if needed. |
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

# 2. Make sure Ollama is running on the host
make pull-models

# 3. Start Qdrant in Docker
make up

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
cd faqchatbot
make pull-models
make up

# Terminal 2
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
  ├── ingest.py          # Standalone ingestion script
  └── pull_host_ollama_models.sh  # Host-side Ollama model bootstrap

data/
  └── faq.json           # Sample FAQ (10 German entries)

tests/                   # Automated test suite
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

**Status**: run `make test` for the current verified test suite.

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
# Local runtime
FAQ_CHATBOT_OLLAMA_BASE_URL=http://localhost:11434
FAQ_CHATBOT_QDRANT_URL=http://localhost:6333

# Docker app container
# FAQ_CHATBOT_OLLAMA_BASE_URL=http://host.docker.internal:11434
# FAQ_CHATBOT_QDRANT_URL=http://qdrant:6333

# Required models on host Ollama
FAQ_CHATBOT_OLLAMA_GENERATE_MODEL=qwen3.5:9b
FAQ_CHATBOT_OLLAMA_EMBEDDING_MODEL=nomic-embed-text-v2-moe
FAQ_CHATBOT_TOP_K=3
FAQ_CHATBOT_SCORE_THRESHOLD=0.50
FAQ_CHATBOT_FALLBACK_MESSAGE="Leider konnte ich Ihre Frage nicht verstehen."
```

See `.env.example` for defaults.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Host Ollama not reachable | `curl http://localhost:11434/api/tags` and restart Ollama on the host |
| Qdrant refused | `curl http://localhost:6333/health` / restart services |
| Model not found | `make pull-models` or `OLLAMA_HOST=http://localhost:11434 ollama list` |
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

Deployment target: app in Docker, Qdrant in Docker, Ollama on the host machine.

---

**Get started**: See [Quick Start](#start-the-chatbot--complete-guide-) above 🚀
