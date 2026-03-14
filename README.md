# FAQ Chatbot

Lokaler, terminalbasierter FAQ-RAG-Chatbot mit Textual, Ollama und Qdrant.
Der Bot beantwortet Fragen nur aus FAQ-Kontext und nutzt bei unsicherem Retrieval eine deterministische Fallback-Antwort.

## Projektstatus

- Phase 1 bis 10 sind umgesetzt.
- Kernsystem (Ingestion, Retrieval, Answer Generation, Chat-Service, TUI) ist implementiert.
- Runtime/Deployment-Artefakte (`Dockerfile`, `docker-compose.yml`) sind vorhanden.
- Test- und Smoke-Checks sind integriert.

## Architektur auf einen Blick

- `app/config.py`: zentrale Runtime-Konfiguration aus Env-Variablen.
- `app/repositories/faq_repository.py`: validierter Zugriff auf `data/faq.json`.
- `app/services/ingestion_service.py`: separater Ingestion-Workflow nach Qdrant.
- `app/services/retriever.py`: Query-Embedding und Vektor-Retrieval.
- `app/services/answer_generator.py`: grounded Antwortgenerierung + Fallback.
- `app/services/chat_service.py`: Orchestrierung einer vollständigen Chat-Anfrage.
- `app/ui/`: Textual-TUI als dünne UI-Schicht.

## Voraussetzungen

- Python 3.11
- `uv` (empfohlen)
- Laufende Instanzen von:
  - Ollama (`http://localhost:11434`)
  - Qdrant (`http://localhost:6333`)

## Setup (lokal)

```bash
uv sync
cp .env.example .env
```

## FAQ-Daten ingestieren

```bash
uv run python -m scripts.ingest
```

## Anwendung starten

Statusmodus:

```bash
uv run faqchatbot
```

TUI starten:

```bash
uv run faqchatbot --tui
```

## Docker-Setup

Qdrant + App-TUI starten:

```bash
docker compose up --build app qdrant
```

Ingestion als One-Off ausführen:

```bash
docker compose run --rm ingest
```

Hinweis: Ollama wird standardmäßig **extern** auf dem Host erwartet (`host.docker.internal:11434`).

## Qualitätssicherung

Alle Tests:

```bash
.venv/bin/python -m pytest
```

Mit `uv`:

```bash
UV_CACHE_DIR=.uv-cache uv run --no-sync pytest
```

## Weiterführende Doku

- `docs/PROJECT-DEFINITION.md`
- `docs/MODULES.md`
- `docs/IMPLEMENTATION-PLAN.md`
- `docs/RUNTIME-DEPLOYMENT.md`
- `docs/QA-DELIVERY.md`
