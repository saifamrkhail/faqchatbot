# Quality Assurance and Delivery (Phase 10)

## Ziel

Projekt handoff-ready machen durch verlässliche Checks, Smoke-Pfade und konsistente Doku.

## Qualitätstore

- **Unit Tests** für Domain, Repository, Infrastruktur, Services und UI.
- **Integrations-/Smoke-Tests** für den Haupt-Chat-Flow.
- **Dokumentationskonsistenz** zwischen README, Plan und Moduldokumenten.

## Neue Phase-10-Maßnahmen

1. Smoke-Test für einen vollständigen Chat-Flow mit kontrollierten Fakes (`tests/test_smoke_chat_flow.py`).
2. Runtime-Artefakt-Checks für `Dockerfile`, `docker-compose.yml` und `.dockerignore` (`tests/test_runtime_assets.py`).
3. Aktualisierte Nutzerdokumentation in `README.md`.
4. Laufzeit-Dokumentation in `docs/RUNTIME-DEPLOYMENT.md`.

## Verifikation

Empfohlener Hauptcheck:

```bash
.venv/bin/python -m pytest
```

Die Smoke- und Runtime-Asset-Tests laufen innerhalb der regulären Test-Suite mit.

## Delivery-Status

- Phasen 1 bis 10: abgeschlossen.
- Runtime/Deployment und QA/Delivery: umgesetzt und getestet.
- Projektstatus, Setup und Betriebsabläufe sind dokumentiert.
