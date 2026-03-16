# Runtime and Deployment

Two deployment modes: local (Python) or Docker.

## Local Development

```bash
uv sync
make pull-models      # Pull qwen3.5:9b and nomic-embed-text-v2-moe on host
make up               # Start Qdrant in Docker
make ingest-local     # Ingest FAQ locally
make run-local        # Run chatbot locally
make test             # Verify
```

Requirements:
- Ollama running on host (`http://localhost:11434`)
- Models: `qwen3.5:9b`, `nomic-embed-text-v2-moe`
- Python 3.11+, `uv`

## Docker Deployment

```bash
make pull-models      # Pull models on host (prerequisite)
make up               # Start Qdrant container
make ingest           # Ingest FAQ in Docker
make chat             # Run app in Docker
```

**Note**: Ollama stays on the host. App/ingest containers use `http://host.docker.internal:11434`.

On Linux, expose Ollama: `OLLAMA_HOST=0.0.0.0:11434 ollama serve`

## Configuration

All settings via `FAQ_CHATBOT_*` environment variables (centralized in `app/config.py`).

Key defaults (from grid search evaluation):
```
FAQ_CHATBOT_TOP_K=3
FAQ_CHATBOT_SCORE_THRESHOLD=0.60
FAQ_CHATBOT_OLLAMA_GENERATE_TEMPERATURE=0.2
FAQ_CHATBOT_OLLAMA_GENERATE_MODEL=qwen3.5:9b
FAQ_CHATBOT_OLLAMA_EMBEDDING_MODEL=nomic-embed-text-v2-moe
FAQ_CHATBOT_QDRANT_URL=http://localhost:6333
```

See `.env.example` for all options.

## Architecture Notes

- **Ingestion is separate** — not coupled to chat startup
- **Same embedding model** for ingestion and queries
- **Threshold-based retrieval** — deterministic fallback if score < threshold
- **Qdrant v1.17.0** containerized
- **Ollama on host** — avoids duplicate container conflicts
- **Configuration centralized** — no scattered env reads

## Files

| File | Purpose |
|------|---------|
| `Makefile` | Development and deployment tasks |
| `Dockerfile` | App container image |
| `docker-compose.yml` | Qdrant + app stack |
| `scripts/pull_host_ollama_models.sh` | Bootstrap host Ollama models |
| `.env.example` | Configuration template |

---

**See `README.md` for quickstart. See `CLAUDE.md` for development guide.**
