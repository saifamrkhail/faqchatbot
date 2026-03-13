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
- `app/config.py`, `app/logging.py` und `app/cli.py` sind vorhanden.
- Das Kernsystem mit Embedding, Retrieval Service, Answer Generator und der Chat-Pipeline existiert.
- Die Kommandozeile (`app/cli.py`) bietet eine CLI und eine TUI.
- Der offizielle `uv`-Entry-Point fuer die App ist weiterhin `uv sync && uv run faqchatbot`.
- `tests/` deckt jetzt Config, Logging, CLI, FAQ-Domain, Repository, Infrastruktur, Pipeline und das TUI ab.
- Der letzte verifizierte Teststand liegt bei `114 passed`.
- Der naechste fachliche Implementierungsschritt ist Phase 9 / Modul 09 Runtime and Deployment.

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

## Detaillierter Umsetzungsplan fuer Phase 2 und 3

### Phase 2 - FAQ Data and Repository plus External Service Clients

Ziel:

- stabile FAQ-Domainobjekte
- validierter Datenzugriff ohne Roh-JSON im Rest des Systems
- kleine, kontrollierte Integrationsgrenzen fuer Ollama und Qdrant

Status:

- abgeschlossen

Arbeitspakete Modul 02:

1. `data/faq.json` aus dem bereitgestellten FAQ-Material erstellen
2. in `app/domain/faq.py` ein validiertes FAQ-Domainmodell definieren
3. klare Validierungsfehler fuer fehlende oder leere Pflichtfelder einfuehren
4. in `app/repositories/faq_repository.py` einen JSON-Loader und Repository-Zugriff implementieren
5. Repository so gestalten, dass spaetere Services nur mit Domainobjekten arbeiten
6. Tests fuer gueltige Eintraege, ungueltige Datensaetze und Repository-Ladevorgaenge schreiben

Arbeitspakete Modul 03:

1. in `app/infrastructure/ollama_client.py` einen kleinen HTTP-Client fuer Embeddings und Generierung implementieren
2. in `app/infrastructure/qdrant_client.py` einen kleinen HTTP-Client fuer Collection-Initialisierung, Upsert und Search implementieren
3. kontrollierte Fehlerklassen fuer Ollama- und Qdrant-Fehler einfuehren
4. Client-Erzeugung an `app.config.AppSettings` binden
5. Tests fuer Request-Aufbau, Antwort-Mapping und Fehlerbehandlung schreiben

Abschlusskriterien Phase 2:

- FAQ-Daten werden aus `data/faq.json` validiert geladen
- ungueltige FAQ-Datensaetze schlagen mit klaren Fehlern fehl
- Ollama- und Qdrant-Clients lassen sich aus zentraler Konfiguration instanziieren
- Infrastrukturfehler werden in kontrollierte Exceptions uebersetzt

### Phase 3 - Ingestion Pipeline

Ziel:

- validierte FAQ-Eintraege offline einlesen
- Embeddings erzeugen
- Vektoren idempotent in Qdrant schreiben

Status:

- abgeschlossen

Arbeitspakete Modul 04:

1. in `app/services/ingestion_service.py` den Ingestion-Ablauf kapseln
2. FAQ-Eintraege ueber das Repository laden
3. Embeddings ueber den Ollama-Client erzeugen
4. Qdrant-Collection bei Bedarf initialisieren oder verifizieren
5. FAQ-Eintraege mit Payload und Vektor idempotent upserten
6. Rueckgabeobjekt mit Anzahl der verarbeiteten Eintraege und Vektordimension definieren
7. `scripts/ingest.py` als separaten Entry-Point fuer die Ingestion anlegen
8. Tests fuer Orchestrierung, Collection-Bootstrap und Upsert-Verhalten schreiben

Abschlusskriterien Phase 3:

- die Ingestion kann alle FAQ-Eintraege erfolgreich verarbeiten
- wiederholtes Ausfuehren bleibt idempotent
- die ermittelte Vektordimension wird konsistent fuer die Collection verwendet
- die Ingestion ist ein separater Schritt und nicht an den Chat-Start gekoppelt

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
3. mit Phase 9 / Modul 09 Runtime and Deployment weitermachen
4. Setup validieren und Release cutten

## Nuetzliche Kommandos

- Dateien finden: `rg --files`
- Inhalte suchen: `rg -n "pattern"`
- Tests: `.venv/bin/python -m pytest`
- Tests mit `uv`: `UV_CACHE_DIR=.uv-cache uv run --no-sync pytest`
- Status-Start der App: `.venv/bin/python -m app`
- FAQ ingestieren: `.venv/bin/python -m scripts.ingest`
- Script-Entry-Point starten: `uv sync && uv run faqchatbot`
- Ingestion mit `uv`: `uv run python -m scripts.ingest`

## Nicht verzetteln

Nicht mit Textual oder Docker anfangen, bevor Retrieval, Answer Generation und Chat Application stehen.
