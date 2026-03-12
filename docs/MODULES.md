# Module Breakdown

## Module Map

| Module | Purpose | Target Area | Depends On |
| --- | --- | --- | --- |
| 01 - Foundation and Configuration | Project skeleton, settings, logging, shared conventions | `pyproject.toml`, `app/config.py`, `app/logging.py`, `.env.example` | None |
| 02 - FAQ Data and Repository | FAQ schema, validation, loading, repository access | `data/faq.json`, `app/domain/`, `app/repositories/` | 01 |
| 03 - External Service Clients | Ollama and Qdrant client wrappers | `app/infrastructure/` | 01 |
| 04 - Ingestion Pipeline | FAQ validation plus upsert into Qdrant | `scripts/ingest.py`, `app/services/ingestion_service.py` | 02, 03 |
| 05 - Retrieval Engine | Query embedding, similarity search, threshold decision | `app/services/retriever.py`, `app/services/vector_store_service.py` | 02, 03 |
| 06 - Answer Generation | Grounded prompting and fallback-aware answer generation | `app/services/answer_service.py` | 03, 05 |
| 07 - Chat Application Service | End-to-end orchestration of a chat turn | `app/services/chat_application.py` | 05, 06 |
| 08 - Terminal UI | Textual app, widgets, user interaction | `app/ui/` | 07 |
| 09 - Runtime and Deployment | Docker assets, startup flow, environment wiring | `Dockerfile`, `docker-compose.yml`, runtime docs | 01, 03, 04, 07 |
| 10 - Quality Assurance and Delivery | Tests, smoke checks, README, architecture docs | `tests/`, `README.md`, `docs/` | 04, 05, 06, 07, 08, 09 |

## Module Boundaries

### 01 - Foundation and Configuration

This module establishes the project package structure, settings model, logging setup, and shared defaults. Nothing in the system should read raw environment variables directly outside this module.

### 02 - FAQ Data and Repository

This module owns the FAQ schema and loading logic. It converts raw JSON into validated domain objects that the rest of the system can consume safely.

### 03 - External Service Clients

This module isolates Ollama and Qdrant integration details. Higher-level services should not manage raw HTTP or client configuration directly.

### 04 - Ingestion Pipeline

This module is the offline write path into Qdrant. It is responsible for transforming validated FAQ entries into stored vector records.

### 05 - Retrieval Engine

This module is the core retrieval boundary. It turns a user question into a ranked FAQ result plus a confidence decision.

### 06 - Answer Generation

This module turns a validated retrieval result into a grounded answer. It must not bypass retrieval or answer from broad model knowledge.

### 07 - Chat Application Service

This module composes retrieval and answer generation into a UI-independent chat turn. It is the main business-logic facade for any interface.

### 08 - Terminal UI

This module handles Textual-specific interaction and rendering. It should not contain business rules about retrieval or prompting.

### 09 - Runtime and Deployment

This module defines how the app is started and wired in local and Docker-based environments. It includes service URLs, health assumptions, and runtime instructions.

### 10 - Quality Assurance and Delivery

This module ensures the project is testable, reviewable, and runnable by others. It covers automated checks, smoke tests, and documentation.

## Integration Order

1. Build the shared foundation first.
2. Lock the FAQ schema and repository behavior.
3. Isolate external service clients.
4. Implement ingestion before chat runtime features.
5. Implement retrieval before prompting.
6. Add answer generation after retrieval is stable.
7. Add the application service before the UI.
8. Add the Textual UI as a thin final adapter.
9. Finish deployment assets after runtime wiring is clear.
10. Close with tests, smoke checks, and final docs.

## Cross-Cutting Rules

- Keep generation and embedding models configurable and separate.
- Use the same embedding model for ingestion and query embedding.
- Make threshold, top-k, URLs, and collection name configurable.
- Keep fallback behavior deterministic and testable.
- Translate backend failures into controlled UI messages.
- Do not move business logic into the UI layer.

## Module Briefs

- [modules/01-foundation-and-configuration.md](modules/01-foundation-and-configuration.md)
- [modules/02-faq-data-and-repository.md](modules/02-faq-data-and-repository.md)
- [modules/03-external-service-clients.md](modules/03-external-service-clients.md)
- [modules/04-ingestion-pipeline.md](modules/04-ingestion-pipeline.md)
- [modules/05-retrieval-engine.md](modules/05-retrieval-engine.md)
- [modules/06-answer-generation.md](modules/06-answer-generation.md)
- [modules/07-chat-application-service.md](modules/07-chat-application-service.md)
- [modules/08-terminal-ui.md](modules/08-terminal-ui.md)
- [modules/09-runtime-and-deployment.md](modules/09-runtime-and-deployment.md)
- [modules/10-quality-assurance-and-delivery.md](modules/10-quality-assurance-and-delivery.md)
