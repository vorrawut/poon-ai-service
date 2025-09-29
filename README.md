# 🤖 Poon AI Microservice

Ultra-fast AI-powered OCR, NLP, and spending analysis service for the Poon Financial App.

## 🚀 Features

- **📸 OCR Processing**: Tesseract.js for local processing, OpenAI Vision fallback
- **🧠 NLP Analysis**: Local pattern matching with AI enhancement
- **💬 Text Processing**: Voice and chat input parsing
- **📊 Batch Processing**: CSV, Excel, JSON file imports
- **🔍 AI Insights**: Spending pattern analysis and recommendations
- **🇹🇭 Thai Support**: Full Thai language and cultural context
- **⚡ Performance**: Caching, rate limiting, optimized processing
- **💰 Cost Efficient**: Local processing first, AI fallback only when needed

## 🏗️ Architecture

```
ai-service/
├── main.py                    # FastAPI application entry point
├── config/
│   ├── settings.py           # Environment-based configuration
│   └── __init__.py
├── models/
│   └── spending_models.py    # Pydantic models for validation
├── services/
│   ├── ocr_service.py        # OCR processing (Tesseract + OpenAI Vision)
│   ├── nlp_service.py        # Local NLP with pattern matching
│   ├── ai_service.py         # OpenAI GPT integration
│   └── cache_service.py      # Redis/memory caching
├── utils/
│   ├── image_utils.py        # Image preprocessing utilities
│   ├── text_utils.py         # Text processing utilities
│   └── cache.py              # Cache management
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Tesseract OCR (optional, for local processing)
- Redis (optional, for caching)

### 1. Install Python Dependencies

```bash
cd backend/ai-service
pip install -r requirements.txt
```

### 2. Install Tesseract OCR (Optional but Recommended)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-tha tesseract-ocr-eng
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### 3. Install Redis (Optional)

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
```

**macOS:**
```bash
brew install redis
```

**Or use Docker:**
```bash
docker run -d -p 6379:6379 redis:alpine
```

### 4. Configure Environment

```bash
cp env.example .env
# Edit .env with your configuration
```

## ⚙️ Configuration

Key environment variables:

```env
# Required
ENVIRONMENT=development
PORT=8001

# Optional - OpenAI for AI fallback
OPENAI_API_KEY=your_key_here

# Optional - Redis for caching
REDIS_URL=redis://localhost:6379/0

# OCR Settings
OCR_CONFIDENCE_THRESHOLD=0.7
NLP_CONFIDENCE_THRESHOLD=0.6
AI_FALLBACK_THRESHOLD=0.5
```

## 🚀 Running the Service

### Development Mode

```bash
python main.py
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

### With Docker (Coming Soon)

```bash
docker build -t poon-ai-service .
docker run -p 8001:8001 poon-ai-service
```

## 📡 API Endpoints

### Health Check
```
GET /health
```

### OCR Processing
```
POST /ocr/process
- file: Image file (JPEG, PNG, WebP, HEIC)
- language: "eng+tha" (default), "eng", "tha"
- confidence_threshold: 0.7 (default)
```

### NLP Text Parsing
```
POST /nlp/parse
- text: Text to parse
- language: "en" (default), "th", "auto"
- use_local_only: true (default)
```

### Complete Receipt Processing
```
POST /process/receipt
- file: Receipt image
- language: "eng+tha" (default)
- use_ai_fallback: true (default)
- confidence_threshold: 0.8 (default)
```

### Text Processing (Voice/Chat)
```
POST /process/text
- text: Natural language text
- language: "auto" (default)
- use_ai_fallback: true (default)
- context: Optional context object
```

### Batch Processing
```
POST /process/batch
- data: Array of data entries
- use_ai_enhancement: false (default)
```

### AI Analysis
```
POST /analyze/spending
- entries: Array of SpendingEntry objects
- analysis_type: "comprehensive" (default)
```

### Utility Endpoints
```
GET /categories/suggest?merchant=...&amount=...&description=...
GET /merchants/normalize?name=...
```

## 🎯 Performance & Optimization

### Local-First Approach
- **Tesseract OCR**: Free, fast, runs locally
- **Pattern Matching NLP**: Regex-based, instant results
- **Caching**: Redis for repeated requests
- **Rate Limiting**: Prevents abuse

### AI Fallback Strategy
- Only used when local confidence < threshold
- Cost-optimized with GPT-4o-mini
- Cached results to avoid repeated API calls
- Target: <$20/month at scale

### Processing Pipeline
```
Image → Preprocess → Tesseract OCR → NLP Parse → AI Enhance (if needed) → Result
Text → Clean → Pattern Match → AI Enhance (if needed) → Result
```

## 📊 Cost Analysis

**Local Processing (Free):**
- Tesseract OCR: 100% free
- Pattern matching NLP: 100% free
- Image preprocessing: 100% free

**AI Fallback (Paid):**
- GPT-4o-mini: $0.00015/1K input tokens
- Typical receipt: ~500 tokens = $0.000075
- Target usage: <10% of requests
- Monthly cost: <$20 at 10K receipts/month

## 🧪 Testing

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:8001/health

# Test OCR with image
curl -X POST -F "file=@receipt.jpg" http://localhost:8001/ocr/process

# Test NLP parsing
curl -X POST -H "Content-Type: application/json" \
  -d '{"text":"Coffee at Starbucks 120 baht"}' \
  http://localhost:8001/nlp/parse
```

