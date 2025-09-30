#!/bin/bash

# Poon AI Service Docker Startup Script
set -e

echo "🚀 Starting Poon AI Service with Docker Compose..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data logs

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    if [ -f docker/env.docker ]; then
        cp docker/env.docker .env
        print_success "Environment file created from docker/env.docker"
    else
        print_warning "No environment file found. Using defaults."
    fi
fi

# Build and start services
print_status "Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
print_status "Waiting for services to be ready..."

# Wait for Ollama
print_status "Waiting for Ollama service..."
timeout=120
counter=0
while ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        print_error "Ollama service failed to start within $timeout seconds"
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done
echo ""
print_success "Ollama service is ready!"

# Wait for Redis
print_status "Waiting for Redis service..."
counter=0
while ! docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    if [ $counter -ge 30 ]; then
        print_error "Redis service failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
    counter=$((counter + 1))
    echo -n "."
done
echo ""
print_success "Redis service is ready!"

# Wait for AI Service
print_status "Waiting for AI Service..."
counter=0
while ! curl -s http://localhost:8001/health > /dev/null 2>&1; do
    if [ $counter -ge 60 ]; then
        print_error "AI Service failed to start within 60 seconds"
        print_status "Checking service logs..."
        docker-compose logs ai-service
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done
echo ""
print_success "AI Service is ready!"

# Initialize Ollama model (if not already done)
print_status "Ensuring Llama model is available..."
if ! docker-compose exec -T ollama ollama list | grep -q "llama3.2:3b"; then
    print_status "Pulling Llama 3.2:3b model (this may take a while)..."
    docker-compose exec -T ollama ollama pull llama3.2:3b
    print_success "Llama model ready!"
else
    print_success "Llama model already available!"
fi

# Show service status
print_success "All services are running!"
echo ""
echo "🎉 Poon AI Service is ready for testing!"
echo ""
echo "📊 Service URLs:"
echo "  • AI Service:    http://localhost:8001"
echo "  • API Docs:      http://localhost:8001/docs"
echo "  • Health Check:  http://localhost:8001/health"
echo "  • Ollama:        http://localhost:11434"
echo "  • Redis:         localhost:6379"
echo ""
echo "📈 Monitoring (optional):"
echo "  • Prometheus:    http://localhost:9090"
echo "  • Grafana:       http://localhost:3000 (admin/admin)"
echo ""
echo "🧪 Testing:"
echo "  • Run Bruno tests against http://localhost:8001"
echo "  • Use curl: curl http://localhost:8001/health"
echo ""
echo "📝 Logs:"
echo "  • View logs: docker-compose logs -f"
echo "  • AI Service: docker-compose logs -f ai-service"
echo "  • Ollama: docker-compose logs -f ollama"
echo ""
echo "🛑 To stop:"
echo "  • docker-compose down"
echo "  • docker-compose down -v (remove volumes)"
echo ""

# Test the service
print_status "Running basic health check..."
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    print_success "Health check passed! ✅"
else
    print_warning "Health check failed. Check service logs."
fi

# Test AI processing
print_status "Testing AI text processing..."
if curl -s -X POST http://localhost:8001/api/v1/spending/process/text \
    -H "Content-Type: application/json" \
    -d '{"text": "Coffee at Starbucks 120 baht", "language": "en"}' | grep -q "success"; then
    print_success "AI processing test passed! ✅"
else
    print_warning "AI processing test failed. This is normal if Ollama is still initializing."
fi

print_success "Setup complete! 🎊"
