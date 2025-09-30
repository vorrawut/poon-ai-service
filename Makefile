# Poon AI Service Makefile
# Clean Architecture FastAPI microservice for AI-powered spending analysis

.PHONY: help install install-dev clean setup-tesseract check-tesseract test-ocr lint format type-check test test-unit test-integration test-coverage security pre-commit run run-dev run-prod docker-build docker-run docker-clean docs serve-docs bruno-update ollama-setup env-local env-dev env-prod migrate db-reset logs health check-deps upgrade-deps

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip
POETRY := pip  # Fallback to pip since poetry not available
DOCKER := docker
COMPOSE := docker-compose
SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs
BRUNO_DIR := bruno

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[0;37m
RESET := \033[0m

# Environment detection
ENV ?= development
ifeq ($(ENV),production)
    POETRY_OPTS := --only=main --no-dev
else
    POETRY_OPTS :=
endif

help: ## 📋 Show this help message
	@echo "$(CYAN)🦙 Poon AI Service - Clean Architecture FastAPI Microservice$(RESET)"
	@echo "$(YELLOW)Available commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

# Installation and Setup
install: ## 📦 Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(RESET)"
	$(PIP) install -r requirements.txt 2>/dev/null || $(PIP) install fastapi uvicorn pydantic pydantic-settings structlog aiosqlite httpx
	@echo "$(GREEN)✅ Production dependencies installed$(RESET)"

install-dev: ## 🛠️ Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(RESET)"
	$(PIP) install -r requirements-dev.txt 2>/dev/null || $(PIP) install fastapi uvicorn pydantic pydantic-settings structlog aiosqlite httpx ruff mypy pytest pytest-cov pytest-asyncio bandit pre-commit
	@command -v pre-commit >/dev/null 2>&1 && pre-commit install || echo "pre-commit not available"
	@echo "$(GREEN)✅ Development dependencies installed$(RESET)"

clean: ## 🧹 Clean up build artifacts and cache
	@echo "$(BLUE)Cleaning up...$(RESET)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf build/ dist/ htmlcov/ .coverage
	@echo "$(GREEN)✅ Cleanup completed$(RESET)"

# OCR Setup
setup-tesseract: ## 🔍 Setup Tesseract OCR for all environments
	@echo "$(BLUE)Setting up Tesseract OCR...$(RESET)"
	@chmod +x scripts/setup_tesseract.sh
	@./scripts/setup_tesseract.sh
	@echo "$(GREEN)✅ Tesseract OCR setup completed$(RESET)"

check-tesseract: ## ✅ Check Tesseract OCR installation and languages
	@echo "$(BLUE)Checking Tesseract OCR...$(RESET)"
	@if command -v tesseract >/dev/null 2>&1; then \
		echo "$(GREEN)✅ Tesseract found: $$(tesseract --version 2>&1 | head -n1)$(RESET)"; \
		echo "$(CYAN)Available languages:$(RESET)"; \
		tesseract --list-langs 2>/dev/null | tail -n +2 | while read lang; do \
			case $$lang in \
				eng) echo "  $(GREEN)✓ English ($$lang)$(RESET)" ;; \
				tha) echo "  $(GREEN)✓ Thai ($$lang)$(RESET)" ;; \
				*) echo "  - $$lang" ;; \
			esac; \
		done; \
	else \
		echo "$(RED)❌ Tesseract not found. Run 'make setup-tesseract' to install.$(RESET)"; \
		exit 1; \
	fi

test-ocr: ## 🧪 Test OCR functionality with sample images
	@echo "$(BLUE)Testing OCR functionality...$(RESET)"
	@$(PYTHON) -c "import sys; sys.path.insert(0, 'src'); from ai_service.infrastructure.external_apis.ocr_client import TesseractOCRClient; import asyncio; client = TesseractOCRClient(); print('$(GREEN)✅ OCR client available$(RESET)' if client.is_available() else '$(RED)❌ OCR client not available$(RESET)'); print('$(CYAN)Languages:$(RESET)', client.languages if client.is_available() else 'N/A')"

# Code Quality
lint: ## 🔍 Run linting with Ruff
	@echo "$(BLUE)Running Ruff linter...$(RESET)"
	@ruff check $(SRC_DIR) $(TEST_DIR) || echo "$(YELLOW)⚠️ Ruff not available. Install with: pip install ruff$(RESET)"
	@echo "$(GREEN)✅ Linting completed$(RESET)"

