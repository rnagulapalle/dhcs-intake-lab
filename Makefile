# =============================================================================
# BHT Multi-Agent Platform - Makefile
# =============================================================================

.PHONY: help build up down logs smoke-test test clean

# Default target
help:
	@echo "BHT Multi-Agent Platform"
	@echo ""
	@echo "Usage:"
	@echo "  make build        - Build all Docker images"
	@echo "  make up           - Start API service only"
	@echo "  make up-infra     - Start API + infrastructure (Kafka, Pinot)"
	@echo "  make up-full      - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - Follow API logs"
	@echo "  make smoke-test   - Run audit correlation smoke test"
	@echo "  make test         - Run unit tests"
	@echo "  make clean        - Remove containers, volumes, and images"
	@echo ""
	@echo "Environment:"
	@echo "  OPENAI_API_KEY    - Required for API and smoke tests"

# Build
build:
	docker compose build

# Start services
up:
	docker compose up -d agent-api

up-infra:
	docker compose --profile infra up -d

up-full:
	docker compose --profile full up -d

# Stop services
down:
	docker compose --profile full down --remove-orphans

# Logs
logs:
	docker compose logs -f agent-api

# Smoke test
smoke-test:
	@./scripts/run_smoke_test.sh

# Unit tests (local)
test:
	@echo "Running unit tests..."
	python -m pytest tests/platform/ -v

# Clean
clean:
	docker compose --profile full down --remove-orphans -v
	docker image rm bht-agent-api:latest bht-dashboard:latest bht-generator:latest 2>/dev/null || true
	rm -rf __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
