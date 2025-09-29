# 📚 Poon AI Service - Technical Documentation

This directory contains comprehensive technical documentation for the Poon AI Service, including UML diagrams, architecture overviews, and integration guides.

## 🗂️ Documentation Structure

### 📊 UML Diagrams

#### 1. **System Overview** (`system-overview.puml`)
High-level system architecture showing:
- Frontend React components
- AI microservice components  
- External service integrations
- Data flow between systems
- Primary vs fallback AI services

#### 2. **Processing Flow** (`processing-flow.puml`)
Detailed sequence diagrams for:
- Photo receipt processing (OCR → NLP → AI)
- Voice/chat text processing
- Batch file processing
- AI analysis workflows
- Caching and optimization strategies

#### 3. **Service Architecture** (`service-architecture.puml`)
Internal service architecture including:
- FastAPI application structure
- Core service classes and relationships
- Data models and their interactions
- External service integrations
- Dependency relationships

#### 4. **API Endpoints** (`api-endpoints.puml`)
Complete API documentation showing:
- All available endpoints
- Request/response schemas
- Data model relationships
- Processing capabilities
- Error handling patterns

#### 5. **Frontend Integration** (`frontend-integration.puml`)
Frontend integration patterns:
- React component architecture
- API integration points
- State management flow
- Error handling strategies
- User experience flows

#### 6. **Deployment Architecture** (`deployment-architecture.puml`)
Production deployment overview:
- Development vs production environments
- Load balancing and scaling
- Monitoring and logging setup
- CI/CD pipeline integration
- Infrastructure requirements

## 🎯 Key Architectural Decisions

### **AI-First Design**
- **Primary**: Llama4 via Ollama (local, free, private)
- **Fallback**: OpenAI GPT (cloud, paid, when needed)
- **Cost Optimization**: 90% local processing, 10% cloud fallback

### **Performance Strategy**
- **Caching**: Redis for repeated requests
- **Local Processing**: Tesseract OCR + pattern matching NLP
- **Async Processing**: FastAPI with background tasks
- **Load Balancing**: Horizontal scaling support

### **Data Privacy**
- **Local AI**: Sensitive data never leaves your infrastructure
- **Minimal Cloud**: Only anonymous/encrypted data to OpenAI
- **Caching**: Local Redis with TTL expiration
- **Compliance**: GDPR/CCPA ready architecture

## 🔧 Technical Specifications

### **Core Technologies**
- **Backend**: Python 3.11+ with FastAPI
- **AI Processing**: Llama4 via Ollama (primary)
- **OCR**: Tesseract with OpenCV preprocessing
- **Caching**: Redis with memory fallback
- **Containerization**: Docker with Kubernetes support

### **Performance Targets**
- **Health Check**: <100ms response time
- **OCR Processing**: <3 seconds for clear images
- **NLP Processing**: <500ms for text parsing
- **Complete Processing**: <5 seconds end-to-end
- **AI Analysis**: <10 seconds for pattern analysis

### **Scalability**
- **Horizontal Scaling**: Multiple AI service instances
- **Load Balancing**: Nginx or cloud load balancers
- **Caching Strategy**: Distributed Redis cluster
- **GPU Support**: NVIDIA GPU acceleration for Llama4

## 📈 Processing Capabilities

### **Input Methods Supported**
1. **Photo/Receipt Upload**: OCR + AI extraction
2. **Voice Input**: Speech-to-text + NLP parsing
3. **Chat/Text Input**: Natural language processing
4. **File Upload**: CSV/Excel/JSON batch processing
5. **Manual Entry**: Direct form input
6. **Quick Templates**: Predefined spending patterns

### **Language Support**
- **English**: Full support with US/UK variants
- **Thai**: Complete Thai language processing
- **Mixed Language**: Automatic detection and processing
- **Extensible**: Architecture ready for additional languages

