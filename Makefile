.PHONY: help install install-dev install-gui install-all clean test lint format type-check pre-commit run-bot run-gui run-daemon docker-build docker-up docker-down migrate

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)AlphaSnobAI - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================================================
# Installation
# ============================================================================

install: ## Install core dependencies only
	@echo "$(BLUE)Installing core dependencies with uv...$(NC)"
	uv pip install -e .

install-dev: ## Install with dev dependencies
	@echo "$(BLUE)Installing with dev dependencies...$(NC)"
	uv pip install -e ".[dev]"

install-gui: ## Install with GUI dependencies
	@echo "$(BLUE)Installing with GUI dependencies...$(NC)"
	uv pip install -e ".[gui]"

install-all: ## Install all dependencies (core + gui + dev)
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	uv pip install -e ".[all]"
	pre-commit install

# ============================================================================
# Development
# ============================================================================

clean: ## Clean build artifacts and cache
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

format: ## Format code with ruff and black
	@echo "$(BLUE)Formatting code...$(NC)"
	ruff check --fix src/ tests/
	black src/ tests/
	@echo "$(GREEN)Formatting complete!$(NC)"

lint: ## Lint code with ruff
	@echo "$(BLUE)Linting code...$(NC)"
	ruff check src/ tests/
	@echo "$(GREEN)Linting complete!$(NC)"

type-check: ## Type check with mypy
	@echo "$(BLUE)Type checking...$(NC)"
	mypy src/
	@echo "$(GREEN)Type checking complete!$(NC)"

test: ## Run tests with coverage
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v
	@echo "$(GREEN)Tests complete!$(NC)"

test-unit: ## Run only unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest tests/unit/ -v -m unit

test-integration: ## Run only integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest tests/integration/ -v -m integration

test-e2e: ## Run only e2e tests
	@echo "$(BLUE)Running e2e tests...$(NC)"
	pytest tests/e2e/ -v -m e2e

test-coverage: ## Run tests and open coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest tests/ --cov-report=html
	open htmlcov/index.html || xdg-open htmlcov/index.html

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files

check-all: lint type-check test ## Run all checks (lint, type-check, test)
	@echo "$(GREEN)All checks passed!$(NC)"

# ============================================================================
# Running
# ============================================================================

run-bot: ## Run bot in foreground (interactive mode)
	@echo "$(BLUE)Starting AlphaSnob bot...$(NC)"
	alphasnob start --interactive

run-gui: ## Run desktop GUI application
	@echo "$(BLUE)Starting AlphaSnob GUI...$(NC)"
	alphasnob-gui

run-daemon: ## Run bot as daemon (background)
	@echo "$(BLUE)Starting AlphaSnob daemon...$(NC)"
	alphasnob daemon start

stop-daemon: ## Stop daemon
	@echo "$(YELLOW)Stopping AlphaSnob daemon...$(NC)"
	alphasnob daemon stop

status: ## Check daemon status
	@echo "$(BLUE)Checking daemon status...$(NC)"
	alphasnob daemon status

logs: ## View daemon logs
	@echo "$(BLUE)Viewing daemon logs...$(NC)"
	alphasnob logs --follow

# ============================================================================
# Database
# ============================================================================

migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create message="description")
	@echo "$(BLUE)Creating new migration...$(NC)"
	alembic revision --autogenerate -m "$(message)"

migrate-downgrade: ## Downgrade database by one revision
	@echo "$(YELLOW)Downgrading database...$(NC)"
	alembic downgrade -1

db-backup: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	alphasnob db backup

db-restore: ## Restore database from backup
	@echo "$(YELLOW)Restoring database...$(NC)"
	alphasnob db restore

# ============================================================================
# Docker
# ============================================================================

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t alphasnob:latest .

docker-up: ## Start Docker containers
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker-compose up -d

docker-down: ## Stop Docker containers
	@echo "$(YELLOW)Stopping Docker containers...$(NC)"
	docker-compose down

docker-logs: ## View Docker logs
	@echo "$(BLUE)Viewing Docker logs...$(NC)"
	docker-compose logs -f

docker-shell: ## Open shell in Docker container
	@echo "$(BLUE)Opening shell in container...$(NC)"
	docker-compose exec bot bash

# ============================================================================
# Development Tools
# ============================================================================

setup-dev: install-all pre-commit migrate ## Complete dev environment setup
	@echo "$(GREEN)Development environment setup complete!$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  1. Copy config/config.yaml.example to config/config.yaml"
	@echo "  2. Copy config/secrets.yaml.example to config/secrets.yaml"
	@echo "  3. Run 'make run-bot' to start the bot"

shell: ## Open Python shell with project context
	@echo "$(BLUE)Opening Python shell...$(NC)"
	python -i -c "import sys; sys.path.insert(0, 'src'); from alphasnob import *"

deps-update: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	uv pip compile pyproject.toml --upgrade

deps-tree: ## Show dependency tree
	@echo "$(BLUE)Dependency tree:$(NC)"
	uv pip tree
