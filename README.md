# FAQ Chatbot

A local, terminal-based FAQ chatbot that uses semantic retrieval over a curated FAQ dataset and only generates grounded answers when a relevant FAQ match exists.
For further details see `docs/` directory.

## Entwicklungsstand

- Phase 1 / Modul 01 ist umgesetzt.
- Das Projekt besitzt jetzt ein Python-Scaffold mit zentraler Konfiguration, Logging und CLI.
- Offizieller Python-Start: `python -m app`
- Offizieller `uv`-Start nach Sync: `uv run faqchatbot`
- Der aktuelle Teststand liegt bei `7 passed`.

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

## Tests ausfuehren

```bash
source .venv/bin/activate
pytest
```

Alternativ mit `uv`:

```bash
UV_CACHE_DIR=.uv-cache uv run --no-sync pytest
```
