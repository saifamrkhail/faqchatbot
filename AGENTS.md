# AGENTS.md

## Zweck

Schneller Projekteinstieg fuer den lokalen FAQ-Chatbot. Diese Datei ist eine kompakte Arbeitsnotiz fuer Navigation, Priorisierung und sauberes Weiterentwickeln.

## Projekt in einem Satz

Lokaler, terminalbasierter FAQ-RAG-Chatbot mit Textual, Ollama und Qdrant. Antworten nur aus FAQ-Kontext, sonst definierter Fallback.

## Erst lesen

1. `docs/PROJECT-DEFINITION.md`
2. `docs/MODULES.md`
3. `docs/IMPLEMENTATION-PLAN.md`
4. `docs/modules/`

## Aktueller Ist-Zustand

- Planung und Modulstruktur sind in `docs/` ausgearbeitet.
- Runtime-Code ist noch kaum vorhanden.
- `main.py` ist aktuell nur ein Platzhalter.
- `pyproject.toml` ist minimal und hat bisher nur Test-Dependencies im Dev-Group-Block.
- Zielstruktur aus den Docs ist noch nicht umgesetzt.

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
3. kleinstes offene Modul waehlen
4. erst Tests schreiben, dann Implementierung

## Nuetzliche Kommandos

- Dateien finden: `rg --files`
- Inhalte suchen: `rg -n "pattern"`
- Tests: `uv run pytest`
- Aktuellen Platzhalter starten: `uv run python main.py`

## Nicht verzetteln

Nicht mit Textual oder Docker anfangen, bevor Foundation, Datenmodell, Service-Clients, Ingestion und Retrieval stehen.
