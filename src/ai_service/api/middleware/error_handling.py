"""Error handling middleware."""

from collections.abc import Callable
import traceback

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle request and catch any unhandled exceptions."""
        try:
            response = await call_next(request)
            return response

        except ValueError as e:
            # Business logic validation errors
            logger.warning(
                "Validation error",
                path=request.url.path,
                method=request.method,
                error=str(e)
            )
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Validation Error",
                    "message": str(e),
                    "type": "validation_error"
                }
            )

        except PermissionError as e:
            # Authorization errors
            logger.warning(
                "Permission denied",
                path=request.url.path,
                method=request.method,
                error=str(e)
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Permission Denied",
                    "message": str(e),
                    "type": "permission_error"
                }
            )

        except FileNotFoundError as e:
            # Resource not found errors
            logger.info(
                "Resource not found",
                path=request.url.path,
                method=request.method,
                error=str(e)
            )
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Not Found",
                    "message": str(e),
                    "type": "not_found_error"
                }
            )

        except TimeoutError as e:
            # Timeout errors (e.g., AI service timeouts)
            logger.error(
                "Request timeout",
                path=request.url.path,
                method=request.method,
                error=str(e)
            )
            return JSONResponse(
                status_code=408,
                content={
                    "error": "Request Timeout",
                    "message": "The request took too long to process",
                    "type": "timeout_error"
                }
            )

        except ConnectionError as e:
            # External service connection errors
            logger.error(
                "Service unavailable",
                path=request.url.path,
                method=request.method,
                error=str(e)
            )
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service Unavailable",
                    "message": "External service is temporarily unavailable",
                    "type": "connection_error"
                }
            )

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(
                "Unhandled exception",
                path=request.url.path,
                method=request.method,
                error=str(e),
                traceback=traceback.format_exc()
            )

            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "type": "internal_error"
                }
            )
