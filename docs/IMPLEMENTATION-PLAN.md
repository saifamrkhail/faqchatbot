# Overall Implementation Plan

## Planning Goal

Turn the project definition into a sequence of small, verifiable implementation steps that produce a runnable FAQ chatbot without mixing concerns.

## Key Assumptions

- The first release is a local proof of concept, not a production system.
- The FAQ dataset is small and curated, around 10 entries.
- Retrieval quality matters more than model creativity.
- Ingestion is a separate command or script, not part of application startup.
- Ollama is available through a configured base URL.
- Qdrant is available locally or through Docker.

## Current Development Status

- Phase 1 / Module 01 is complete.
- The repository now contains the application scaffold under `app/`.
- Central configuration, logging bootstrap, CLI entry logic, and `.env.example` are in place.
- The official project script is defined in `pyproject.toml` as `faqchatbot = "app.cli:main"`.
- The current verified test baseline is `7 passed`.
- The next implementation target is Phase 2, starting with the FAQ data model and repository layer.

## Phase Plan

| Phase | Modules | Objective | Main Outputs | Exit Criteria |
| --- | --- | --- | --- | --- |
| 1 | 01 | Establish the project skeleton and configuration model | package layout, settings, logging, `.env.example` | app imports cleanly and config validation works |
| 2 | 02, 03 | Define the FAQ domain and isolate external dependencies | FAQ schema, repository, Ollama client, Qdrant client | FAQ data loads and both clients can be instantiated from config |
| 3 | 04 | Build the offline ingestion path | ingestion service, ingest script, collection bootstrap | FAQ entries can be embedded and written into Qdrant |
| 4 | 05 | Build the retrieval core | query embedding, top-k search, threshold decision | relevant and irrelevant questions can be distinguished reliably |
| 5 | 06 | Build grounded answer generation | prompt builder, answer service, fallback handling | answers stay tied to retrieved FAQ context |
| 6 | 07 | Build the business-logic orchestration layer | chat application service, response model | one chat turn works without a UI |
| 7 | 08 | Add the terminal interface | Textual app, input flow, loading states, error display | user can ask a question through the TUI |
| 8 | 09 | Finalize runtime and deployment assets | Dockerfile, compose file, startup instructions | project can be demonstrated in the target local setup |
| 9 | 10 | Add quality gates and delivery docs | tests, smoke checks, README, architecture docs | a third party can run and review the project |

## Detailed Build Order

### Phase 1 - Foundation and Configuration

Deliverables:

- package structure under `app/`
- centralized settings model
- logging configuration
- dependency declaration in `pyproject.toml`
- `.env.example`

Why first:

Everything else depends on stable configuration and a predictable project layout.

### Phase 2 - FAQ Domain and Service Clients

Deliverables:

- FAQ entry model and validation rules
- FAQ repository loader for `data/faq.json`
- Ollama client wrapper for embeddings and generation
- Qdrant client wrapper for collection and search operations

Why next:

This phase creates the stable interfaces that the rest of the runtime will use.

### Phase 3 - Ingestion Pipeline

Deliverables:

- ingestion service that reads validated FAQ entries
- collection initialization strategy for Qdrant
- idempotent upsert behavior
- standalone ingestion script

Why now:

Retrieval depends on having known-good indexed data.

### Phase 4 - Retrieval Engine

Deliverables:

- query embedding path
- semantic search wrapper
- threshold evaluation logic
- structured retrieval result object

Why now:

Retrieval is the functional core of the application and should be proven before prompt generation or UI work.

### Phase 5 - Answer Generation

Deliverables:

- grounded prompt template
- answer service that consumes retrieval results
- fixed fallback behavior when retrieval is weak or generation fails

Why now:

This phase closes the core RAG loop while keeping the UI out of the way.

### Phase 6 - Chat Application Service

Deliverables:

- one orchestration service for a full chat turn
- response DTO or domain object for the UI
- unified error translation for retrieval and generation failures

Why now:

The UI should depend on a single application-level facade, not on several low-level services.

### Phase 7 - Terminal UI

Deliverables:

- Textual application shell
- input field and chat history rendering
- loading, status, and error states
- event wiring into the application service

Why now:

The UI becomes a thin adapter over already tested core logic.

### Phase 8 - Runtime and Deployment

Deliverables:

- Dockerfile for the app
- Docker Compose setup
- service URL configuration strategy
- runtime instructions for local Ollama plus Dockerized app and Qdrant

Why now:

Deployment details are easier to finalize once the runtime shape is stable.

### Phase 9 - Quality Assurance and Delivery

Deliverables:

- unit tests for FAQ parsing, threshold logic, and fallback decisions
- smoke test for one end-to-end chat path
- README with setup and run steps
- architecture summary and project explanation

Why last:

This phase hardens the finished system and makes it reviewable.

## Recommended Internal Milestones

1. Config bootstraps and FAQ data validates.
2. FAQ entries can be ingested into Qdrant.
3. Retrieval returns correct matches for known test questions.
4. Answer generation stays grounded in one FAQ.
5. A CLI or test harness can run one full chat turn.
6. The Textual UI works interactively.
7. Docker-based local demo works.
8. Tests and docs make the project handoff-ready.

## Critical Early Decisions

The source documents leave a few items open. Resolve these early and keep them configurable where possible.

### Embedding Model

Use one dedicated embedding model for both ingestion and query embedding. Do not reuse the generation model for embeddings.

### Generation Model

Keep it configurable. The project should not depend on a single hard-coded local model.

### Threshold and Top-K

Start with conservative defaults such as `top_k = 3` and `score_threshold = 0.70`, then tune with test questions.

### Ollama Deployment Mode

Use an external local Ollama instance as the baseline to reduce Docker complexity. Treat full Ollama containerization as optional.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Weak retrieval quality | wrong or missed answers | use a suitable embedding model, keep FAQ entries clean, tune threshold |
| Hallucinated answers | loss of trust | only answer from retrieved FAQ context and preserve fallback behavior |
| Coupled architecture | hard to test and maintain | keep UI, application, retrieval, and infrastructure separate |
| Docker and Ollama runtime friction | difficult demo setup | keep Ollama external by default and document the connection clearly |
| Hidden config errors | unreliable startup | validate required config at startup and fail early with readable messages |

## Definition of Done for the Planning Baseline

The planning work is complete when:

- the project scope is unambiguous
- modules are explicit and non-overlapping
- the build order is clear
- each phase has outputs and exit criteria
- reviewers can see what gets implemented first and why
