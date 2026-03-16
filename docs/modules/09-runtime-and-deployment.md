# Module 09 - Runtime and Deployment

## Purpose

Define how the application runs in local development and in the Docker delivery setup
where Ollama stays on the host machine.

## Scope

- app Dockerfile
- Docker Compose wiring
- host Ollama prerequisite and model bootstrap
- environment variable strategy
- runtime service dependencies
- startup and operational notes

## Expected Deliverables

- `Dockerfile`
- `docker-compose.yml`
- `scripts/pull_host_ollama_models.sh`
- documented local runtime instructions

## Dependencies

- Module 01
- Module 03
- Module 04
- Module 07

## Done When

- the target local setup is reproducible
- service URLs are configurable and documented
- app and Qdrant can be demonstrated in the expected environment
- required Ollama host models are documented or pulled outside Docker