### Unit Tests (Coming Soon)
```bash
pytest tests/
```

## 🔒 Security

- Input validation with Pydantic models
- File type and size restrictions
- Rate limiting to prevent abuse
- Optional API key authentication
- CORS configuration for frontend access

## 🌍 Thai Language Support

- **OCR**: Tesseract Thai language pack
- **NLP**: Thai keyword patterns and regex
- **Cultural Context**: Thai spending categories
- **Number Formats**: Thai Baht formatting
- **Date Formats**: Buddhist calendar support

## 🚨 Error Handling

The service implements graceful degradation:

1. **OCR Failure**: Falls back to manual entry
2. **NLP Low Confidence**: Falls back to AI enhancement
3. **AI API Failure**: Returns local results with lower confidence
4. **Cache Failure**: Continues without caching
5. **Rate Limit**: Returns 429 with retry information

## 📈 Monitoring

### Health Metrics
- Service uptime and health
- Processing success rates
- Average confidence scores
- Cache hit/miss rates

### Performance Metrics
- Request processing times
- OCR confidence distribution
- AI fallback usage rates
- Cost per request

## 🔄 Development Workflow

1. **Local Development**: Use Tesseract + Redis
2. **Testing**: Mock AI services for cost efficiency
3. **Staging**: Full AI integration with low limits
4. **Production**: Optimized caching and rate limiting

## 🤝 Integration

### Frontend Integration
```typescript
// OCR Processing
const formData = new FormData();
formData.append('file', imageFile);
const result = await fetch('http://localhost:8001/process/receipt', {
  method: 'POST',
  body: formData
});

// Text Processing
const result = await fetch('http://localhost:8001/process/text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: 'Coffee 120 baht', use_ai_fallback: true })
});
```

### Backend Integration
```typescript
// From NestJS backend
const aiResponse = await this.httpService.post('http://ai-service:8001/process/receipt', formData);
const spendingEntry = aiResponse.data;
```

## 🎯 Roadmap

- [ ] **Docker Support**: Containerized deployment
- [ ] **Kubernetes**: Production orchestration  
- [ ] **Monitoring**: Prometheus metrics
- [ ] **ML Models**: Local spending classification
- [ ] **Multi-language**: Support for more languages
- [ ] **Real-time**: WebSocket support for live processing
- [ ] **Mobile**: Optimized mobile image processing

## 📝 License

MIT License - See LICENSE file for details

## 🙋 Support

For issues and questions:
1. Check the logs: `tail -f ai-service.log`
2. Verify configuration: `GET /api/config`
3. Test health: `GET /health`
4. Check dependencies: `pip list`

---

**🚀 Built for the Poon Financial App - Making spending tracking lightning fast and delightful!**
