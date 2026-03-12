# Module 05 - Retrieval Engine

## Purpose

Turn a user question into a ranked FAQ match and a confidence decision.

## Scope

- query embedding
- top-k vector search
- best-hit selection
- threshold evaluation
- structured retrieval result for downstream services

## Expected Deliverables

- `app/services/vector_store_service.py`
- `app/services/retriever.py`
- tests for threshold behavior

## Dependencies

- Module 02
- Module 03

## Done When

- relevant questions return the expected FAQ hit
- irrelevant questions trigger the fallback path
- top-k and threshold are configurable
