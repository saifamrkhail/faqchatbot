# Module 07 - Chat Application Service

## Purpose

Orchestrate one complete chat turn without depending on any specific UI.

## Scope

- receive a user question
- call retrieval
- decide fallback or answer generation
- return a structured response object to the caller
- centralize application-level error translation

## Expected Deliverables

- `app/services/chat_application.py`
- request and response models for the UI layer

## Dependencies

- Module 05
- Module 06

## Done When

- a single service can process one question end to end
- the UI needs only this service, not lower-level clients
- orchestration logic is testable without Textual
