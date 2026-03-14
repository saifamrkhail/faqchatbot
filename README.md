# FAQ Chatbot

Lokaler, terminalbasierter FAQ-RAG-Chatbot mit Textual, Ollama und Qdrant.
Der Bot beantwortet Fragen nur aus FAQ-Kontext und nutzt bei unsicherem Retrieval eine deterministische Fallback-Antwort.

## Projektstatus

- ✅ Phase 1 bis 10 sind umgesetzt.
- ✅ Kernsystem (Ingestion, Retrieval, Answer Generation, Chat-Service, TUI) ist implementiert.
- ✅ Docker-Containerisierung vollständig konfiguriert.
- ✅ Test- und Smoke-Checks sind integriert.

## Architektur auf einen Blick

- `app/config.py`: zentrale Runtime-Konfiguration aus Env-Variablen.
- `app/repositories/faq_repository.py`: validierter Zugriff auf `data/faq.json`.
- `app/services/ingestion_service.py`: separater Ingestion-Workflow nach Qdrant.
- `app/services/retriever.py`: Query-Embedding und Vektor-Retrieval.
- `app/services/answer_generator.py`: grounded Antwortgenerierung + Fallback.
- `app/services/chat_service.py`: Orchestrierung einer vollständigen Chat-Anfrage.
- `app/ui/`: Textual-TUI als dünne UI-Schicht.

---

## 🐳 Docker-Setup (Empfohlen)

### Voraussetzungen

