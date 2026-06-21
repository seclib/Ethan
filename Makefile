# =============================================================================
# OpenJarvis — Makefile
# =============================================================================
# Targets:
#   help        : Show this help message
#   install     : Install dependencies (Python + frontend)
#   build       : Build all artifacts
#   dev         : Start development environment
#   prod        : Start production environment
#   test        : Run tests
#   lint        : Run linters
#   format      : Format code
#   clean       : Clean build artifacts
#   docker-build: Build Docker images
#   docker-push : Push Docker images
#   docs        : Build documentation
# =============================================================================

SHELL := /bin/bash
.PHONY: help install build dev prod test lint format clean docker-build docker-push docs

# ─── Configuration ──────────────────────────────────────────────────────────

PYTHON := python3
PIP := uv pip
NPM := npm
CARGO := cargo
DOCKER := docker
DOCKER_COMPOSE := docker compose

# Colors for output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# ─── Help ───────────────────────────────────────────────────────────────────

help: ## Display this help message
	@echo "$(BLUE)OpenJarvis — Makefile$(RESET)"
	@echo "$(BLUE)=================$(RESET)"
	@echo ""
	@echo "$(GREEN)Usage:$(RESET)"
	@echo "  make $(YELLOW)<target>$(RESET)"
	@echo ""
	@echo "$(GREEN)Targets:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}'

# ─── Installation ───────────────────────────────────────────────────────────

install: ## Install all dependencies (Python + frontend + Rust)
	@echo "$(BLUE)Installing Python dependencies...$(RESET)"
	@which uv > /dev/null 2>&1 || pip install uv
	uv sync --all-extras

	@echo "$(BLUE)Installing frontend dependencies...$(RESET)"
	cd frontend && npm install

	@echo "$(BLUE)Building Rust crates...$(RESET)"
	cd rust && cargo build --workspace

	@echo "$(GREEN)✓ Installation complete$(RESET)"

install-python: ## Install Python dependencies only
	@echo "$(BLUE)Installing Python dependencies...$(RESET)"
	@which uv > /dev/null 2>&1 || pip install uv
	uv sync --all-extras
	@echo "$(GREEN)✓ Python dependencies installed$(RESET)"

install-frontend: ## Install frontend dependencies only
	@echo "$(BLUE)Installing frontend dependencies...$(RESET)"
	cd frontend && npm install
	@echo "$(GREEN)✓ Frontend dependencies installed$(RESET)"

install-rust: ## Build Rust crates
	@echo "$(BLUE)Building Rust crates...$(RESET)"
	cd rust && cargo build --workspace
	@echo "$(GREEN)✓ Rust crates built$(RESET)"

# ─── Build ──────────────────────────────────────────────────────────────────

build: build-python build-frontend build-rust ## Build all artifacts

build-python: ## Build Python package
	@echo "$(BLUE)Building Python package...$(RESET)"
	uv build
	@echo "$(GREEN)✓ Python package built$(RESET)"

build-frontend: ## Build frontend
	@echo "$(BLUE)Building frontend...$(RESET)"
	cd frontend && npm run build
	@echo "$(GREEN)✓ Frontend built$(RESET)"

build-rust: ## Build Rust crates (release)
	@echo "$(BLUE)Building Rust crates (release)...$(RESET)"
	cd rust && cargo build --release --workspace
	@echo "$(GREEN)✓ Rust crates built$(RESET)"

# ─── Development ────────────────────────────────────────────────────────────

dev: ## Start development environment with hot reload (root compose)
	@echo "$(BLUE)Starting development environment...$(RESET)"
	@echo "$(YELLOW)  Backend : http://localhost:8000$(RESET)"
	@echo "$(YELLOW)  Frontend: http://localhost:5173$(RESET)"
	@echo ""
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up --build

dev-backend: ## Start backend only (development)
	@echo "$(BLUE)Starting backend (development)...$(RESET)"
	cd src && uv run jarvis serve --host 0.0.0.0 --port 8000 --reload

dev-frontend: ## Start frontend only (development)
	@echo "$(BLUE)Starting frontend (development)...$(RESET)"
	cd frontend && npm run dev

dev-detached: ## Start development environment in background (root compose)
	@echo "$(BLUE)Starting development environment (detached)...$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up --build -d

dev-logs: ## Follow development logs (root compose)
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml logs -f

dev-stop: ## Stop development environment (root compose)
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml down

# ─── Production ─────────────────────────────────────────────────────────────

prod: ## Start production environment (root compose)
	@echo "$(BLUE)Starting production environment...$(RESET)"
	@echo "$(YELLOW)  Frontend: http://localhost:80$(RESET)"
	@echo "$(YELLOW)  Backend : http://localhost:8000$(RESET)"
	$(DOCKER_COMPOSE) -f docker-compose.yml up --build -d

prod-down: ## Stop production environment (root compose)
	$(DOCKER_COMPOSE) -f docker-compose.yml down

prod-logs: ## Follow production logs (root compose)
	$(DOCKER_COMPOSE) -f docker-compose.yml logs -f

prod-restart: ## Restart production environment (root compose)
	$(DOCKER_COMPOSE) -f docker-compose.yml restart

# ─── Testing ────────────────────────────────────────────────────────────────

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(RESET)"
	uv run pytest tests/ -v --tb=short
	@echo "$(GREEN)✓ Tests passed$(RESET)"

test-unit: ## Run unit tests
	@echo "$(BLUE)Running unit tests...$(RESET)"
	uv run pytest tests/ -v --tb=short -m "not integration and not slow"
	@echo "$(GREEN)✓ Unit tests passed$(RESET)"

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(RESET)"
	uv run pytest tests/ -v --tb=short -m "integration"
	@echo "$(GREEN)✓ Integration tests passed$(RESET)"

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	uv run pytest tests/ -v --tb=short --cov=src/openjarvis --cov-report=term --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(RESET)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(RESET)"
	cd frontend && npm test
	@echo "$(GREEN)✓ Frontend tests passed$(RESET)"

