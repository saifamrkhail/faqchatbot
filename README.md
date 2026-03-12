# FAQ Chatbot

A local, terminal-based FAQ chatbot that uses semantic retrieval over a curated FAQ dataset and only generates grounded answers when a relevant FAQ match exists.
For further details see `docs/` directory.

## Entwicklungsstand

- Phase 1 / Modul 01 ist umgesetzt.
- Phase 2 / Module 02 und 03 sind umgesetzt.
- Phase 3 / Modul 04 ist umgesetzt.
- Das Projekt besitzt jetzt zentrale Konfiguration, Logging, CLI, ein validiertes FAQ-Datenmodell, Repository-Zugriff, Ollama- und Qdrant-Clients sowie eine separate Ingestion-Pipeline.
- Offizieller Python-Start: `python -m app`
- Offizieller `uv`-Start nach Sync: `uv run faqchatbot`
- FAQ-Ingestion: `python -m scripts.ingest`
- Der aktuelle Teststand liegt bei `37 passed`.
- Der naechste Implementierungsschritt ist Phase 4 / Modul 05 Retrieval Engine.

## FAQ-Daten

- Die kuratierte Wissensbasis liegt in `data/faq.json`.
- Die Datei wurde aus `data/faq.txt` in ein maschinenlesbares JSON-Format ueberfuehrt.
- Jede FAQ besitzt jetzt eine eindeutig validierte `id`, damit Ingestion und spaetere Retrieval-Ergebnisse stabil referenzierbar bleiben.
- Der Zugriff erfolgt ueber `app/repositories/faq_repository.py`; der Rest des Systems arbeitet nur mit validierten Domainobjekten aus `app/domain/faq.py`.

## Wichtige Konfiguration

- `FAQ_CHATBOT_FAQ_DATA_PATH` steuert den Pfad zur FAQ-JSON-Datei.
- `FAQ_CHATBOT_OLLAMA_BASE_URL`, `FAQ_CHATBOT_OLLAMA_GENERATE_MODEL`, `FAQ_CHATBOT_OLLAMA_EMBEDDING_MODEL` und `FAQ_CHATBOT_OLLAMA_TIMEOUT_SECONDS` steuern Ollama.
- `FAQ_CHATBOT_QDRANT_URL`, `FAQ_CHATBOT_QDRANT_COLLECTION_NAME` und `FAQ_CHATBOT_QDRANT_TIMEOUT_SECONDS` steuern Qdrant.
- Relative Pfade wie `data/faq.json` werden gegen das Projektverzeichnis aufgeloest und haengen nicht vom aktuellen Working Directory ab.
- Ingestion und spaeteres Query-Embedding muessen dasselbe Embedding-Modell verwenden.

# Usage

## Python starten

Dieses Projekt nutzt `uv` und Python 3.11.

```bash
source .venv/bin/activate
python --version
python -m app
```

Alternativ mit `uv`:

```bash
uv sync
uv run faqchatbot
```

Der Start ueber `python -m app` oder `uv run faqchatbot` validiert aktuell die Konfiguration und zeigt den Core-Service-Status an. Der interaktive Chat-Loop folgt erst in spaeteren Phasen.

## FAQ ingestieren

Die Ingestion ist ein separater Offline-Schritt. Dafuer muessen Ollama und Qdrant ueber die konfigurierte URL erreichbar sein.

```bash
.venv/bin/python -m scripts.ingest
```

Alternativ mit `uv`:

```bash
uv run python -m scripts.ingest
```

## Tests ausfuehren

```bash
.venv/bin/python -m pytest
```

Alternativ mit `uv`:

```bash
UV_CACHE_DIR=.uv-cache uv run --no-sync pytest
```
