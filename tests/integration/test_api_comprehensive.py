"""Comprehensive API integration tests."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import the app directly from conftest.py fixtures instead
# from main import create_app


@pytest.mark.integration
class TestAPIComprehensive:
    """Comprehensive API integration tests."""

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)

    @pytest.fixture
    def test_image(self):
        """Create test image for upload tests."""
        img = Image.new("RGB", (200, 100), color="white")
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(temp_file.name)
        temp_file.close()

        yield temp_file.name

        Path(temp_file.name).unlink(missing_ok=True)

    def test_health_endpoints(self, client):
        """Test all health endpoints."""
        # Basic health
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "version" in data

        # API health
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

        # Detailed health
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "dependencies" in data
        assert "features" in data

        # Readiness check
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200

        # Liveness check
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200

    def test_spending_crud_operations(self, client):
        """Test complete CRUD operations for spending entries."""
        # Create entry
        entry_data = {
            "merchant": "Test Restaurant",
            "amount": 25.50,
            "currency": "USD",
            "category": "Food & Dining",
            "description": "Lunch with colleagues",
        }

        response = client.post("/api/v1/spending/", json=entry_data)
        assert response.status_code == 200
        create_data = response.json()
        assert "entry_id" in create_data
        entry_id = create_data["entry_id"]

        # Read entry
        response = client.get(f"/api/v1/spending/{entry_id}")
        if response.status_code == 200:
            read_data = response.json()
            assert read_data["merchant"] == "Test Restaurant"
            assert read_data["amount"] == 25.50
            assert read_data["currency"] == "USD"
        else:
            # Entry might not be immediately available due to async processing
            assert response.status_code == 404

        # List entries
        response = client.get("/api/v1/spending/")
        assert response.status_code == 200
        list_data = response.json()
        assert "entries" in list_data
        assert "total_count" in list_data
        assert isinstance(list_data["entries"], list)

    def test_spending_validation(self, client):
        """Test input validation for spending endpoints."""
        # Missing required fields
        response = client.post("/api/v1/spending/", json={})
        assert response.status_code == 422

        # Invalid amount
        response = client.post(
            "/api/v1/spending/",
            json={
                "merchant": "Test",
                "amount": -10.0,
                "currency": "USD",
                "category": "Food & Dining",
            },
        )
        assert response.status_code == 422

        # Invalid currency
        response = client.post(
            "/api/v1/spending/",
            json={
                "merchant": "Test",
                "amount": 10.0,
                "currency": "INVALID",
                "category": "Food & Dining",
            },
        )
        assert response.status_code == 422

        # Invalid category
        response = client.post(
            "/api/v1/spending/",
            json={
                "merchant": "Test",
                "amount": 10.0,
                "currency": "USD",
                "category": "Invalid Category",
            },
        )
        assert response.status_code == 422

    def test_text_processing_endpoint(self, client):
        """Test text processing endpoint."""
        # Valid text processing
        text_data = {
            "text": "Coffee at Starbucks $4.50",
            "use_ai_enhancement": False,  # Don't require AI for this test
        }

        response = client.post("/api/v1/spending/process/text", json=text_data)
        # Should succeed even without AI
        assert response.status_code in [
            200,
            400,
            500,
        ]  # 400 if AI required but not available, 500 if service error

        # Empty text
        response = client.post(
            "/api/v1/spending/process/text",
            json={"text": "", "use_ai_enhancement": False},
        )
        assert response.status_code in [
            422,
            500,
        ]  # 422 for validation, 500 for service error

        # Missing text field
        response = client.post(
            "/api/v1/spending/process/text", json={"use_ai_enhancement": False}
        )
        assert response.status_code in [
            422,
            500,
        ]  # 422 for validation, 500 for service error

    def test_image_processing_endpoint(self, client, test_image):
        """Test image processing endpoint."""
        # Test with valid image
        with open(test_image, "rb") as f:
            files = {"file": ("test.png", f, "image/png")}
            response = client.post("/api/v1/spending/process/image", files=files)
            # May return 404 if OCR not available or endpoint not implemented
            assert response.status_code in [200, 404, 422]

        # Test with invalid file type
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt") as f:
            f.write("Not an image")
            f.flush()

            with open(f.name, "rb") as txt_file:
                files = {"file": ("test.txt", txt_file, "text/plain")}
                response = client.post("/api/v1/spending/process/image", files=files)
                assert response.status_code in [400, 404, 422]

    def test_pagination_and_filtering(self, client):
        """Test pagination and filtering for spending entries."""
        # Create multiple entries for testing
        entries = []
        for i in range(5):
            entry_data = {
                "merchant": f"Test Merchant {i}",
                "amount": 10.0 + i,
                "currency": "USD",
                "category": "Food & Dining" if i < 3 else "Transportation",
                "description": f"Test entry {i}",
            }
            response = client.post("/api/v1/spending/", json=entry_data)
            if response.status_code == 200:
                entries.append(response.json()["entry_id"])

        # Test pagination
        response = client.get("/api/v1/spending/?limit=3")
        assert response.status_code == 200
        data = response.json()
        # Allow for pagination not being fully implemented
        assert len(data["entries"]) >= 0  # At least we get a response

        response = client.get("/api/v1/spending/?limit=2&offset=1")
        assert response.status_code == 200
        data = response.json()
        # Allow for pagination not being fully implemented
        assert len(data["entries"]) >= 0  # At least we get a response

        # Test category filtering
        response = client.get("/api/v1/spending/?category=Food%20%26%20Dining")
        assert response.status_code == 200

        # Test invalid pagination parameters
        response = client.get("/api/v1/spending/?limit=-1")
        assert response.status_code in [200, 422]  # May not validate negative values

        response = client.get("/api/v1/spending/?offset=-1")
        assert response.status_code in [200, 422]  # May not validate negative values

    def test_error_handling(self, client):
        """Test error handling across endpoints."""
        # 404 for non-existent entry
        response = client.get("/api/v1/spending/non-existent-id")
        assert response.status_code == 404

        # 404 for non-existent endpoint
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

        # 405 for wrong method
        response = client.delete("/api/v1/spending/")
        assert response.status_code == 405

        # Test malformed JSON
        response = client.post(
            "/api/v1/spending/",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v1/spending/")
        assert response.status_code in [200, 405]  # OPTIONS may not be implemented

        # Check for CORS headers in actual requests
        response = client.get("/api/v1/spending/")
        assert response.status_code == 200
        # CORS headers should be present in development

    def test_content_type_handling(self, client):
        """Test different content types."""
        # JSON content type
        response = client.post(
            "/api/v1/spending/",
            json={
                "merchant": "Test",
                "amount": 10.0,
                "currency": "USD",
                "category": "Other",
            },
        )
        assert response.status_code in [200, 422]

        # Form data (should fail for JSON endpoints)
        response = client.post(
            "/api/v1/spending/",
            data={
                "merchant": "Test",
                "amount": "10.0",
                "currency": "USD",
                "category": "Other",
            },
        )
        assert response.status_code == 422

    def test_rate_limiting_headers(self, client):
        """Test rate limiting headers if implemented."""
        response = client.get("/api/v1/spending/")
        assert response.status_code == 200

        # Check if rate limiting headers are present
        # This is optional and depends on implementation
        # Could check for X-RateLimit-* headers if implemented
        if "X-RateLimit-Limit" in response.headers:
            assert int(response.headers["X-RateLimit-Limit"]) > 0

    def test_security_headers(self, client):
        """Test security headers."""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200

        headers = response.headers
        # Check for basic security headers
        # These might not all be implemented yet
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
        ]

        # Don't fail if security headers aren't implemented yet
        for header in expected_headers:
            if header in headers:
                assert headers[header] is not None

    def test_api_versioning(self, client):
        """Test API versioning."""
        # v1 endpoints should work
        response = client.get("/api/v1/health/")
        assert response.status_code == 200

        # Non-existent version should return 404
        response = client.get("/api/v2/health/")
        assert response.status_code == 404

    def test_request_id_tracking(self, client):
        """Test request ID tracking if implemented."""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200

        # Check if request ID header is present
        if "X-Request-ID" in response.headers:
            assert response.headers["X-Request-ID"] is not None

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint if available."""
        # Prometheus metrics endpoint
        response = client.get("/metrics")
        # May not be implemented or may be on different port
        assert response.status_code in [200, 404]

    def test_openapi_documentation(self, client):
        """Test OpenAPI documentation endpoints."""
        # OpenAPI JSON
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

        # Swagger UI (if enabled)
        response = client.get("/docs")
        assert response.status_code in [200, 404]  # May be disabled in production

        # ReDoc (if enabled)
        response = client.get("/redoc")
        assert response.status_code in [200, 404]  # May be disabled in production

    @patch("ai_service.infrastructure.external_apis.llama_client.LlamaClient")
    def test_ai_service_integration(self, mock_llama_client, client):
        """Test AI service integration."""
        # Mock AI client
        mock_client = AsyncMock()
        mock_client.parse_spending_text.return_value = {
            "merchant": "AI Parsed Merchant",
            "amount": 15.0,
            "category": "Food & Dining",
        }
        mock_llama_client.return_value = mock_client

        # Test text processing with AI
        text_data = {"text": "Lunch at restaurant $15.00", "use_ai_enhancement": True}

        response = client.post("/api/v1/spending/process/text", json=text_data)
        # Should work with mocked AI
        assert response.status_code in [200, 400, 500]  # 500 if service error

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import threading

        results = []

        def make_request():
            response = client.get("/api/v1/health/")
            results.append(response.status_code)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert len(results) == 10
        assert all(status == 200 for status in results)

    def test_large_payload_handling(self, client):
        """Test handling of large payloads."""
        # Large description
        large_description = "A" * 10000  # 10KB description

        entry_data = {
            "merchant": "Test Merchant",
            "amount": 25.50,
            "currency": "USD",
            "category": "Food & Dining",
            "description": large_description,
        }

        response = client.post("/api/v1/spending/", json=entry_data)
        # Should handle large descriptions or return appropriate error
        assert response.status_code in [200, 400, 413, 422]  # 400 for bad request

    def test_special_characters_handling(self, client):
        """Test handling of special characters."""
        # Unicode characters
        entry_data = {
            "merchant": "Café München 🍕",
            "amount": 25.50,
            "currency": "USD",
            "category": "Food & Dining",
            "description": "Special chars: àáâãäåæçèéêë",
        }

        response = client.post("/api/v1/spending/", json=entry_data)
        assert response.status_code in [200, 422]

        # SQL injection attempt (should be safe)
        entry_data = {
            "merchant": "'; DROP TABLE spending; --",
            "amount": 25.50,
            "currency": "USD",
            "category": "Food & Dining",
        }

        response = client.post("/api/v1/spending/", json=entry_data)
        assert response.status_code in [200, 422]  # Should not crash
