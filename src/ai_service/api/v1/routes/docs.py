"""Documentation and examples endpoints."""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get(
    "/examples",
    response_class=HTMLResponse,
    summary="API Usage Examples",
    description="Interactive examples and tutorials for using the Poon AI Service API",
    tags=["Documentation"],
)
async def api_examples() -> str:
    """Provide interactive API usage examples and tutorials."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Poon AI Service - API Examples</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }
            .example { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; }
            .code { background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 4px; overflow-x: auto; }
            h1 { color: #2d3748; }
            h2 { color: #4a5568; }
            .highlight { background: #fef5e7; padding: 2px 4px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🦙 Poon AI Service - API Examples</h1>

        <div class="example">
            <h2>🤖 AI Text Processing</h2>
            <p>Process natural language text into structured spending entries:</p>
            <div class="code">
curl -X POST "http://localhost:8001/api/v1/spending/process/text" \\
  -H "Content-Type: application/json" \\
  -d '{
    "text": "Bought coffee at Starbucks for 120 baht with credit card",
    "language": "en"
  }'
            </div>
        </div>

        <div class="example">
            <h2>📝 Manual Entry Creation</h2>
            <p>Create spending entries manually with structured data:</p>
            <div class="code">
curl -X POST "http://localhost:8001/api/v1/spending/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "amount": 85.50,
    "merchant": "Central World Food Court",
    "description": "Lunch with colleagues",
    "category": "Food & Dining",
    "payment_method": "Credit Card",
    "currency": "THB"
  }'
            </div>
        </div>

        <div class="example">
            <h2>📊 List Spending Entries</h2>
            <p>Retrieve all spending entries with pagination:</p>
            <div class="code">
curl -X GET "http://localhost:8001/api/v1/spending/"
            </div>
        </div>

        <div class="example">
            <h2>❤️ Health Checks</h2>
            <p>Monitor service health and dependencies:</p>
            <div class="code">
# Basic health check
curl -X GET "http://localhost:8001/api/v1/health/"

# Detailed health with dependencies
curl -X GET "http://localhost:8001/api/v1/health/detailed"
            </div>
        </div>

        <div class="example">
            <h2>🌍 Multi-language Support</h2>
            <p>Process text in different languages:</p>
            <div class="code">
# Thai language example
curl -X POST "http://localhost:8001/api/v1/spending/process/text" \\
  -H "Content-Type: application/json" \\
  -d '{
    "text": "ซื้อกาแฟที่สตาร์บัคส์ 120 บาท ด้วยบัตรเครดิต",
    "language": "th"
  }'
            </div>
        </div>

        <p><strong>💡 Tip:</strong> Use the <a href="/docs">interactive Swagger UI</a> to test these endpoints directly in your browser!</p>

        <hr>
        <p><small>🔗 <a href="/docs">Swagger UI</a> | <a href="/redoc">ReDoc</a> | <a href="/health">Health Check</a></small></p>
    </body>
    </html>
    """


@router.get(
    "/status",
    summary="API Status Dashboard",
    description="Simple status dashboard showing service information and quick links",
    tags=["Documentation"],
)
async def api_status(request: Request) -> dict[str, Any]:
    """Provide API status dashboard with service information."""
    base_url = str(request.base_url).rstrip("/")

    return {
        "service": "Poon AI Service",
        "status": "operational",
        "version": "1.0.0",
        "documentation": {
            "swagger_ui": f"{base_url}/docs",
            "redoc": f"{base_url}/redoc",
            "examples": f"{base_url}/api/v1/docs/examples",
        },
        "endpoints": {
            "health_check": f"{base_url}/api/v1/health/",
            "detailed_health": f"{base_url}/api/v1/health/detailed",
            "list_spending": f"{base_url}/api/v1/spending/",
            "create_spending": f"{base_url}/api/v1/spending/",
            "ai_text_processing": f"{base_url}/api/v1/spending/process/text",
        },
        "features": {
            "ai_processing": "✅ Local Llama 3.2 model",
            "ocr_support": "✅ Tesseract OCR integration",
            "multi_language": "✅ English, Thai, and more",
            "real_time": "✅ Fast processing (1-3 seconds)",
            "monitoring": "✅ Health checks and metrics",
        },
        "quick_start": {
            "1": "Visit /docs for interactive API documentation",
            "2": "Try the AI text processing endpoint",
            "3": "Check /api/v1/health/detailed for service status",
            "4": "View /api/v1/docs/examples for code samples",
        },
    }