- **Docker Engine** (v20.10+) - [Installation Guide](https://docs.docker.com/engine/install/)
- **Docker Compose** (v2.0+) - meist mit Docker Desktop bereits enthalten
- **~5 GB freier Speicherplatz** (für Ollama-Modelle)
- **Internetverbindung** (für Model-Downloads)

### Schnellstart mit Docker

#### 1. Überprüfen Sie Docker-Installation

```bash
docker --version
docker compose version
```

#### 2. Starten Sie alle Services (Ollama, Qdrant, App)

```bash
# Bauen Sie das App-Image und starten Sie alle Services
docker compose up --build

# Oder im Hintergrund:
docker compose up -d
```

Dies startet automatisch:
- **Ollama** (http://localhost:11434) - LLM und Embedding-Service
- **Qdrant** (http://localhost:6333) - Vektor-Datenbank
- **App Container** - Chatbot-Anwendung

#### 3. Ingestion durchführen (Daten in Qdrant laden)

```bash
# In separatem Terminal
docker compose run --rm ingest

# Oder mit Logs
docker compose run --rm ingest 2>&1 | tail -20
```

Dieses Kommando:
- Lädt 10 FAQ-Einträge aus `data/faq.json`
- Generiert Embeddings mit Ollama (nomic-embed-text)
- Speichert sie in Qdrant

#### 4. Starten Sie die Chatbot-TUI

```bash
# Terminal-UI öffnen
docker compose up app

# Oder mit Live-Logs
docker compose logs -f app
```

Die TUI wird im Terminal angezeigt. Geben Sie Fragen ein wie:
- "Welche IT-Dienstleistungen bieten Sie an?"
- "What support options are available?"
- "Wie geht ihr mit Cybersecurity um?"

### Docker-Konfiguration

| Service | Port | URL | Funktion |
|---------|------|-----|----------|
| **Ollama** | 11434 | http://localhost:11434 | LLM + Embeddings |
| **Qdrant** | 6333 | http://localhost:6333 | Vector Store |
| **App** | – | In Terminal | TUI Chatbot |

### Modelle

| Modell | Größe | Zweck |
|--------|-------|-------|
| **qwen3.5:0.8b** | 1.0 GB | Antwortgenerierung |
| **nomic-embed-text** | 274 MB | Text-Embeddings |

*Hinweis: Modelle werden beim ersten Start automatisch heruntergeladen (~1-2 Minuten)*

### Nützliche Docker-Kommandos

```bash
# Status aller Services prüfen
docker compose ps

# Logs eines Services ansehen
docker compose logs -f ollama
docker compose logs -f qdrant
docker compose logs -f app

# Alle Services stoppen
docker compose down

# Services stoppen und Daten löschen
docker compose down -v

# App-Container neu bauen
docker compose build

# Modelle in Ollama prüfen
docker exec faqchatbot-claude-ollama-1 ollama list

# Qdrant-Dashboard im Browser
# http://localhost:6333/dashboard
```

---

## 💻 Lokales Setup (ohne Docker)

### Voraussetzungen

- Python 3.11+
- `uv` Paketmanager ([Installation](https://docs.astral.sh/uv/))
- Ollama lokal laufend (`http://localhost:11434`)
- Qdrant lokal laufend (`http://localhost:6333`)

### Installation

```bash
# Abhängigkeiten installieren
uv sync

# .env-Datei erstellen (optional)
cp .env.example .env
```

### FAQ-Daten ingestieren

```bash
uv run python -m scripts.ingest
```

### Anwendung starten

Statusmodus:

```bash
uv run faqchatbot
```

TUI starten:

```bash
uv run faqchatbot --tui
```

### Wichtige Runtime-Parameter

Setzen Sie diese Umgebungsvariablen zum Konfigurieren:

```bash
export FAQ_CHATBOT_OLLAMA_GENERATE_MODEL=qwen3.5:0.8b
export FAQ_CHATBOT_OLLAMA_EMBEDDING_MODEL=nomic-embed-text
export FAQ_CHATBOT_TOP_K=3
export FAQ_CHATBOT_SCORE_THRESHOLD=0.70
export FAQ_CHATBOT_FALLBACK_MESSAGE="Leider konnte ich Ihre Frage nicht verstehen."
```

---

## 🧪 Qualitätssicherung

### Tests ausführen

Alle Tests:

```bash
# Mit uv
UV_CACHE_DIR=.uv-cache uv run --no-sync pytest

# Oder mit venv
.venv/bin/python -m pytest
```

### Test-Statistik

```
Phase 1 (Foundation):        7 Tests ✓
Phase 2 (FAQ Domain):        6 Tests ✓
Phase 3 (Clients):          10 Tests ✓
Phase 4 (Ingestion):         7 Tests ✓
Phase 5 (Retrieval):        30 Tests ✓
Phase 6 (Generation):       32 Tests ✓
Phase 7 (Chat Service):     41 Tests ✓
Phase 8 (TUI):              16 Tests ✓
─────────────────────────────────────
Total:                     149 Tests ✓
```

---

## 🔧 Troubleshooting

### Docker-bezogen

**Problem: "Ollama request timed out"**
```bash
# Überprüfen, ob Ollama läuft
docker compose logs ollama | tail -20

# Ollama neustarten
docker compose restart ollama
```

**Problem: "Qdrant connection refused"**
```bash
# Qdrant-Health prüfen
curl http://localhost:6333/health

# Services neustarten
docker compose down && docker compose up -d
```

**Problem: "Model not found"**
```bash
# Modelle neu laden
docker exec faqchatbot-claude-ollama-1 ollama pull qwen3.5:0.8b
docker exec faqchatbot-claude-ollama-1 ollama pull nomic-embed-text
```

### Lokal-bezogen

**Problem: "ModuleNotFoundError"**
```bash
# Abhängigkeiten neu installieren
uv sync --force
```

**Problem: "Connection refused" zu Ollama/Qdrant**
```bash
# Stellen Sie sicher, dass Services laufen
# Ollama: ollama serve
# Qdrant: docker run -p 6333:6333 qdrant/qdrant
```

---

## 📚 Weiterführende Dokumentation

- `docs/PROJECT-DEFINITION.md` - Projektdefinition und Anforderungen
- `docs/MODULES.md` - Modulbeschreibungen
- `docs/IMPLEMENTATION-PLAN.md` - Implementierungsplan für alle Phasen
- `docs/RUNTIME-DEPLOYMENT.md` - Runtime- und Deployment-Richtlinien
- `docs/QA-DELIVERY.md` - QA und Delivery-Prozess

---

## 📋 Dateistruktur

```
faqchatbot-claude/
├── Dockerfile              # App-Container-Definition
├── docker-compose.yml      # Multi-Service Orchestration
├── pyproject.toml         # Python-Abhängigkeiten
├── app/
│   ├── config.py          # Zentrale Konfiguration
│   ├── cli.py             # CLI-Einstiegspunkt
│   ├── domain/            # Domain-Modelle
│   ├── repositories/      # Data Access Layer
│   ├── services/          # Business Logic
│   ├── infrastructure/    # External Service Clients
│   └── ui/                # Textual TUI
├── scripts/
│   └── ingest.py          # FAQ-Ingestion Script
├── data/
│   └── faq.json           # FAQ-Daten (10 German entries)
├── tests/                 # Unit & Integration Tests
└── docs/                  # Dokumentation
```

---

## 🚀 Nächste Schritte

1. **Mit Docker starten**: `docker compose up --build`
2. **FAQ ingestieren**: `docker compose run --rm ingest`
3. **Chatbot testen**: `docker compose up app`
4. **Fragen stellen**: Geben Sie FAQ-bezogene Fragen ein

---

**Viel Erfolg mit dem FAQ Chatbot! 🎉**
