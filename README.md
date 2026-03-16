# FAQ Chatbot

Local terminal-based FAQ RAG chatbot. Answers questions **only from FAQ context**; returns a deterministic German fallback when confidence is low.

**Stack**: Plain terminal UI · Ollama (host) · Qdrant (Docker)

---

## Prerequisites

- Docker & Docker Compose v2+
- Ollama running on the host machine
- Python 3.11+ and `uv` (for local development only)

---

## Quickstart

**Terminal 1 — pull models and start Qdrant:**

```bash
make pull-models   # pulls qwen3.5:9b and nomic-embed-text-v2-moe on host Ollama
make up            # starts Qdrant in Docker
```

**Terminal 2 — ingest FAQ data and start chat:**

```bash
make ingest        # embed 15 FAQ entries and store in Qdrant (~30s)
make chat          # start the chatbot
```

Type your question in German. Exit with `exit` or `Ctrl+C`.

> **Re-ingest required** whenever `data/faq.json` changes.

---

## Key Commands

| Command | Purpose |
|---------|---------|
| `make pull-models` | Pull required models on host Ollama |
| `make up` | Start Qdrant in Docker |
| `make ingest` | Load FAQ data into Qdrant (via Docker) |
| `make ingest-local` | Load FAQ data locally (no Docker) |
| `make chat` | Run chatbot in Docker |
| `make run-local` | Run chatbot locally |
| `make test` | Run the test suite |
| `make health` | Check Ollama and Qdrant reachability |
| `make down` | Stop all services |
| `make clean` | Stop services and delete all data |

Use `make up USE_EXTERNAL_QDRANT=true` to reuse an existing Qdrant on port 6333 instead of starting the Docker container.

---

## Configuration

All settings via `FAQ_CHATBOT_*` environment variables. Copy `.env.example` to `.env` for local overrides. Key defaults:

| Variable | Default | Notes |
|----------|---------|-------|
| `FAQ_CHATBOT_OLLAMA_BASE_URL` | `http://localhost:11434` | Docker uses `host.docker.internal` |
| `FAQ_CHATBOT_OLLAMA_GENERATE_MODEL` | `qwen3.5:9b` | Generation LLM |
| `FAQ_CHATBOT_OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text-v2-moe` | Embedding model |
| `FAQ_CHATBOT_QDRANT_URL` | `http://localhost:6333` | Docker uses `http://qdrant:6333` |
| `FAQ_CHATBOT_SCORE_THRESHOLD` | `0.60` | Min similarity for FAQ match |
| `FAQ_CHATBOT_TOP_K` | `3` | Candidates retrieved per query |
| `FAQ_CHATBOT_OLLAMA_GENERATE_TEMPERATURE` | `0.2` | Generation temperature |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| App cannot reach Ollama | On Linux: `OLLAMA_HOST=0.0.0.0:11434 ollama serve` |
| Models not found (404) | `make pull-models` |
| Qdrant connection refused | `make health`, then `make down && make up` |
| No answers / wrong answers | `make ingest` to reload FAQ data into Qdrant |
| Local deps broken | `uv sync --force` |

---

## Local Development

```bash
uv sync
make up           # Qdrant only
make ingest-local
make test
make run-local
```

Watch mode: `make test-watch`

---

## Architecture

```
User question
  → Retriever (embed + Qdrant search + threshold)
  → AnswerGenerator (grounded prompt → Ollama streaming)
  → Terminal UI
```

| Layer | Module |
|-------|--------|
| Config | `app/config.py` |
| Domain models | `app/domain/` |
| FAQ loading | `app/repositories/` |
| Ollama & Qdrant clients | `app/infrastructure/` |
| Ingestion / Retrieval / Chat | `app/services/` |
| Terminal UI | `app/ui/` |

---

## Documentation

- `docs/PROJECT-DEFINITION.md` — scope and goals
- `docs/MODULES.md` — module boundaries
- `docs/RUNTIME-DEPLOYMENT.md` — deployment details
- `docs/IMPROVEMENT-PLAN.md` — evaluation results and implemented improvements
