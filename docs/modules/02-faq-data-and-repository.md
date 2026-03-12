# Module 02 - FAQ Data and Repository

## Purpose

Define the FAQ domain model and provide a reliable way to load FAQ entries from disk.

## Scope

- FAQ schema and validation rules
- FAQ source file structure
- repository for loading and returning FAQ entries
- mapping from raw JSON into internal domain objects

## Expected Deliverables

- `data/faq.json`
- `app/domain/faq.py`
- `app/repositories/faq_repository.py`
- validation tests for required fields

## Dependencies

- Module 01

## Done When

- invalid FAQ records are rejected clearly
- valid FAQ records load into consistent domain objects
- the rest of the system can consume FAQ entries without parsing raw JSON directly
