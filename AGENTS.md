# Development Notes (German)

Schneller Einstieg für den FAQ-Chatbot.

## Projekt in einem Satz

Lokaler, terminalbasierter FAQ-RAG-Chatbot mit Plain Terminal UI, Ollama und Qdrant.

## Status

**Phase 1–8: VOLLSTÄNDIG ✅**

- 161 Tests bestehen
- Grid Search: alle 6 Kombinationen erzielen 1.000 mit `qwen3.5:9b`
- Neue Defaults: `top_k=3`, `threshold=0.60`, `temp=0.20`

## Einstieg

1. `CLAUDE.md` lesen (English, ausführlich)
2. `README.md` lesen (Schnellstart)
3. `docs/PROJECT-DEFINITION.md` lesen (Scope)
4. `make test` — Tests bestehen?
5. `make health` — Services erreichbar?

## Architektur-Regeln

- UI ist dünn
- Ingestion ist separater Schritt
- Retrieval entscheidet zuerst, Generation danach
- Embedding-Modell für Ingestion und Query identisch
- Config zentral
- Backend-Fehler → User-Meldungen

## Nächster Schritt

Neue Phase starten mit `make test` → TDD.

---

Siehe `CLAUDE.md` (English) für vollständige Entwicklungs-Anleitung.
