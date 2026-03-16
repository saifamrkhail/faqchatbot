# Runtime and Deployment Guide (Phase 9)

## Ziel

Reproduzierbarer Betrieb des FAQ-Chatbots in zwei Modi:

1. Lokal mit Python/uv
2. Docker-basiert mit App-Container, Qdrant-Container und Ollama auf dem Host

## Laufzeitkomponenten

- **App**: `faqchatbot` (`app.cli:main`)
- **Ingestion**: `python -m scripts.ingest`
- **Vector Store**: Qdrant
- **LLM/Embeddings**: Ollama

## Lokaler Betrieb

1. Abhängigkeiten installieren:

```bash
uv sync
```

2. Konfiguration bereitstellen:

```bash
cp .env.example .env
```

3. Sicherstellen, dass Ollama auf dem Host läuft und die Pflichtmodelle vorhanden sind:

```bash
./scripts/pull_host_ollama_models.sh
```

Pflichtmodelle:

- `qwen3.5:9b`
- `nomic-embed-text-v2-moe`

4. Ingestion ausführen:

```bash
uv run python -m scripts.ingest
```

5. App starten:

```bash
uv run faqchatbot --tui
```

## Docker-Betrieb

### Voraussetzungen

```bash
./scripts/pull_host_ollama_models.sh
docker compose up -d qdrant
```

Der Compose-Stack startet nur die App und Qdrant. Ollama bleibt bewusst auf dem Host,
damit kein zweiter Ollama-Container mit bestehenden Host-Setups kollidiert.

Die App- und Ingest-Container sprechen standardmaessig mit
`http://host.docker.internal:11434`. Auf Linux kann es noetig sein, Ollama mit
`OLLAMA_HOST=0.0.0.0:11434 ollama serve` zu exponieren.

### App starten

```bash
docker compose run --rm --build app
```

### Ingestion als One-Off

```bash
docker compose run --rm --build ingest
```

## Konfigurationsstrategie

Alle Settings kommen zentral aus `AppSettings` (`app/config.py`) mit Prefix `FAQ_CHATBOT_`.

Wichtige Runtime-Variablen:

- `FAQ_CHATBOT_FAQ_DATA_PATH`
- `FAQ_CHATBOT_QDRANT_URL`
- `FAQ_CHATBOT_OLLAMA_BASE_URL`
- `FAQ_CHATBOT_OLLAMA_GENERATE_MODEL`
- `FAQ_CHATBOT_OLLAMA_EMBEDDING_MODEL`
- `FAQ_CHATBOT_OLLAMA_ENABLE_THINKING`
- `FAQ_CHATBOT_TOP_K`
- `FAQ_CHATBOT_SCORE_THRESHOLD`
- `FAQ_CHATBOT_FALLBACK_MESSAGE`

## Betriebsnotizen

- Ingestion bleibt ein separater Schritt (nicht im App-Start versteckt).
- Embedding-Modell für Ingestion und Query muss identisch sein.
- Bei Retrieval unterhalb Threshold liefert der Bot deterministisch die Fallback-Antwort.
- Im Compose-Stack laeuft Qdrant `v1.17.0` containerisiert.
- Ollama ist eine Host-Voraussetzung und wird nicht im Compose-Stack gestartet.
- Die benoetigten Host-Modelle sind `qwen3.5:9b` und `nomic-embed-text-v2-moe`.
- Das Hilfsskript `scripts/pull_host_ollama_models.sh` zieht diese Modelle auf dem Host.