lint-fix: ## 🔧 Fix linting issues automatically
	@echo "$(BLUE)Fixing linting issues with Ruff...$(RESET)"
	@ruff check --fix $(SRC_DIR) $(TEST_DIR) 2>/dev/null || echo "$(YELLOW)⚠️ Ruff not available. Install with: pip install ruff$(RESET)"
	@ruff check --unsafe-fixes --fix $(SRC_DIR) $(TEST_DIR) 2>/dev/null || true
	@echo "$(GREEN)✅ Linting fixes applied$(RESET)"

format: ## 🎨 Format code with Ruff and Prettier
	@echo "$(BLUE)Formatting code with Ruff...$(RESET)"
	@ruff format $(SRC_DIR) $(TEST_DIR) || echo "$(YELLOW)⚠️ Ruff not available. Install with: pip install ruff$(RESET)"
	@ruff check --fix $(SRC_DIR) $(TEST_DIR) 2>/dev/null || true
	@echo "$(BLUE)Formatting YAML/JSON files with Prettier...$(RESET)"
	@prettier --write "**/*.{yaml,yml,json,md}" --ignore-path .gitignore 2>/dev/null || echo "$(YELLOW)⚠️ Prettier not available. Install with: npm install -g prettier$(RESET)"
	@echo "$(GREEN)✅ Code formatting completed$(RESET)"

type-check: ## 🔎 Run type checking with MyPy
	@echo "$(BLUE)Running MyPy type checking...$(RESET)"
	@mypy $(SRC_DIR) || echo "$(YELLOW)⚠️ MyPy not available. Install with: pip install mypy$(RESET)"
	@echo "$(GREEN)✅ Type checking completed$(RESET)"

security: ## 🔒 Run security checks with Bandit
	@echo "$(BLUE)Running security checks...$(RESET)"
	@bandit -r $(SRC_DIR) -f json -o security-report.json 2>/dev/null || true
	@bandit -r $(SRC_DIR) || echo "$(YELLOW)⚠️ Bandit not available. Install with: pip install bandit$(RESET)"
	@echo "$(GREEN)✅ Security checks completed$(RESET)"

pre-commit: ## ⚡ Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(RESET)"
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit run --all-files; \
		if [ $$? -ne 0 ]; then \
			echo "$(YELLOW)⚠️ Pre-commit found issues and fixed them. Re-running...$(RESET)"; \
			pre-commit run --all-files; \
		fi; \
	else \
		echo "$(YELLOW)⚠️ Pre-commit not available. Install with: pip install pre-commit$(RESET)"; \
	fi
	@echo "$(GREEN)✅ Pre-commit checks completed$(RESET)"

pre-commit-install: ## 🔧 Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(RESET)"
	@pre-commit install || echo "$(YELLOW)⚠️ Pre-commit not available. Install with: pip install pre-commit$(RESET)"
	@echo "$(GREEN)✅ Pre-commit hooks installed$(RESET)"

# Testing
test: ## 🧪 Run all tests
	@echo "$(BLUE)Running all tests...$(RESET)"
	@pytest || echo "$(YELLOW)⚠️ Pytest not available. Install with: pip install pytest$(RESET)"
	@echo "$(GREEN)✅ All tests completed$(RESET)"

test-unit: ## 🔬 Run unit tests only
	@echo "$(BLUE)Running unit tests...$(RESET)"
	@pytest -m "unit" -v || echo "$(YELLOW)⚠️ Pytest not available. Install with: pip install pytest$(RESET)"
	@echo "$(GREEN)✅ Unit tests completed$(RESET)"

test-integration: ## 🔗 Run integration tests only
	@echo "$(BLUE)Running integration tests...$(RESET)"
	@pytest -m "integration" -v || echo "$(YELLOW)⚠️ Pytest not available. Install with: pip install pytest$(RESET)"
	@echo "$(GREEN)✅ Integration tests completed$(RESET)"

test-coverage: ## 📊 Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	@pytest --cov=ai_service --cov-report=html --cov-report=term-missing || echo "$(YELLOW)⚠️ Pytest-cov not available. Install with: pip install pytest-cov$(RESET)"
	@echo "$(GREEN)✅ Coverage report generated in htmlcov/$(RESET)"

# Application
run: ## 🚀 Run the application (production mode)
	@echo "$(BLUE)Starting Poon AI Service (production)...$(RESET)"
	@python -m src.main

run-dev: ## 🔧 Run the application in development mode
	@echo "$(BLUE)Starting Poon AI Service (development)...$(RESET)"
	@ENV=development DEBUG=true uvicorn src.main:app --reload --host 0.0.0.0 --port 8001

