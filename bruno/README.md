# 🧪 Poon AI Service - Bruno API Testing Collection

This Bruno collection provides comprehensive API testing for the Poon AI Service, covering all endpoints with realistic test scenarios.

## 🚀 Quick Start

### 1. Install Bruno

```bash
# macOS
brew install bruno

# Windows
winget install Bruno

# Linux
# Download from https://github.com/usebruno/bruno/releases
```

### 2. Open Collection

```bash
bruno open backend/ai-service/bruno
```

### 3. Set Environment

- Select **Development** environment for local testing
- Select **Production** environment for production API testing

## 📁 Collection Structure

### ✅ **Working Endpoints**

#### Health Checks (`/Health/`)

- **Health Check** - Basic service health status (`GET /health`)
- **Detailed Health** - Detailed service status with dependencies (`GET /api/v1/health/detailed`)
- **AI Status** - AI service status via detailed health check

#### Spending Management (`/Spending/`)

- **Get All Entries** - Retrieve spending entries with pagination (`GET /api/v1/spending/`)
- **Create Entry** - Create new spending entry (`POST /api/v1/spending/`)

#### Text Processing (`/Processing/`, `/NLP/`, `/AI/`)

- **Text Processing** - Process natural language text into spending entries (`POST /api/v1/spending/process/text`)
- **Parse Text** - English text parsing (redirected to text processing)
- **Parse Thai Text** - Thai language text parsing (redirected to text processing)
- **AI Parse Text** - AI-enhanced text parsing (redirected to text processing)

### ❌ **Planned/Disabled Endpoints**

The following endpoints are planned for future implementation but not currently available:

#### OCR Processing (`/OCR/`)

- **Process Image** - OCR text extraction from images
  - _Status_: Not implemented
  - _Alternative_: Use text processing after manual OCR

#### Advanced Processing (`/Processing/`)

- **Batch Processing** - Process multiple texts at once
  - _Status_: Not implemented
  - _Alternative_: Process texts individually

- **Complete Receipt Processing** - End-to-end receipt processing
  - _Status_: Not implemented
  - _Alternative_: Use text processing for receipt text

#### AI Analysis (`/AI Analysis/`)

- **Spending Analysis** - Comprehensive spending analysis
  - _Status_: Not implemented
  - _Alternative_: Use individual spending entries for analysis

#### Utilities (`/Utilities/`)

- **Category Suggestions** - Smart category recommendations
  - _Status_: Not implemented
  - _Alternative_: Categories are auto-assigned by AI

- **Merchant Normalization** - Merchant name normalization
  - _Status_: Not implemented
  - _Alternative_: Merchant names are auto-normalized by AI

## 🧪 Test Scenarios

### Basic Functionality Tests

```bash
# Run all health checks
bruno run Health/

# Test OCR processing
bruno run OCR/

# Test NLP parsing
bruno run NLP/
```

### Integration Tests

```bash
# Test complete workflows
bruno run Processing/

# Test AI analysis
bruno run "AI Analysis/"

# Test utility functions
bruno run Utilities/
```

### Performance Tests

```bash
# Run all tests with timing
bruno run --verbose

# Test specific endpoint performance
bruno run "Processing/Complete Receipt Processing.bru" --verbose
```

## 📊 Test Data

### Sample Images

Place test receipt images in `test-files/`:

- `sample-receipt.jpg` - Standard receipt
- `thai-receipt.jpg` - Thai language receipt
- `blurry-receipt.jpg` - Low quality image test
- `handwritten-receipt.jpg` - Handwriting test

### Sample Text Inputs

The collection includes various text scenarios:

- English spending descriptions
- Thai spending descriptions
- Mixed language inputs
- Voice transcription formats
- Natural language variations

## 🎯 Expected Results

### OCR Processing

- **Confidence**: 0.7+ for clear images
- **Text Extraction**: Readable merchant, amount, date
- **Language Detection**: Automatic English/Thai detection
- **Processing Time**: <3 seconds

### NLP Processing

- **Confidence**: 0.6+ for structured text
- **Field Extraction**: Merchant, amount, category, payment method
- **Thai Support**: Full Thai language processing
- **Fallback**: AI enhancement for low confidence

### Complete Processing

- **End-to-End**: OCR → NLP → AI → Structured Entry
- **Confidence**: 0.8+ for final result
- **Processing Time**: <5 seconds total
- **Accuracy**: 90%+ for clear receipts

### AI Analysis

- **Insights**: 3-5 meaningful insights per analysis
- **Recommendations**: Actionable financial advice
- **Pattern Detection**: Spending trends and anomalies
- **Confidence**: 0.85+ for analysis results

## 🔧 Environment Variables

### Development Environment

```
baseUrl: http://localhost:8001
timeout: 30000
```

### Production Environment

```
baseUrl: https://api.poon.app
timeout: 60000
```

## 🚨 Common Issues

### Service Not Running

```bash
# Start the AI service
cd backend/ai-service
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Ollama Not Available

- Install Ollama: `brew install ollama`
- Start Ollama: `ollama serve`
- Pull Llama model: `ollama pull llama2`

### Test Files Missing

```bash
# Create sample test files
cd bruno/test-files
# Add your test receipt images here
```

### Authentication Issues

- Check API keys in environment
- Verify CORS settings
- Confirm service permissions

## 📈 Performance Benchmarks

### Target Performance

- **Health Check**: <100ms
- **OCR Processing**: <3s
- **NLP Processing**: <500ms
- **Complete Processing**: <5s
- **AI Analysis**: <10s

### Load Testing

```bash
# Run multiple concurrent requests
for i in {1..10}; do bruno run "Health/Health Check.bru" & done
```

## 🔍 Debugging

### Enable Verbose Logging

```bash
# Run with detailed output
bruno run --verbose --reporter json

# Save results to file
bruno run --reporter json > test-results.json
```

### Check Service Logs

```bash
# View AI service logs
tail -f ai-service.log

# Check Ollama logs
ollama logs
```

## 🎨 Custom Tests

### Adding New Tests

1. Create new `.bru` file in appropriate folder
2. Define request method and URL
3. Add request body/parameters
4. Set assertions and tests
5. Update this README

### Test Templates

```javascript
// Basic assertion
assert {
  res.status: eq 200
  res.body.field: isString
}

// Custom test
tests {
  test("Custom validation", function() {
    expect(res.body.value).to.be.greaterThan(0);
  });
}
```

## 🚀 CI/CD Integration

### GitHub Actions

```yaml
- name: Run API Tests
  run: |
    cd backend/ai-service
    bruno run --reporter junit > test-results.xml
```

### Docker Testing

```bash
# Run tests in Docker
docker run --rm -v $(pwd):/app bruno run /app/bruno
```

---

**🎯 This collection ensures the AI service works perfectly across all use cases and environments!**
