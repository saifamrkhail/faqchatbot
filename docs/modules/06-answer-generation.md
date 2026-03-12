# Module 06 - Answer Generation

## Purpose

Generate a short answer that stays grounded in the selected FAQ context.

## Scope

- prompt construction from user question plus FAQ context
- answer generation through Ollama
- fallback handling for weak retrieval or generation failure
- answer style control

## Expected Deliverables

- `app/services/answer_service.py`
- prompt template or prompt builder
- tests for fallback behavior

## Dependencies

- Module 03
- Module 05

## Done When

- answers use only the selected FAQ context
- the service does not answer when retrieval confidence is too low
- failure cases return controlled messages instead of leaking internals