run-prod: ## 🏭 Run the application in production mode
	@echo "$(BLUE)Starting Poon AI Service (production)...$(RESET)"
	@ENV=production uvicorn src.main:app --host 0.0.0.0 --port 8001 --workers 4

# Docker
docker-build: ## 🐳 Build Docker image
	@echo "$(BLUE)Building Docker image...$(RESET)"
	$(DOCKER) build -t poon-ai-service:latest .
	@echo "$(GREEN)✅ Docker image built$(RESET)"

docker-run: ## 🐳 Run Docker container
	@echo "$(BLUE)Running Docker container...$(RESET)"
	$(DOCKER) run -p 8001:8001 --env-file .env poon-ai-service:latest

docker-clean: ## 🐳 Clean Docker images and containers
	@echo "$(BLUE)Cleaning Docker resources...$(RESET)"
	$(DOCKER) system prune -f
	$(DOCKER) image prune -f
	@echo "$(GREEN)✅ Docker cleanup completed$(RESET)"

# Documentation
docs: ## 📚 Generate documentation
	@echo "$(BLUE)Generating documentation...$(RESET)"
	@mkdir -p docs
	@python -c "import json; from src.main import app; spec = app.openapi(); json.dump(spec, open('docs/openapi.json', 'w'), indent=2); print('OpenAPI spec generated')"
	@echo "$(GREEN)✅ Documentation generated$(RESET)"

serve-docs: ## 📖 Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(RESET)"
	@python -m http.server 8080 -d docs
	@echo "$(CYAN)📖 Documentation available at http://localhost:8080$(RESET)"

# Bruno API Testing
bruno-update: ## 📡 Update Bruno API tests
	@echo "$(BLUE)Updating Bruno API tests...$(RESET)"
	@if [ -d "$(BRUNO_DIR)" ]; then \
		echo "$(YELLOW)Updating existing Bruno tests...$(RESET)"; \
		cp bruno/environments/development.bru.example bruno/environments/development.bru 2>/dev/null || true; \
		cp bruno/environments/production.bru.example bruno/environments/production.bru 2>/dev/null || true; \
	else \
		echo "$(YELLOW)Creating Bruno test structure...$(RESET)"; \
		mkdir -p bruno/environments; \
		mkdir -p bruno/Health; \
		mkdir -p bruno/Spending; \
		mkdir -p bruno/AI; \
	fi
	@echo "$(GREEN)✅ Bruno tests updated$(RESET)"

# Ollama Setup
ollama-setup: ## 🦙 Setup Ollama and Llama model
	@echo "$(BLUE)Setting up Ollama and Llama model...$(RESET)"
	@if command -v ollama >/dev/null 2>&1; then \
		echo "$(GREEN)✅ Ollama is already installed$(RESET)"; \
	else \
		echo "$(YELLOW)Installing Ollama...$(RESET)"; \
		curl -fsSL https://ollama.ai/install.sh | sh; \
	fi
	@echo "$(BLUE)Pulling Llama 3.2 3B model...$(RESET)"
	ollama pull llama3.2:3b
	@echo "$(GREEN)✅ Ollama setup completed$(RESET)"

# Environment Setup
env-local: ## 🏠 Setup local development environment
	@echo "$(BLUE)Setting up local environment...$(RESET)"
	@if [ ! -f ".env" ]; then \
		cp .env.example .env; \
		echo "$(YELLOW)Created .env file from template$(RESET)"; \
	fi
	@echo "ENVIRONMENT=development" >> .env.local
	@echo "DEBUG=true" >> .env.local
	@echo "LOG_LEVEL=DEBUG" >> .env.local
	@echo "OLLAMA_URL=http://localhost:11434" >> .env.local
	@echo "$(GREEN)✅ Local environment configured$(RESET)"

env-dev: ## 🔧 Setup development environment
	@echo "$(BLUE)Setting up development environment...$(RESET)"
	@echo "ENVIRONMENT=development" > .env.dev
	@echo "DEBUG=true" >> .env.dev
	@echo "LOG_LEVEL=INFO" >> .env.dev
	@echo "DATABASE_URL=sqlite:///./spending_dev.db" >> .env.dev
	@echo "$(GREEN)✅ Development environment configured$(RESET)"

