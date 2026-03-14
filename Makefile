.PHONY: help build up down logs ingest run test clean rebuild rebuild-clean

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Help target
help:
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(CYAN)  FAQ Chatbot - Quick Start$(NC)"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""
	@echo "$(YELLOW)Terminal 1:$(NC)"
	@echo "  $$ make up              # Start Ollama, Qdrant, App"
	@echo ""
	@echo "$(YELLOW)Terminal 2:$(NC)"
	@echo "  $$ make pull-models     # Download AI models (~3 min)"
	@echo "  $$ make ingest          # Load FAQ data"
	@echo "  $$ make chat            # Start chatting!"
	@echo ""
	@echo "$(GREEN)Docker Commands:$(NC)"
	@echo "  make up              - Start all services (Ollama, Qdrant, App)"
	@echo "  make pull-models     - Pull Ollama models into container"
	@echo "  make down            - Stop all services"
	@echo "  make logs            - View app logs (live)"
	@echo "  make logs-ollama     - View Ollama logs"
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
	@echo "$(CYAN)Starting all services...$(NC)"
	docker compose up --build app

up-bg:
	@echo "$(CYAN)Starting all services in background...$(NC)"
	docker compose up -d

down:
	@echo "$(CYAN)Stopping all services...$(NC)"
	docker compose down

ps:
	@docker compose ps

logs:
	docker compose logs -f app

logs-ollama:
	docker compose logs -f ollama

logs-qdrant:
	docker compose logs -f qdrant

rebuild:
	@echo "$(CYAN)Rebuilding app image...$(NC)"
	docker compose build --no-cache app

# ============================================================================
# Ingestion & Chat
# ============================================================================

pull-models:
	@echo "$(CYAN)Pulling Ollama models into container...$(NC)"
	docker compose exec ollama ollama pull nomic-embed-text-v2-moe
	docker compose exec ollama ollama pull qwen3.5:2b
	@echo "$(GREEN)Models pulled successfully$(NC)"
	@make models

ingest:
	@echo "$(CYAN)Ingesting FAQ data...$(NC)"
	docker compose run --rm --build ingest

chat:
	@echo "$(CYAN)Starting chatbot...$(NC)"
	docker compose run --rm app

chat-bg:
	@echo "$(CYAN)Starting chatbot in background...$(NC)"
	docker compose up -d app

# ============================================================================
# Local Development (no Docker)
# ============================================================================

sync:
	@echo "$(CYAN)Installing dependencies with uv...$(NC)"
	uv sync

test:
	@echo "$(CYAN)Running tests...$(NC)"
	uv run pytest -v

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
	docker rmi $$(docker images -q faqchatbot-claude*) 2>/dev/null || true
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
	@echo "Ollama: $$(curl -s http://localhost:11434/api/tags > /dev/null && echo '✓ OK' || echo '✗ FAIL')"
	@echo "Qdrant: $$(curl -s http://localhost:6333/health > /dev/null && echo '✓ OK' || echo '✗ FAIL')"

models:
	@echo "$(CYAN)Checking Ollama models...$(NC)"
	docker exec faqchatbot-claude-ollama-1 ollama list 2>/dev/null || echo "Ollama not running"

shell-app:
	@echo "$(CYAN)Opening shell in app container...$(NC)"
	docker compose exec app /bin/bash

shell-ollama:
	@echo "$(CYAN)Opening shell in Ollama container...$(NC)"
	docker compose exec ollama /bin/sh

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
