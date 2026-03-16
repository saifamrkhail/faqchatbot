.PHONY: help build up up-all up-bg down ps logs logs-qdrant rebuild \
	pull-models ingest chat chat-bg sync test eval eval-category \
	grid-search grid-search-full test-watch test-coverage run-local \
	ingest-local clean clean-hard clean-py health models shell-app docs

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color
HOST_OLLAMA_URL ?= http://localhost:11434
COMPOSE_APP_ENV := FAQ_CHATBOT_OLLAMA_BASE_URL=$(HOST_OLLAMA_URL)

# Help target
help:
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(CYAN)  FAQ Chatbot - Quick Start$(NC)"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""
	@echo "$(YELLOW)Terminal 1:$(NC)"
	@echo "  $$ make pull-models     # Pull required models on host Ollama"
	@echo "  $$ make up              # Start Qdrant in Docker"
	@echo ""
	@echo "$(YELLOW)Terminal 2:$(NC)"
	@echo "  $$ make ingest          # Load FAQ data"
	@echo "  $$ make chat            # Start chatting!"
	@echo ""
	@echo "$(GREEN)Docker Commands:$(NC)"
	@echo "  make up              - Start Qdrant in background"
	@echo "  make up-all          - Start Qdrant + app logs (host Ollama required)"
	@echo "  make pull-models     - Pull required models on host Ollama"
	@echo "  make down            - Stop all services"
	@echo "  make logs            - View app logs (live)"
	@echo "  make logs-qdrant     - View Qdrant logs"
	@echo "  make ps              - Show container status"
	@echo "  make rebuild         - Rebuild app image"
	@echo ""
	@echo "$(GREEN)Ingestion & Chatbot:$(NC)"
	@echo "  make ingest          - Load FAQ data into Qdrant"
	@echo "  make chat            - Run chatbot (interactive terminal)"
	@echo "  make chat-bg         - Run chatbot in background"
	@echo ""
	@echo "$(GREEN)Development (Local):$(NC)"
	@echo "  make sync            - Install dependencies (uv sync)"
	@echo "  make test            - Run all tests"
	@echo "  make test-watch      - Run tests in watch mode"
	@echo "  make run-local       - Run chatbot locally (no Docker)"
	@echo "  make ingest-local    - Ingest FAQ locally (no Docker)"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean           - Stop services and remove volumes"
	@echo "  make clean-hard      - Deep clean (removes images too)"
	@echo ""

# ============================================================================
# Docker Commands
# ============================================================================

build:
	@echo "$(CYAN)Building app image...$(NC)"
	docker compose build

up:
	@echo "$(CYAN)Starting Qdrant in Docker...$(NC)"
	@echo "$(YELLOW)Host Ollama must already be running at $(HOST_OLLAMA_URL)$(NC)"
	docker compose up -d qdrant

up-all:
	@echo "$(CYAN)Starting Qdrant and app logs...$(NC)"
	@echo "$(YELLOW)Host Ollama must already be running at $(HOST_OLLAMA_URL)$(NC)"
	$(COMPOSE_APP_ENV) docker compose up --build qdrant app

up-bg:
	@echo "$(CYAN)Starting Qdrant and app in background...$(NC)"
	@echo "$(YELLOW)Host Ollama must already be running at $(HOST_OLLAMA_URL)$(NC)"
	$(COMPOSE_APP_ENV) docker compose up -d --build qdrant app

down:
	@echo "$(CYAN)Stopping all services...$(NC)"
	docker compose down

ps:
	@docker compose ps

logs:
	docker compose logs -f app

logs-qdrant:
	docker compose logs -f qdrant

rebuild:
	@echo "$(CYAN)Rebuilding app image...$(NC)"
	docker compose build --no-cache app

# ============================================================================
# Ingestion & Chat
# ============================================================================

pull-models:
	@echo "$(CYAN)Pulling required models on host Ollama at $(HOST_OLLAMA_URL)...$(NC)"
	OLLAMA_HOST=$(HOST_OLLAMA_URL) ./scripts/pull_host_ollama_models.sh
	@echo "$(GREEN)Host Ollama models ready$(NC)"
	@make models

