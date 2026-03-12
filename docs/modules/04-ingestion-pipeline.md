# Module 04 - Ingestion Pipeline

## Purpose

Load validated FAQ entries, generate embeddings, and store them in Qdrant.

## Scope

- FAQ loading through the repository
- embedding generation for each entry
- collection creation or verification
- idempotent upsert into Qdrant
- standalone ingestion command

## Expected Deliverables

- `app/services/ingestion_service.py`
- `scripts/ingest.py`
- collection initialization strategy

## Dependencies

- Module 02
- Module 03

## Done When

- all FAQ entries can be written to Qdrant consistently
- the script can be re-run without corrupting the collection
- vector dimensions match the configured embedding model
