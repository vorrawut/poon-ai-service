#!/bin/bash

# 🚀 Poon AI Microservice Startup Script
# Ultra-fast OCR, NLP, and AI processing service

set -e

echo "🤖 Starting Poon AI Microservice..."

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

# Check if running in Docker
if [ -f /.dockerenv ]; then
    print_status "Running in Docker container"
    DOCKER_MODE=true
else
    DOCKER_MODE=false
fi

# Check Python version
print_status "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_success "Python $python_version is compatible"
else
    print_error "Python 3.8+ is required, found $python_version"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ "$DOCKER_MODE" = false ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment (if not in Docker)
if [ "$DOCKER_MODE" = false ]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for environment file
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        print_warning "No .env file found, copying from env.example"
        cp env.example .env
        print_status "Please edit .env file with your configuration"
    else
        print_error "No .env or env.example file found"
        exit 1
    fi
fi

# Load environment variables
if [ -f ".env" ]; then
    print_status "Loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set defaults
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"8001"}
export ENVIRONMENT=${ENVIRONMENT:-"development"}
export DEBUG=${DEBUG:-"true"}
export RELOAD=${RELOAD:-"true"}

# Check optional dependencies
print_status "Checking optional dependencies..."

# Check Tesseract
if command -v tesseract >/dev/null 2>&1; then
    tesseract_version=$(tesseract --version | head -1)
    print_success "Tesseract found: $tesseract_version"
    
    # Check Thai language support
    if tesseract --list-langs 2>/dev/null | grep -q "tha"; then
        print_success "Thai language support available"
    else
        print_warning "Thai language pack not found - install tesseract-ocr-tha for better Thai support"
    fi
else
    print_warning "Tesseract OCR not found - OCR will use OpenAI Vision fallback only"
fi

# Check Redis
if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli ping >/dev/null 2>&1; then
        print_success "Redis server is running"
    else
        print_warning "Redis server not responding - using in-memory cache"
    fi
else
    print_warning "Redis not found - using in-memory cache"
fi

# Check OpenAI API key
if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "your_openai_api_key_here" ]; then
    print_success "OpenAI API key configured"
else
    print_warning "OpenAI API key not configured - AI fallback disabled"
fi

# Create logs directory
mkdir -p logs

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for service to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://$HOST:$PORT/health" >/dev/null 2>&1; then
            print_success "Service is healthy and ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "Service failed to start within 30 seconds"
    return 1
}

# Start the service
print_status "Starting AI microservice..."
print_status "Environment: $ENVIRONMENT"
print_status "Host: $HOST"
print_status "Port: $PORT"
print_status "Debug: $DEBUG"
print_status "Reload: $RELOAD"

# Determine startup command based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    print_status "Starting in production mode with Gunicorn..."
    
    # Install gunicorn if not present
    pip install gunicorn uvicorn[standard]
    
    # Start with Gunicorn
    exec gunicorn main:app \
        -w 4 \
        -k uvicorn.workers.UvicornWorker \
        --bind "$HOST:$PORT" \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log \
        --log-level info \
        --timeout 120 \
        --keep-alive 2 \
        --max-requests 1000 \
        --max-requests-jitter 100
else
    print_status "Starting in development mode with Uvicorn..."
    
    # Start with Uvicorn for development
    if [ "$RELOAD" = "true" ]; then
        exec uvicorn main:app \
            --host "$HOST" \
            --port "$PORT" \
            --reload \
            --log-level info \
            --access-log
    else
        exec uvicorn main:app \
            --host "$HOST" \
            --port "$PORT" \
            --log-level info \
            --access-log
    fi
fi
