# Docker Management for Poon AI Service
.PHONY: help build up down restart logs clean test health status

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

help: ## 📖 Show this help message
	@echo "$(BLUE)Poon AI Service - Docker Management$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## 🔨 Build all services
	@echo "$(BLUE)Building services...$(NC)"
	cd .. && docker-compose build --no-cache

up: ## 🚀 Start all services
	@echo "$(BLUE)Starting services...$(NC)"
	cd .. && docker-compose up -d
	@echo "$(GREEN)Services started! Use 'make status' to check health.$(NC)"

up-with-monitoring: ## 📊 Start all services including monitoring
	@echo "$(BLUE)Starting services with monitoring...$(NC)"
	cd .. && docker-compose --profile monitoring up -d
	@echo "$(GREEN)Services with monitoring started!$(NC)"

down: ## 🛑 Stop all services
	@echo "$(BLUE)Stopping services...$(NC)"
	cd .. && docker-compose down
	@echo "$(GREEN)Services stopped.$(NC)"

restart: ## 🔄 Restart all services
	@echo "$(BLUE)Restarting services...$(NC)"
	cd .. && docker-compose restart
	@echo "$(GREEN)Services restarted.$(NC)"

status: ## 📊 Show service status
	@echo "$(BLUE)Service Status:$(NC)"
	@cd .. && docker-compose ps
	@echo ""
	@echo "$(BLUE)Health Checks:$(NC)"
	@echo -n "AI Service: "
	@if curl -s http://localhost:8001/health | grep -q "healthy"; then \
		echo "$(GREEN)✅ Healthy$(NC)"; \
	else \
		echo "$(RED)❌ Unhealthy$(NC)"; \
	fi
	@echo -n "Ollama: "
	@if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then \
		echo "$(GREEN)✅ Healthy$(NC)"; \
	else \
		echo "$(RED)❌ Unhealthy$(NC)"; \
	fi
	@echo -n "Redis: "
	@if cd .. && docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then \
		echo "$(GREEN)✅ Healthy$(NC)"; \
	else \
		echo "$(RED)❌ Unhealthy$(NC)"; \
	fi

health: ## 🏥 Run comprehensive health check
	@echo "$(BLUE)Running health checks...$(NC)"
	@echo ""
	@echo "$(BLUE)1. Basic Health Check:$(NC)"
	curl -s http://localhost:8001/health | jq .
	@echo ""
	@echo "$(BLUE)2. Detailed Health Check:$(NC)"
	curl -s http://localhost:8001/api/v1/health/detailed | jq .
	@echo ""
	@echo "$(BLUE)3. AI Processing Test:$(NC)"
	curl -s -X POST http://localhost:8001/api/v1/spending/process/text \
		-H "Content-Type: application/json" \
		-d '{"text": "Coffee at Starbucks 120 baht", "language": "en"}' | jq .

test: ## 🧪 Run basic API tests
	@echo "$(BLUE)Running API tests...$(NC)"
	@echo ""
	@echo "$(BLUE)Testing Health Endpoint:$(NC)"
	@if curl -s http://localhost:8001/health | grep -q "healthy"; then \
		echo "$(GREEN)✅ Health check passed$(NC)"; \
	else \
		echo "$(RED)❌ Health check failed$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)Testing Spending Entries:$(NC)"
	@if curl -s http://localhost:8001/api/v1/spending/ | grep -q "entries"; then \
		echo "$(GREEN)✅ Spending entries endpoint working$(NC)"; \
	else \
		echo "$(RED)❌ Spending entries endpoint failed$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)Testing Text Processing:$(NC)"
	@if curl -s -X POST http://localhost:8001/api/v1/spending/process/text \
		-H "Content-Type: application/json" \
		-d '{"text": "Lunch 250 baht", "language": "en"}' | grep -q "success"; then \
		echo "$(GREEN)✅ Text processing working$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ Text processing may be initializing$(NC)"; \
	fi

clean: ## 🧹 Clean up containers and volumes
	@echo "$(YELLOW)Warning: This will remove all containers and volumes!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	cd .. && docker-compose down -v
	docker system prune -f
	@echo "$(GREEN)Cleanup complete.$(NC)"

init-model: ## 🤖 Initialize Ollama model
	@echo "$(BLUE)Initializing Llama model...$(NC)"
	cd .. && docker-compose exec ollama ollama pull llama3.2:3b
	@echo "$(GREEN)Model initialized!$(NC)"

shell-ai: ## 🐚 Open shell in AI service container
	cd .. && docker-compose exec ai-service bash

shell-ollama: ## 🐚 Open shell in Ollama container
	cd .. && docker-compose exec ollama bash

urls: ## 🔗 Show all service URLs
	@echo "$(BLUE)Service URLs:$(NC)"
	@echo "  • AI Service:    http://localhost:8001"
	@echo "  • API Docs:      http://localhost:8001/docs"
	@echo "  • Health Check:  http://localhost:8001/health"
	@echo "  • Metrics:       http://localhost:8001/metrics"
	@echo "  • Ollama:        http://localhost:11434"
	@echo "  • Redis:         localhost:6379"
	@echo ""
	@echo "$(BLUE)Monitoring (if enabled):$(NC)"
	@echo "  • Prometheus:    http://localhost:9090"
	@echo "  • Grafana:       http://localhost:3000 (admin/admin)"

dev: ## 🛠️ Start development environment
	@echo "$(BLUE)Starting development environment...$(NC)"
	./start.sh

# Default target
.DEFAULT_GOAL := help
