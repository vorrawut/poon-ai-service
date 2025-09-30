"""Health check endpoints."""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request

from ....core.config import Settings, get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/")
async def health_check(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@router.get("/detailed")
async def detailed_health_check(
    request: Request, settings: Settings = Depends(get_settings)
) -> dict[str, Any]:
    """Detailed health check with service dependencies."""
    health_status: dict[str, Any] = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "dependencies": {},
        "features": settings.get_feature_flags(),
    }

    # Check database
    try:
        if (
            hasattr(request.app.state, "spending_repository")
            and request.app.state.spending_repository
        ):
            await request.app.state.spending_repository.count_total()
            health_status["dependencies"]["database"] = {
                "status": "healthy",
                "type": "sqlite",
            }
        else:
            health_status["dependencies"]["database"] = {
                "status": "not_initialized",
                "type": "sqlite",
            }
    except Exception as e:
        health_status["dependencies"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    # Check Llama client
    try:
        if (
            hasattr(request.app.state, "llama_client")
            and request.app.state.llama_client
        ):
            is_available = await request.app.state.llama_client.health_check()
            health_status["dependencies"]["llama"] = {
                "status": "healthy" if is_available else "unavailable",
                "model": settings.llama_model,
                "url": settings.get_ollama_url(),
            }
            if not is_available:
                health_status["status"] = "degraded"
        else:
            health_status["dependencies"]["llama"] = {"status": "disabled"}
    except Exception as e:
        health_status["dependencies"]["llama"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    # Check OCR client
    try:
        if hasattr(request.app.state, "ocr_client") and request.app.state.ocr_client:
            is_available = request.app.state.ocr_client.is_available()
            health_status["dependencies"]["ocr"] = {
                "status": "healthy" if is_available else "unavailable",
                "type": "tesseract",
            }
            if not is_available:
                health_status["status"] = "degraded"
        else:
            health_status["dependencies"]["ocr"] = {"status": "disabled"}
    except Exception as e:
        health_status["dependencies"]["ocr"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"

    return health_status


@router.get("/ready")
async def readiness_check(request: Request) -> dict[str, Any]:
    """Readiness check for Kubernetes."""
    # Check if essential services are ready
    ready = True

    # Database must be ready
    if not (
        hasattr(request.app.state, "spending_repository")
        and request.app.state.spending_repository
    ):
        ready = False

    return {"status": "ready" if ready else "not_ready", "ready": ready}


@router.get("/live")
async def liveness_check() -> dict[str, Any]:
    """Liveness check for Kubernetes."""
    return {"status": "alive"}