env-prod: ## 🏭 Setup production environment template
	@echo "$(BLUE)Setting up production environment template...$(RESET)"
	@echo "ENVIRONMENT=production" > .env.prod.example
	@echo "DEBUG=false" >> .env.prod.example
	@echo "LOG_LEVEL=WARNING" >> .env.prod.example
	@echo "DATABASE_URL=postgresql://user:pass@localhost/poon_ai" >> .env.prod.example
	@echo "API_KEY=your-secure-api-key-here" >> .env.prod.example
	@echo "$(YELLOW)⚠️  Production environment template created as .env.prod.example$(RESET)"
	@echo "$(YELLOW)⚠️  Copy to .env.prod and update with real values$(RESET)"

# Database
migrate: ## 🗄️ Run database migrations
	@echo "$(BLUE)Running database migrations...$(RESET)"
	@python scripts/migrate.py
	@echo "$(GREEN)✅ Database migrations completed$(RESET)"

db-reset: ## 🗄️ Reset database (WARNING: Deletes all data)
	@echo "$(RED)⚠️  WARNING: This will delete all data!$(RESET)"
	@read -p "Are you sure? (y/N) " confirm && [ "$$confirm" = "y" ] || exit 1
	rm -f spending.db spending_dev.db spending_test.db
	$(MAKE) migrate
	@echo "$(GREEN)✅ Database reset completed$(RESET)"

# Monitoring and Health
logs: ## 📋 Show application logs
	@echo "$(BLUE)Showing application logs...$(RESET)"
	tail -f ai-service.log 2>/dev/null || echo "$(YELLOW)No log file found. Run the application first.$(RESET)"

health: ## ❤️ Check service health
	@echo "$(BLUE)Checking service health...$(RESET)"
	@curl -s http://localhost:8001/health | jq '.' || echo "$(RED)❌ Service not responding$(RESET)"

# Dependencies
check-deps: ## 🔍 Check for dependency vulnerabilities
	@echo "$(BLUE)Checking dependencies for vulnerabilities...$(RESET)"
	@safety check || echo "$(YELLOW)⚠️ Safety not available. Install with: pip install safety$(RESET)"
	@echo "$(GREEN)✅ Dependency check completed$(RESET)"

upgrade-deps: ## ⬆️ Upgrade dependencies
	@echo "$(BLUE)Upgrading dependencies...$(RESET)"
	@pip list --outdated || echo "$(YELLOW)⚠️ Use pip install --upgrade <package> to upgrade individual packages$(RESET)"
	@echo "$(GREEN)✅ Dependencies upgrade check completed$(RESET)"

# Complete Quality Check
quality: lint-fix format type-check security pre-commit test-coverage ## 🏆 Run complete quality check pipeline (auto-fixes linting issues, includes prettier)
	@echo "$(GREEN)🎉 All quality checks passed!$(RESET)"

# Development Setup
setup-dev: install-dev pre-commit-install env-local ollama-setup bruno-update migrate ## 🚀 Complete development setup
	@echo "$(GREEN)🎉 Development environment setup completed!$(RESET)"
	@echo "$(CYAN)Next steps:$(RESET)"
	@echo "  1. $(YELLOW)make run-dev$(RESET) - Start development server"
	@echo "  2. $(YELLOW)make test$(RESET) - Run tests"
	@echo "  3. $(YELLOW)make health$(RESET) - Check service health"

# Production Deployment
deploy-check: quality security check-deps ## 🚀 Pre-deployment checks
	@echo "$(GREEN)✅ Deployment checks passed$(RESET)"

# Continuous Integration
ci: install lint type-check security test-coverage ## 🔄 CI pipeline
	@echo "$(GREEN)✅ CI pipeline completed$(RESET)"

# Show current status
status: ## 📊 Show project status
	@echo "$(CYAN)📊 Poon AI Service Status$(RESET)"
	@echo "$(BLUE)Environment:$(RESET) $(ENV)"
	@echo "$(BLUE)Python:$(RESET) $(shell $(PYTHON) --version 2>/dev/null || echo 'Not found')"
	@echo "$(BLUE)Pip:$(RESET) $(shell $(PIP) --version 2>/dev/null || echo 'Not found')"
	@echo "$(BLUE)Docker:$(RESET) $(shell $(DOCKER) --version 2>/dev/null || echo 'Not found')"
	@echo "$(BLUE)Ollama:$(RESET) $(shell ollama --version 2>/dev/null || echo 'Not installed')"
	@echo "$(BLUE)Service Health:$(RESET)"
	@curl -s http://localhost:8001/health >/dev/null 2>&1 && echo "  $(GREEN)✅ Service is running$(RESET)" || echo "  $(RED)❌ Service is not running$(RESET)"