### **AI Capabilities**
- **Text Extraction**: OCR with confidence scoring
- **Entity Recognition**: Merchant, amount, category, date
- **Pattern Analysis**: Spending behavior insights
- **Anomaly Detection**: Unusual spending identification
- **Recommendations**: Actionable financial advice

## 🔄 Integration Patterns

### **Frontend Integration**
```typescript
// Photo processing
const result = await fetch('/process/receipt', {
  method: 'POST',
  body: formData
});

// Text processing
const result = await fetch('/process/text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: userInput })
});
```

### **Backend Integration**
```python
# Service initialization
llama_service = LlamaService(settings)
nlp_result = await llama_service.enhance_nlp_result(text, initial_result)
```

### **Monitoring Integration**
```yaml
# Prometheus metrics
- ai_requests_total
- ai_processing_duration_seconds
- ai_confidence_score
- cache_hit_ratio
```

## 🚀 Deployment Guide

### **Development Setup**
1. Install Python 3.11+ and dependencies
2. Install Ollama and pull Llama4 model
3. Start Redis (optional, will use memory cache)
4. Run FastAPI development server

### **Production Deployment**
1. Build Docker container
2. Deploy to Kubernetes cluster
3. Configure load balancer
4. Setup monitoring and logging
5. Configure SSL/TLS certificates

### **Environment Configuration**
```bash
# Primary AI (recommended)
USE_LLAMA=true
OLLAMA_URL=http://localhost:11434
LLAMA_MODEL=llama4

# Fallback AI (optional)
OPENAI_API_KEY=your_key_here

# Performance tuning
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
```

## 📊 Monitoring and Observability

### **Health Checks**
- Service availability monitoring
- AI service status (Llama4/OpenAI)
- External dependency health
- Performance metrics tracking

### **Logging Strategy**
- Structured JSON logging
- Request/response tracing
- Error tracking and alerting
- Performance profiling

### **Metrics Collection**
- Request volume and latency
- AI processing accuracy
- Cache hit/miss ratios
- Resource utilization

## 🔒 Security Considerations

### **Data Protection**
- Input validation and sanitization
- Rate limiting and throttling
- API key management
- Secure file upload handling

### **Privacy Compliance**
- Local AI processing (data never leaves)
- Minimal cloud API usage
- Audit logging capabilities
- Data retention policies

### **Infrastructure Security**
- Container security scanning
- Network segmentation
- SSL/TLS encryption
- Access control and authentication

## 🧪 Testing Strategy

### **API Testing**
- Bruno collection for comprehensive testing
- Unit tests for individual services
- Integration tests for workflows
- Load testing for performance validation

### **AI Quality Testing**
- OCR accuracy benchmarks
- NLP parsing validation
- AI enhancement effectiveness
- Multi-language processing tests

### **Performance Testing**
- Response time validation
- Concurrent request handling
- Memory usage profiling
- Cache efficiency testing

## 📋 Maintenance and Operations

### **Regular Tasks**
- Model updates (Llama4 versions)
- Cache cleanup and optimization
- Log rotation and archival
- Performance monitoring review

### **Troubleshooting**
- Common error patterns
- Performance bottleneck identification
- AI service connectivity issues
- Cache invalidation strategies

### **Scaling Operations**
- Horizontal scaling procedures
- Load balancing configuration
- Resource allocation optimization
- Capacity planning guidelines

---

## 🎯 Quick Start

1. **View Diagrams**: Open `.puml` files in PlantUML viewer
2. **Test APIs**: Use Bruno collection in `../bruno/`
3. **Deploy Service**: Follow deployment architecture guide
4. **Monitor System**: Setup observability stack

## 🔗 Related Documentation

- **API Reference**: See Bruno collection
- **Frontend Integration**: React component documentation
- **Deployment Guide**: Infrastructure setup instructions
- **Performance Tuning**: Optimization best practices

---

**🚀 This documentation ensures successful implementation and operation of the Poon AI Service!**
