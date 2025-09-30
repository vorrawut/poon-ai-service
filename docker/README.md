# 🐳 Poon AI Service - Docker Deployment

Complete Docker setup for running the Poon AI Service locally with all necessary dependencies.

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (4.20+)
- Docker Compose (2.20+)
- At least 4GB RAM available for containers
- 10GB free disk space (for AI models)

### One-Command Setup

```bash
# From the project root
./docker/start.sh
```

This will:

- ✅ Build all services
- ✅ Start Ollama, Redis, and AI Service
- ✅ Download the Llama 3.2:3b model
- ✅ Run health checks
- ✅ Show service URLs

## 📋 Services Included

### Core Services

| Service        | Port  | Description                    | Health Check                      |
| -------------- | ----- | ------------------------------ | --------------------------------- |
| **AI Service** | 8001  | Main FastAPI application       | `http://localhost:8001/health`    |
| **Ollama**     | 11434 | AI model server (Llama 3.2:3b) | `http://localhost:11434/api/tags` |
| **Redis**      | 6379  | Caching and session storage    | `redis-cli ping`                  |

### Optional Services (Monitoring)

| Service        | Port | Description           | Credentials |
| -------------- | ---- | --------------------- | ----------- |
| **Prometheus** | 9090 | Metrics collection    | -           |
| **Grafana**    | 3000 | Monitoring dashboards | admin/admin |

## 🛠️ Management Commands

### Using the Makefile

```bash
cd docker/

# Show all available commands
make help

# Start services
make up

# Start with monitoring
make up-with-monitoring

# Check service status
make status

# Run health checks
make health

# View logs
make logs
make logs-ai
make logs-ollama

# Stop services
make down

# Clean everything
make clean
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

# Remove volumes too
docker-compose down -v
```

## 🧪 Testing the Setup

### 1. Health Checks

```bash
# Basic health
curl http://localhost:8001/health

# Detailed health with dependencies
curl http://localhost:8001/api/v1/health/detailed
```

### 2. API Testing

```bash
# Get spending entries
curl http://localhost:8001/api/v1/spending/

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
```

### 3. Bruno API Testing

```bash
# Open Bruno and test against http://localhost:8001
bruno open ../bruno/
```

## 🔧 Configuration

### Environment Variables

The services use environment variables defined in the docker-compose.yml:

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

1. Copy `docker/env.docker` to `.env` in the project root
2. Modify values as needed
3. Restart services: `docker-compose restart`

## 📊 Monitoring & Observability

### Prometheus Metrics

- **URL**: http://localhost:9090
- **Metrics**: HTTP requests, response times, AI processing stats
- **Targets**: AI Service, Redis

### Grafana Dashboards

- **URL**: http://localhost:3000
- **Login**: admin/admin
- **Datasource**: Prometheus (auto-configured)

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ai-service
docker-compose logs -f ollama
docker-compose logs -f redis

# Follow logs with timestamps
docker-compose logs -f -t
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Services Won't Start

```bash
# Check Docker is running
docker info

# Check available resources
docker system df

# View detailed logs
docker-compose logs
```

#### 2. Ollama Model Download Fails

```bash
# Manual model download
docker-compose exec ollama ollama pull llama3.2:3b

# Check available models
docker-compose exec ollama ollama list

# Check Ollama service
curl http://localhost:11434/api/tags
```

#### 3. AI Service Can't Connect to Ollama

```bash
# Check network connectivity
docker-compose exec ai-service ping ollama

# Restart services in order
docker-compose restart ollama
sleep 10
docker-compose restart ai-service
```

#### 4. Out of Memory

```bash
# Check container memory usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
# Recommended: 4GB minimum, 8GB preferred
```

#### 5. Port Conflicts

```bash
# Check what's using the ports
lsof -i :8001
lsof -i :11434
lsof -i :6379

# Stop conflicting services or change ports in docker-compose.yml
```

### Health Check Commands

```bash
# AI Service
curl -f http://localhost:8001/health

# Ollama
curl -f http://localhost:11434/api/tags

# Redis
docker-compose exec redis redis-cli ping

# All services status
make status
```

## 🔒 Security Notes

### Development vs Production

This setup is optimized for **local development and testing**. For production:

1. **Change default passwords**
2. **Use proper secrets management**
3. **Enable authentication**
4. **Configure proper CORS origins**
5. **Use HTTPS**
6. **Limit exposed ports**

### Current Security Features

- ✅ Non-root user in production container
- ✅ Health checks enabled
- ✅ Resource limits configured
- ✅ Network isolation
- ⚠️ Default passwords (change for production)
- ⚠️ Debug mode enabled (disable for production)

## 📈 Performance Tuning

### Resource Allocation

```yaml
# In docker-compose.yml
deploy:
  resources:
    reservations:
      memory: 2G
    limits:
      memory: 4G
      cpus: "2.0"
```

### Ollama Optimization

- **Model Size**: llama3.2:3b (~2GB)
- **Memory**: 2-4GB recommended
- **CPU**: 2+ cores recommended
- **GPU**: Optional, requires nvidia-docker

### Redis Optimization

- **Memory**: 256MB limit configured
- **Persistence**: AOF enabled
- **Eviction**: allkeys-lru policy

## 🚀 Advanced Usage

### Custom Models

```bash
# Use different Llama model
docker-compose exec ollama ollama pull llama3.2:1b
# Update LLAMA_MODEL in environment

# List available models
docker-compose exec ollama ollama list
```

### Development Mode

```bash
# Mount source code for live reload
# Already configured in docker-compose.yml
volumes:
  - .:/app
```

### Production Deployment

```bash
# Use production target
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📝 File Structure

```
docker/
├── Dockerfile.tesseract     # Multi-stage Docker build
├── docker-compose.yml       # Main compose file
├── start.sh                 # Startup script
├── Makefile                 # Management commands
├── env.docker               # Environment template
├── prometheus.yml           # Prometheus config
├── grafana/                 # Grafana configuration
│   ├── dashboards/
│   └── datasources/
└── README.md               # This file
```

---

## 🎯 Ready for Testing!

Once everything is running:

1. **API Documentation**: http://localhost:8001/docs
2. **Health Check**: http://localhost:8001/health
3. **Bruno Tests**: Point to http://localhost:8001
4. **Monitoring**: http://localhost:9090 (Prometheus), http://localhost:3000 (Grafana)

**Happy coding! 🚀**
