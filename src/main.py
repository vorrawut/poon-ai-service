"""
Main application entry point for Poon AI Service.

This is a Clean Architecture FastAPI microservice for AI-powered spending analysis.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from ai_service.api.middleware.error_handling import ErrorHandlingMiddleware
from ai_service.api.middleware.logging import LoggingMiddleware
from ai_service.api.middleware.metrics import MetricsMiddleware
from ai_service.api.v1.routes import api_router
from ai_service.core.config import get_settings, setup_logging
from ai_service.infrastructure.database.sqlite_repository import (
    SqliteSpendingRepository,
)
from ai_service.infrastructure.external_apis.llama_client import LlamaClient
from ai_service.infrastructure.external_apis.ocr_client import TesseractOCRClient

# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Global settings
settings = get_settings()


class ServiceRegistry:
    """Service registry for dependency injection."""

    def __init__(self) -> None:
        """Initialize service registry."""
        self.spending_repository: SqliteSpendingRepository | None = None
        self.llama_client: LlamaClient | None = None
        self.ocr_client: TesseractOCRClient | None = None

    async def initialize(self) -> None:
        """Initialize all services."""
        logger.info("🚀 Initializing AI Service components...")

        # Initialize database repository
        self.spending_repository = SqliteSpendingRepository(settings.get_database_url())
        await self.spending_repository.initialize()
        logger.info("✅ Database repository initialized")

        # Initialize Llama client if enabled
        if settings.use_llama:
            self.llama_client = LlamaClient(
                base_url=settings.get_ollama_url(),
                model=settings.llama_model,
                timeout=settings.llama_timeout,
            )

            # Test connection
            is_available = await self.llama_client.health_check()
            if is_available:
                logger.info("✅ Llama4 client initialized and connected")
            else:
                logger.warning("⚠️ Llama4 client initialized but not connected")

        # Initialize OCR client
        self.ocr_client = TesseractOCRClient(
            tesseract_path=settings.tesseract_path,
            languages=settings.tesseract_languages,
        )

        if self.ocr_client.is_available():
            logger.info("✅ OCR client initialized")
        else:
            logger.warning("⚠️ OCR client not available (Tesseract not found)")

        logger.info("🎉 All services initialized successfully")

    async def cleanup(self) -> None:
        """Cleanup all services."""
        logger.info("🧹 Cleaning up services...")

        if self.spending_repository:
            await self.spending_repository.close()
            logger.info("✅ Database repository closed")

        if self.llama_client:
            await self.llama_client.close()
            logger.info("✅ Llama client closed")

        logger.info("✅ Service cleanup completed")


# Global service registry
service_registry = ServiceRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown of services.
    """
    # Startup
    logger.info(
        "🦙 Starting Poon AI Service",
        version=settings.app_version,
        environment=settings.environment,
        debug=settings.debug,
    )

    try:
        await service_registry.initialize()

        # Store services in app state for dependency injection
        app.state.spending_repository = service_registry.spending_repository
        app.state.llama_client = service_registry.llama_client
        app.state.ocr_client = service_registry.ocr_client
        app.state.settings = settings

        logger.info("🚀 AI Service startup completed")

        yield

    except Exception as e:
        logger.error("❌ Failed to start AI Service", error=str(e))
        raise

    finally:
        # Shutdown
        logger.info("🛑 Shutting down AI Service...")
        await service_registry.cleanup()
        logger.info("✅ AI Service shutdown completed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered spending analysis microservice with local Llama4 processing",
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development() else None,
        redoc_url="/redoc" if settings.is_development() else None,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)

    if settings.enable_metrics:
        app.add_middleware(MetricsMiddleware)

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    # Add Prometheus metrics endpoint
    if settings.enable_metrics:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root() -> dict[str, Any]:
        """Root endpoint with service information."""
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "description": "AI-powered spending analysis microservice",
            "docs": "/docs" if settings.is_development() else "disabled",
            "health": "/health",
            "metrics": "/metrics" if settings.enable_metrics else "disabled",
        }

    return app


# Create the FastAPI application
app = create_app()


def main() -> None:
    """Run the application."""
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and settings.is_development(),
        log_level=settings.log_level.lower(),
        access_log=settings.is_development(),
    )


if __name__ == "__main__":
    main()
