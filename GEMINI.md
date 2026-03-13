# AGENTS.md

## Zweck

Schneller Projekteinstieg fuer den lokalen FAQ-Chatbot. Diese Datei ist eine kompakte Arbeitsnotiz fuer Navigation, Priorisierung und sauberes Weiterentwickeln.

## Projekt in einem Satz

Lokaler, terminalbasierter FAQ-RAG-Chatbot mit Textual, Ollama und Qdrant. Antworten nur aus FAQ-Kontext, sonst definierter Fallback.

## Erst lesen

1. `README.md`
2. `docs/PROJECT-DEFINITION.md`
3. `docs/MODULES.md`
4. `docs/IMPLEMENTATION-PLAN.md`
5. `docs/modules/`

## Aktueller Ist-Zustand

- Planung und Modulstruktur sind in `docs/` ausgearbeitet.
- Phase 1 bis 8 sind umgesetzt.
- `app/config.py`, `app/logging.py` und `app/cli.py` existieren.
- `python -m app` startet aktuell das Scaffold direkt aus der aktivierten `.venv`.
- Der offizielle `uv`-Entry-Point ist in `pyproject.toml` gesetzt: `uv sync && uv run faqchatbot --tui`.
- `tests/` deckt die Basis fuer Config, Logging, CLI, API und UI ab.
- Der letzte verifizierte Teststand liegt bei `114 passed`.
- `README.md` beschreibt den Python-Start und das Ausfuehren der Tests.
- Die fachlichen Module ab `app/domain/`, `app/repositories/`, `app/infrastructure/`, `app/services/` und `app/ui/` sind nur als leere Pakete vorbereitet.

## Source of Truth

- Scope und Produktverhalten: `docs/PROJECT-DEFINITION.md`
- Modulgrenzen: `docs/MODULES.md`
- Reihenfolge und Meilensteine: `docs/IMPLEMENTATION-PLAN.md`

## Implementierungsreihenfolge

1. Foundation and Configuration
2. FAQ Data and Repository
3. External Service Clients
4. Ingestion Pipeline
5. Retrieval Engine
6. Answer Generation
7. Chat Application Service
8. Terminal UI
9. Runtime and Deployment
10. Quality Assurance and Delivery

## Harte Architekturregeln

- UI bleibt duenn und enthaelt keine Business-Logik.
- Ingestion ist ein separater Schritt, nicht Teil des Chat-Starts.
- Retrieval entscheidet zuerst, Generierung kommt danach.
- Embedding-Modell fuer Ingestion und Query muss identisch sein.
- Generate-Modell und Embedding-Modell separat konfigurierbar halten.
- Fallback-Verhalten deterministisch halten.
- Konfiguration zentral abbilden, keine verstreuten Env-Reads.
- Backend-Fehler in kontrollierte User-Meldungen uebersetzen.

## Zielstruktur

```text
app/
  config.py
  logging.py
  domain/
  repositories/
  infrastructure/
  services/
  ui/
data/
  faq.json
scripts/
  ingest.py
tests/
docs/
```

## Naechster sinnvoller Einstieg

Wenn unklar ist, wo weitergemacht werden soll:

1. `git status --short` pruefen
2. Docs gegen aktuellen Code abgleichen
3. nach Modul 08 mit Modul 09 (Runtime and Deployment) weitermachen
4. erst Tests/Checks schreiben, dann Implementierung

## Nuetzliche Kommandos

- Dateien finden: `rg --files`
- Inhalte suchen: `rg -n "pattern"`
- Tests: `source .venv/bin/activate && pytest`
- Tests mit `uv`: `UV_CACHE_DIR=.uv-cache uv run --no-sync pytest`
- Aktuellen Platzhalter starten: `source .venv/bin/activate && python -m app`
- Script-Entry-Point starten: `uv sync && uv run faqchatbot`

## Nicht verzetteln

Nicht mit Textual oder Docker anfangen, bevor Foundation, Datenmodell, Service-Clients, Ingestion und Retrieval stehen.