ingest:
	@echo "$(CYAN)Ingesting FAQ data...$(NC)"
	$(COMPOSE_APP_ENV) docker compose run --rm --build ingest

chat:
	@echo "$(CYAN)Starting chatbot...$(NC)"
	$(COMPOSE_APP_ENV) docker compose run --rm --build app

chat-bg:
	@echo "$(CYAN)Starting chatbot in background...$(NC)"
	$(COMPOSE_APP_ENV) docker compose up -d --build app

# ============================================================================
# Local Development (no Docker)
# ============================================================================

sync:
	@echo "$(CYAN)Installing dependencies with uv...$(NC)"
	uv sync

test:
	@echo "$(CYAN)Running tests...$(NC)"
	uv run pytest -v

eval:
	@echo "$(CYAN)Running chatbot evaluation against live services...$(NC)"
	uv run python -m tests.evaluation.runner -v

eval-category:
	@echo "$(CYAN)Running evaluation for category: $(CAT)$(NC)"
	uv run python -m tests.evaluation.runner -v --category $(CAT)

grid-search:
	@echo "$(CYAN)Running parameter grid search (quick)...$(NC)"
	uv run python -m tests.evaluation.grid_search --quick

grid-search-full:
	@echo "$(CYAN)Running full parameter grid search...$(NC)"
	uv run python -m tests.evaluation.grid_search

test-watch:
	@echo "$(CYAN)Running tests in watch mode...$(NC)"
	uv run pytest-watch

test-coverage:
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	uv run pytest --cov=app --cov-report=html
	@echo "$(GREEN)Coverage report: htmlcov/index.html$(NC)"

run-local:
	@echo "$(CYAN)Running chatbot locally...$(NC)"
	uv run faqchatbot --tui

ingest-local:
	@echo "$(CYAN)Ingesting FAQ data locally...$(NC)"
	uv run python -m scripts.ingest

# ============================================================================
# Cleanup
# ============================================================================

clean:
	@echo "$(YELLOW)Stopping services and removing volumes...$(NC)"
	docker compose down -v
	@echo "$(GREEN)Clean complete$(NC)"

clean-hard: clean
	@echo "$(YELLOW)Removing all images...$(NC)"
	docker compose rm -f
	docker rmi $$(docker images -q faqchatbot*) 2>/dev/null || true
	@echo "$(GREEN)Hard clean complete$(NC)"

clean-py:
	@echo "$(YELLOW)Cleaning Python cache...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
	@echo "$(GREEN)Python cache cleaned$(NC)"

# ============================================================================
# Utilities
# ============================================================================

health:
	@echo "$(CYAN)Checking service health...$(NC)"
	@echo "Host Ollama: $$(curl -s $(HOST_OLLAMA_URL)/api/tags > /dev/null && echo '✓ OK' || echo '✗ FAIL')"
	@echo "Qdrant: $$(curl -s http://localhost:6333/health > /dev/null && echo '✓ OK' || echo '✗ FAIL')"

models:
	@echo "$(CYAN)Checking host Ollama models...$(NC)"
	@OLLAMA_HOST=$(HOST_OLLAMA_URL) ollama list 2>/dev/null || echo "Host Ollama not running or not installed"

shell-app:
	@echo "$(CYAN)Opening shell in app container...$(NC)"
	docker compose exec app /bin/bash

# ============================================================================
# Documentation
# ============================================================================

docs:
	@echo "$(CYAN)Key documentation files:$(NC)"
	@echo ""
	@echo "Project Definition:"
	@echo "  cat docs/PROJECT-DEFINITION.md"
	@echo ""
	@echo "Implementation Plan:"
	@echo "  cat docs/IMPLEMENTATION-PLAN.md"
	@echo ""
	@echo "Runtime & Deployment:"
	@echo "  cat docs/RUNTIME-DEPLOYMENT.md"
	@echo ""
