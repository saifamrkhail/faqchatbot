# Runtime and Deployment Guide (Phase 9)

## Ziel

Reproduzierbarer Betrieb des FAQ-Chatbots in zwei Modi:

1. Lokal mit Python/uv
2. Docker-basiert mit Qdrant-Container und externer Ollama-Instanz

## Laufzeitkomponenten

- **App**: `faqchatbot` (`app.cli:main`)
- **Ingestion**: `python -m scripts.ingest`
- **Vector Store**: Qdrant
- **LLM/Embeddings**: Ollama (extern, hostseitig)

## Lokaler Betrieb

1. Abhängigkeiten installieren:

```bash
uv sync
```

2. Konfiguration bereitstellen:

```bash
cp .env.example .env
```

3. Ingestion ausführen:

```bash
uv run python -m scripts.ingest
```

4. App starten:

```bash
uv run faqchatbot --tui
```

## Docker-Betrieb

### App + Qdrant starten

```bash
docker compose up --build app qdrant
```

### Ingestion als One-Off

```bash
docker compose run --rm ingest
```

## Konfigurationsstrategie

Alle Settings kommen zentral aus `AppSettings` (`app/config.py`) mit Prefix `FAQ_CHATBOT_`.

Wichtige Runtime-Variablen:

- `FAQ_CHATBOT_FAQ_DATA_PATH`
- `FAQ_CHATBOT_QDRANT_URL`
- `FAQ_CHATBOT_OLLAMA_BASE_URL`
- `FAQ_CHATBOT_OLLAMA_GENERATE_MODEL`
- `FAQ_CHATBOT_OLLAMA_EMBEDDING_MODEL`
- `FAQ_CHATBOT_TOP_K`
- `FAQ_CHATBOT_SCORE_THRESHOLD`
- `FAQ_CHATBOT_FALLBACK_MESSAGE`

## Betriebsnotizen

- Ingestion bleibt ein separater Schritt (nicht im App-Start versteckt).
- Embedding-Modell für Ingestion und Query muss identisch sein.
- Bei Retrieval unterhalb Threshold liefert der Bot deterministisch die Fallback-Antwort.
- In Docker wird Ollama standardmäßig über `host.docker.internal` angesprochen.
