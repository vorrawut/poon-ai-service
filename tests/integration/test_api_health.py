"""Integration tests for health API endpoints."""

# We'll import the app directly for testing
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.mark.integration
class TestHealthAPI:
    """Test health check API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        app = create_app()
        return TestClient(app)

    def test_basic_health_check(self, client):
        """Test the basic health check endpoint."""
        response = client.get("/api/v1/health/")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "service" in data
        assert "version" in data
        assert "environment" in data

        # Basic health check doesn't include timestamp

    def test_detailed_health_check(self, client):
        """Test the detailed health check endpoint."""
        response = client.get("/api/v1/health/detailed")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "environment" in data
        assert "dependencies" in data
        assert "features" in data

        # Check dependencies structure
        dependencies = data["dependencies"]
        assert "database" in dependencies
        assert "llama" in dependencies

        # Check features structure
        features = data["features"]
        assert isinstance(features, dict)
        assert "ai_enhancement" in features
        assert "batch_processing" in features
        assert "ocr_processing" in features
        assert "metrics_enabled" in features

    def test_readiness_check(self, client):
        """Test the readiness check endpoint."""
        response = client.get("/api/v1/health/ready")

        # Should return 200 or 503 depending on service state
        assert response.status_code in [200, 503]

        data = response.json()
        assert "ready" in data
        assert "status" in data

        # Status should be "ready" or "not_ready"
        assert data["status"] in ["ready", "not_ready"]

    def test_liveness_check(self, client):
        """Test the liveness check endpoint."""
        response = client.get("/api/v1/health/live")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "alive"
