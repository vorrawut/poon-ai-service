#!/bin/bash

# Test script for Docker deployment
set -e

echo "🧪 Testing Poon AI Service Docker Deployment..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Test 1: Health Check
print_test "Testing health endpoint..."
if curl -s -f http://localhost:8001/health | grep -q "healthy"; then
    print_pass "Health check endpoint working"
else
    print_fail "Health check endpoint failed"
    exit 1
fi

# Test 2: Detailed Health Check
print_test "Testing detailed health endpoint..."
if curl -s -f http://localhost:8001/api/v1/health/detailed | grep -q "dependencies"; then
    print_pass "Detailed health check working"
else
    print_fail "Detailed health check failed"
    exit 1
fi

# Test 3: Spending Entries
print_test "Testing spending entries endpoint..."
if curl -s -f http://localhost:8001/api/v1/spending/ | grep -q "entries"; then
    print_pass "Spending entries endpoint working"
else
    print_fail "Spending entries endpoint failed"
    exit 1
fi

# Test 4: Create Spending Entry
print_test "Testing create spending entry..."
response=$(curl -s -X POST http://localhost:8001/api/v1/spending/ \
    -H "Content-Type: application/json" \
    -d '{
        "amount": 99.99,
        "merchant": "Test Merchant",
        "description": "Docker test entry",
        "category": "Testing",
        "payment_method": "Credit Card"
    }')

if echo "$response" | grep -q "success"; then
    print_pass "Create spending entry working"
    entry_id=$(echo "$response" | jq -r '.entry_id')
    echo "  Created entry ID: $entry_id"
else
    print_fail "Create spending entry failed"
    echo "  Response: $response"
    exit 1
fi

# Test 5: Text Processing (may take longer)
print_test "Testing AI text processing..."
response=$(curl -s -X POST http://localhost:8001/api/v1/spending/process/text \
    -H "Content-Type: application/json" \
    -d '{
        "text": "Bought coffee at Starbucks for 120 baht with credit card",
        "language": "en"
    }')

if echo "$response" | grep -q "success"; then
    print_pass "AI text processing working"
    confidence=$(echo "$response" | jq -r '.confidence')
    merchant=$(echo "$response" | jq -r '.parsed_data.merchant')
    amount=$(echo "$response" | jq -r '.parsed_data.amount')
    echo "  Parsed: $merchant, $amount baht (confidence: $confidence)"
else
    print_fail "AI text processing failed (this may be normal if Ollama is still initializing)"
    echo "  Response: $response"
fi

# Test 6: Thai Text Processing
print_test "Testing Thai text processing..."
response=$(curl -s -X POST http://localhost:8001/api/v1/spending/process/text \
    -H "Content-Type: application/json" \
    -d '{
        "text": "ซื้อกาแฟที่สตาร์บัคส์ 150 บาท จ่ายด้วยบัตรเครดิต",
        "language": "th"
    }')

if echo "$response" | grep -q "success"; then
    print_pass "Thai text processing working"
    merchant=$(echo "$response" | jq -r '.parsed_data.merchant')
    amount=$(echo "$response" | jq -r '.parsed_data.amount')
    echo "  Parsed Thai: $merchant, $amount baht"
else
    print_fail "Thai text processing failed (this may be normal if Ollama is still initializing)"
fi

# Test 7: Service Dependencies
print_test "Testing service dependencies..."

# Check Ollama
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_pass "Ollama service accessible"
else
    print_fail "Ollama service not accessible"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_pass "Redis service accessible"
else
    print_fail "Redis service not accessible"
fi

# Test 8: API Documentation
print_test "Testing API documentation..."
if curl -s -f http://localhost:8001/docs | grep -q "FastAPI"; then
    print_pass "API documentation accessible"
else
    print_fail "API documentation not accessible"
fi

# Test 9: Metrics Endpoint
print_test "Testing metrics endpoint..."
if curl -s -f http://localhost:8001/metrics | grep -q "http_requests"; then
    print_pass "Metrics endpoint working"
else
    print_fail "Metrics endpoint not working"
fi

echo ""
echo "🎉 Docker deployment test completed!"
echo ""
echo "📊 Service URLs:"
echo "  • AI Service:    http://localhost:8001"
echo "  • API Docs:      http://localhost:8001/docs"
echo "  • Health Check:  http://localhost:8001/health"
echo "  • Metrics:       http://localhost:8001/metrics"
echo "  • Ollama:        http://localhost:11434"
echo ""
echo "✅ All core services are working correctly!"
echo "🧪 Ready for Bruno API testing!"
