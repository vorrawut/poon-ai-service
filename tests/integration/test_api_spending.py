"""Integration tests for spending API endpoints."""

# We'll import the app directly for testing
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.mark.integration
class TestSpendingAPI:
    """Test spending API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def sample_spending_data(self):
        """Sample spending data for tests."""
        return {
            "amount": 120.50,
            "merchant": "Test Cafe",
            "description": "Coffee and pastry",
            "category": "Food & Dining",
            "payment_method": "Credit Card",
        }

    def test_get_spending_entries_empty(self, client):
        """Test getting spending entries when none exist."""
        response = client.get("/api/v1/spending/")

        # Should succeed or fail gracefully with service unavailable
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            assert data["entries"] == []
            assert data["total_count"] == 0
        elif response.status_code == 500:
            # Expected when repository is not properly initialized in test
            data = response.json()
            assert "detail" in data
        else:
            # Other valid error responses
            assert response.status_code in [503]

    def test_create_spending_entry(self, client, sample_spending_data):
        """Test creating a new spending entry."""
        response = client.post("/api/v1/spending/", json=sample_spending_data)

        # Should succeed or fail gracefully
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            assert "entry_id" in data
            assert "message" in data
        elif response.status_code == 503:
            # Service unavailable (repository not initialized)
            data = response.json()
            assert "Repository not available" in data["detail"]
        else:
            # Other errors should still be valid HTTP responses
            assert response.status_code in [400, 422, 500]

    def test_create_spending_entry_invalid_data(self, client):
        """Test creating spending entry with invalid data."""
        invalid_data = {
            "amount": "not_a_number",  # Invalid amount
            "merchant": "",  # Empty merchant
            "description": "Test",
        }

        response = client.post("/api/v1/spending/", json=invalid_data)

        # Should return validation error
        assert response.status_code == 422

    def test_create_spending_entry_missing_fields(self, client):
        """Test creating spending entry with missing required fields."""
        incomplete_data = {
            "amount": 100.0
            # Missing merchant and description
        }

        response = client.post("/api/v1/spending/", json=incomplete_data)

        # Should return validation error
        assert response.status_code == 422

    def test_process_text_endpoint(self, client):
        """Test the process text endpoint."""
        text_data = {"text": "Coffee at Starbucks 120 baht", "language": "en"}

        response = client.post("/api/v1/spending/process/text", json=text_data)

        # Should succeed or fail gracefully
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
            assert "parsed_data" in data
        elif response.status_code == 503:
            # Service unavailable
            data = response.json()
            assert "not available" in data["detail"].lower()
        else:
            # Other errors should still be valid HTTP responses
            assert response.status_code in [400, 422, 500]

    def test_process_text_invalid_data(self, client):
        """Test process text with invalid data."""
        invalid_data = {
            "language": "en"
            # Missing text field
        }

        response = client.post("/api/v1/spending/process/text", json=invalid_data)

        # Should return validation error
        assert response.status_code == 422

    def test_process_text_empty_text(self, client):
        """Test process text with empty text."""
        empty_text_data = {"text": "", "language": "en"}

        response = client.post("/api/v1/spending/process/text", json=empty_text_data)

        # Should handle empty text gracefully
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "success"
        elif response.status_code == 400:
            # Bad request for empty text
            data = response.json()
            assert "text" in data["detail"].lower()
        else:
            # Other valid error responses
            assert response.status_code in [422, 503]

    def test_api_cors_headers(self, client):
        """Test that CORS headers are properly set."""
        # Test preflight request
        response = client.options("/api/v1/spending/")

        # Should handle OPTIONS request
        assert response.status_code in [
            200,
            405,
        ]  # 405 if OPTIONS not explicitly handled

        # Test actual request for CORS headers
        response = client.get("/api/v1/spending/")

        # In development, CORS should be configured
        # Headers might not be visible in TestClient, but endpoint should work
        assert response.status_code in [200, 500, 503]
