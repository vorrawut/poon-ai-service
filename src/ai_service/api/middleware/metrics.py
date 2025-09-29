"""Metrics middleware for Prometheus."""

import time
from collections.abc import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

AI_PROCESSING_COUNT = Counter(
    "ai_processing_total",
    "Total AI processing requests",
    ["model_type", "processing_method", "success"],
)

AI_PROCESSING_DURATION = Histogram(
    "ai_processing_duration_seconds",
    "AI processing duration in seconds",
    ["model_type", "processing_method"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect metrics for request/response."""
        start_time = time.time()

        # Get endpoint pattern (remove path parameters)
        endpoint = self._get_endpoint_pattern(request)

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method, endpoint=endpoint, status_code=response.status_code
        ).inc()

        REQUEST_DURATION.labels(method=request.method, endpoint=endpoint).observe(
            duration
        )

        return response

    def _get_endpoint_pattern(self, request: Request) -> str:
        """Extract endpoint pattern from request."""
        path = request.url.path

        # Common patterns for API endpoints
        if path.startswith("/api/v1/spending/"):
            if path.endswith("/entries"):
                return "/api/v1/spending/entries"
            elif "/entries/" in path:
                return "/api/v1/spending/entries/{id}"
            elif path.endswith("/process/text"):
                return "/api/v1/spending/process/text"
            elif path.endswith("/process/image"):
                return "/api/v1/spending/process/image"
            else:
                return "/api/v1/spending/*"

        return path
