# Module 03 - External Service Clients

## Purpose

Wrap Ollama and Qdrant behind small, predictable interfaces.

## Scope

- Ollama embedding requests
- Ollama generation requests
- Qdrant collection management
- Qdrant upsert and search operations
- connection and timeout handling

## Expected Deliverables

- `app/infrastructure/ollama_client.py`
- `app/infrastructure/qdrant_client.py`
- configuration bindings for URLs, models, and collection name

## Dependencies

- Module 01

## Done When

- clients can be created from centralized config
- failures are translated into controlled exceptions or error results
- higher-level services do not need to know transport details
