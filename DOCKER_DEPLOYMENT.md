# 🐳 Poon AI Service - Complete Docker Deployment

## 🚀 Quick Start (One Command)

```bash
# Start everything with one command
./docker/start.sh
```

This will:
- ✅ Build all services
- ✅ Start Ollama, Redis, and AI Service
- ✅ Download Llama 3.2:3b model
- ✅ Run health checks
- ✅ Show service URLs

## 📋 What's Included

### Core Services
- **AI Service** (Port 8001) - Main FastAPI application with Tesseract OCR
- **Ollama** (Port 11434) - AI model server with Llama 3.2:3b
- **Redis** (Port 6379) - Caching and session storage

### Optional Monitoring
- **Prometheus** (Port 9090) - Metrics collection
- **Grafana** (Port 3000) - Monitoring dashboards

### Features
- ✅ **Tesseract OCR** - Multi-language text extraction (English, Thai, Chinese, Japanese, Korean)
- ✅ **AI Processing** - Natural language spending analysis
- ✅ **Health Checks** - Comprehensive service monitoring
- ✅ **Auto-scaling** - Resource limits and reservations
- ✅ **Persistent Storage** - Data volumes for models and cache
- ✅ **Network Isolation** - Secure service communication

## 🛠️ Management Commands

### Using the Startup Script
```bash
# Start all services (recommended)
./docker/start.sh

# The script will:
# - Check Docker availability
# - Build and start services
# - Wait for health checks
# - Download AI models
# - Run basic tests
# - Show service URLs
```

### Using the Makefile
```bash
cd docker/

# Show all commands
make help

# Start services
make up

# Start with monitoring
make up-with-monitoring

# Check status
make status

# Run health checks
make health

# View logs
make logs

# Stop services
make down
```

### Using Docker Compose Directly
```bash
# Start all services
docker-compose up -d

# Start with monitoring
docker-compose --profile monitoring up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🧪 Testing

### Automated Testing
```bash
# Run comprehensive tests
./docker/test-deployment.sh

# Or use Makefile
make test
```

### Manual Testing
```bash
# Health check
curl http://localhost:8001/health

# Create spending entry
curl -X POST http://localhost:8001/api/v1/spending/ \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 120.50,
    "merchant": "Starbucks",
    "description": "Coffee",
    "category": "Food & Dining",
    "payment_method": "Credit Card"
  }'

# Process natural language text
curl -X POST http://localhost:8001/api/v1/spending/process/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bought lunch at McDonald'\''s for 250 baht with cash",
    "language": "en"
  }'

# Thai language processing
curl -X POST http://localhost:8001/api/v1/spending/process/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "ซื้อกาแฟที่สตาร์บัคส์ 120 บาท จ่ายด้วยบัตรเครดิต",
    "language": "th"
  }'
```

### Bruno API Testing
```bash
# Point Bruno to http://localhost:8001
# All Bruno collections are updated and working
```

## 📊 Service URLs

### Core Services
- **AI Service**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **Detailed Health**: http://localhost:8001/api/v1/health/detailed
- **Metrics**: http://localhost:8001/metrics
- **Ollama**: http://localhost:11434
- **Redis**: localhost:6379

### Monitoring (Optional)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 🔧 Configuration

### Environment Variables
All configuration is in `docker-compose.yml`:

```yaml
# Application
DEBUG=true
ENVIRONMENT=development
APP_NAME=Poon AI Service

# Database
DATABASE_URL=sqlite:///./data/spending.db

# AI Service
OLLAMA_URL=http://ollama:11434
LLAMA_MODEL=llama3.2:3b

# OCR
TESSERACT_PATH=/usr/bin/tesseract
TESSERACT_LANGUAGES=eng+tha+chi_sim+jpn+kor

# Caching
REDIS_URL=redis://redis:6379/0

# Monitoring
ENABLE_METRICS=true
```

### Custom Configuration
1. Copy `docker/env.docker` to `.env` in project root
2. Modify values as needed
3. Restart: `docker-compose restart`

## 🐛 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker
docker info

# Check logs
docker-compose logs

# Restart in order
docker-compose restart ollama
sleep 10
docker-compose restart ai-service
```

#### Ollama Model Issues
```bash
# Manual model download
docker-compose exec ollama ollama pull llama3.2:3b

# Check models
docker-compose exec ollama ollama list

# Check Ollama health
curl http://localhost:11434/api/tags
```

#### Out of Memory
```bash
# Check memory usage
docker stats

# Increase Docker memory in Docker Desktop
# Recommended: 4GB minimum, 8GB preferred
```

#### Port Conflicts
```bash
# Check ports
lsof -i :8001
lsof -i :11434
lsof -i :6379

# Change ports in docker-compose.yml if needed
```

### Health Checks
```bash
# All services
make status

# Individual checks
curl http://localhost:8001/health
curl http://localhost:11434/api/tags
docker-compose exec redis redis-cli ping
```

## 📁 File Structure

```
docker/
├── Dockerfile.tesseract     # Multi-stage build with Tesseract
├── start.sh                 # One-command startup script
├── test-deployment.sh       # Comprehensive test script
├── Makefile                 # Management commands
├── env.docker               # Environment template
├── prometheus.yml           # Prometheus configuration
├── grafana/                 # Grafana dashboards and datasources
└── README.md               # Detailed documentation

docker-compose.yml           # Main compose file
requirements.txt             # Updated with OCR dependencies
```

## 🎯 Ready for Production

### What's Included
- ✅ Multi-stage Docker builds
- ✅ Health checks and monitoring
- ✅ Resource limits and reservations
- ✅ Persistent volumes
- ✅ Network security
- ✅ Comprehensive logging
- ✅ Graceful shutdowns

### Production Checklist
- [ ] Change default passwords
- [ ] Use proper secrets management
- [ ] Enable HTTPS/TLS
- [ ] Configure proper CORS origins
- [ ] Set up backup strategies
- [ ] Configure log rotation
- [ ] Set up monitoring alerts

## 🎉 Success!

Your Poon AI Service is now fully containerized and ready for:
- ✅ Local development
- ✅ Testing with Bruno
- ✅ CI/CD integration
- ✅ Production deployment

**All services are working perfectly together!** 🚀
