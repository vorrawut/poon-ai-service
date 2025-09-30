"""Unit tests for error handling middleware."""

import pytest
from fastapi import Response
from fastapi.responses import JSONResponse

from ai_service.api.middleware.error_handling import ErrorHandlingMiddleware


class MockRequest:
    """Mock request for testing."""

    def __init__(self, path="/test", method="GET"):
        self.url = MockURL(path)
        self.method = method


class MockURL:
    """Mock URL for testing."""

    def __init__(self, path):
        self.path = path


class TestErrorHandlingMiddleware:
    """Test ErrorHandlingMiddleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return ErrorHandlingMiddleware(app=None)

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        return MockRequest()

    @pytest.mark.asyncio
    async def test_successful_request(self, middleware, mock_request):
        """Test middleware with successful request."""

        async def call_next(_request):
            return Response(content="Success", status_code=200)

        response = await middleware.dispatch(mock_request, call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_value_error_handling(self, middleware, mock_request):
        """Test handling of ValueError."""

        async def call_next(_request):
            raise ValueError("Invalid input data")

        response = await middleware.dispatch(mock_request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        # Check response content
        import json

        content = json.loads(response.body.decode())
        assert content["error"] == "Validation Error"
        assert content["message"] == "Invalid input data"
        assert content["type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_permission_error_handling(self, middleware, mock_request):
        """Test handling of PermissionError."""

        async def call_next(_request):
            raise PermissionError("Access denied")

        response = await middleware.dispatch(mock_request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 403
        # Check response content
        import json

        content = json.loads(response.body.decode())
        assert content["error"] == "Permission Denied"
        assert content["message"] == "Access denied"
        assert content["type"] == "permission_error"

    @pytest.mark.asyncio
    async def test_file_not_found_error_handling(self, middleware, mock_request):
        """Test handling of FileNotFoundError."""

        async def call_next(_request):
            raise FileNotFoundError("File not found")

        response = await middleware.dispatch(mock_request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        # Check response content
        import json

        content = json.loads(response.body.decode())
        assert content["error"] == "Not Found"
        assert content["message"] == "File not found"
        assert content["type"] == "not_found_error"

    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, middleware, mock_request):
        """Test handling of TimeoutError."""

        async def call_next(_request):
            raise TimeoutError("Request timeout")

        response = await middleware.dispatch(mock_request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 408
        # Check response content
        import json

        content = json.loads(response.body.decode())
        assert content["error"] == "Request Timeout"
        assert "request took too long" in content["message"].lower()
        assert content["type"] == "timeout_error"

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, middleware, mock_request):
        """Test handling of ConnectionError."""

        async def call_next(_request):
            raise ConnectionError("Connection failed")

        response = await middleware.dispatch(mock_request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 503
        # Check response content
        import json

        content = json.loads(response.body.decode())
        assert content["error"] == "Service Unavailable"
        assert "service" in content["message"].lower()
        assert "unavailable" in content["message"].lower()
        assert content["type"] == "connection_error"

    @pytest.mark.asyncio
    async def test_generic_exception_handling(self, middleware, mock_request):
        """Test handling of generic exceptions."""

        async def call_next(_request):
            raise RuntimeError("Unexpected error")

        response = await middleware.dispatch(mock_request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        # Check response content
        import json

        content = json.loads(response.body.decode())
        assert content["error"] == "Internal Server Error"
        assert "An unexpected error occurred" in content["message"]
        assert content["type"] == "internal_error"

    @pytest.mark.asyncio
    async def test_different_request_methods(self, middleware):
        """Test middleware with different HTTP methods."""
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

        for method in methods:
            mock_request = MockRequest(method=method)

            async def call_next(_request):
                raise ValueError("Test error")

            response = await middleware.dispatch(mock_request, call_next)
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_different_request_paths(self, middleware):
        """Test middleware with different request paths."""
        paths = ["/api/v1/spending", "/health", "/metrics", "/docs"]

        for path in paths:
            mock_request = MockRequest(path=path)

            async def call_next(_request):
                raise ValueError("Test error")

            response = await middleware.dispatch(mock_request, call_next)
            assert response.status_code == 400