# ─── Linting & Formatting ──────────────────────────────────────────────────

lint: lint-python lint-frontend ## Run all linters

lint-python: ## Lint Python code with ruff
	@echo "$(BLUE)Linting Python code...$(RESET)"
	uv run ruff check src/ tests/
	@echo "$(GREEN)✓ Python lint passed$(RESET)"

lint-frontend: ## Lint frontend code
	@echo "$(BLUE)Linting frontend code...$(RESET)"
	cd frontend && npx tsc --noEmit
	@echo "$(GREEN)✓ Frontend lint passed$(RESET)"

format: format-python format-frontend ## Format all code

format-python: ## Format Python code with ruff
	@echo "$(BLUE)Formatting Python code...$(RESET)"
	uv run ruff format src/ tests/
	@echo "$(GREEN)✓ Python code formatted$(RESET)"

format-frontend: ## Format frontend code
	@echo "$(BLUE)Formatting frontend code...$(RESET)"
	cd frontend && npm run format 2>/dev/null || echo "No format script configured"
	@echo "$(GREEN)✓ Frontend code formatted$(RESET)"

# ─── Docker ─────────────────────────────────────────────────────────────────

docker-build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(RESET)"
	$(DOCKER) build -f deploy/docker/Dockerfile.backend -t openjarvis/backend:latest .
	$(DOCKER) build -f deploy/docker/Dockerfile.frontend -t openjarvis/frontend:latest .
	@echo "$(GREEN)✓ Docker images built$(RESET)"

# ─── Legacy Compose (deploy/docker/) ─────────────────────────────

legacy-dev: ## Start development using deploy/docker/ compose
	$(DOCKER_COMPOSE) -f deploy/docker/docker-compose.dev.yml up --build

legacy-prod: ## Start production using deploy/docker/ compose
	$(DOCKER_COMPOSE) -f deploy/docker/docker-compose.yml up --build -d

docker-build-backend: ## Build backend Docker image only
	@echo "$(BLUE)Building backend Docker image...$(RESET)"
	$(DOCKER) build -f deploy/docker/Dockerfile.backend -t openjarvis/backend:latest .
	@echo "$(GREEN)✓ Backend Docker image built$(RESET)"

docker-build-frontend: ## Build frontend Docker image only
	@echo "$(BLUE)Building frontend Docker image...$(RESET)"
	$(DOCKER) build -f deploy/docker/Dockerfile.frontend -t openjarvis/frontend:latest .
	@echo "$(GREEN)✓ Frontend Docker image built$(RESET)"

docker-push: ## Push Docker images to registry
	@echo "$(BLUE)Pushing Docker images...$(RESET)"
	$(DOCKER) push openjarvis/backend:latest
	$(DOCKER) push openjarvis/frontend:latest
	@echo "$(GREEN)✓ Docker images pushed$(RESET)"

docker-clean: ## Remove Docker images
	@echo "$(BLUE)Cleaning Docker images...$(RESET)"
	-$(DOCKER) rmi openjarvis/backend:latest
	-$(DOCKER) rmi openjarvis/frontend:latest
	@echo "$(GREEN)✓ Docker images cleaned$(RESET)"

docker-prune: ## Prune Docker system
	@echo "$(BLUE)Pruning Docker system...$(RESET)"
	$(DOCKER) system prune -f
	@echo "$(GREEN)✓ Docker system pruned$(RESET)"

# ─── Clean ──────────────────────────────────────────────────────────────────

clean: ## Clean all build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(RESET)"
	rm -rf dist/ build/ *.egg-info/
	rm -rf frontend/dist/
	rm -rf rust/target/
	rm -rf site/
	rm -rf htmlcov/
	rm -rf .pytest_cache/ .ruff_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Build artifacts cleaned$(RESET)"

clean-all: clean docker-clean ## Clean everything (including Docker images)

# ─── Documentation ──────────────────────────────────────────────────────────

docs: ## Build documentation with MkDocs
	@echo "$(BLUE)Building documentation...$(RESET)"
	uv run mkdocs build
	@echo "$(GREEN)✓ Documentation built in site/$(RESET)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://localhost:8000$(RESET)"
	uv run mkdocs serve

# ─── Utilities ──────────────────────────────────────────────────────────────

precommit: lint test ## Run lint + tests (pre-commit check)

update-deps: ## Update Python dependencies
	@echo "$(BLUE)Updating Python dependencies...$(RESET)"
	uv sync --all-extras --upgrade
	@echo "$(GREEN)✓ Dependencies updated$(RESET)"

info: ## Display environment information
	@echo "$(BLUE)OpenJarvis — Environment Info$(RESET)"
	@echo "$(BLUE)===========================$(RESET)"
	@echo ""
	@echo "Python:  $(shell which $(PYTHON))"
	@echo "Version: $(shell $(PYTHON) --version 2>&1)"
	@echo "uv:      $(shell which uv 2>/dev/null || echo 'not installed')"
	@echo "Node:    $(shell node --version 2>/dev/null || echo 'not installed')"
	@echo "npm:     $(shell npm --version 2>/dev/null || echo 'not installed')"
	@echo "Rust:    $(shell rustc --version 2>/dev/null || echo 'not installed')"
	@echo "Cargo:   $(shell cargo --version 2>/dev/null || echo 'not installed')"
	@echo "Docker:  $(shell docker --version 2>/dev/null || echo 'not installed')"