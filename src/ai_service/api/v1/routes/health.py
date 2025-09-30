"""Health check endpoints."""

import structlog
from fastapi import APIRouter, Depends, Request, status

from ....core.config import Settings, get_settings
from ..schemas.health import (
    DependencyStatus,
    DetailedHealthResponse,
    FeatureFlags,
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
    ServiceStatus,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic Health Check",
    description="""
    **Basic health check endpoint** for monitoring service availability.

    This endpoint provides essential service information and confirms the service is running.
    It's designed for simple uptime monitoring and load balancer health checks.

    **Use Cases:**
    - Load balancer health checks
    - Simple monitoring systems
    - Quick service status verification

    **Response includes:**
    - Service status (always "healthy" if responding)
    - Service name and version
    - Current deployment environment
    """,
    responses={
        200: {
            "description": "Service is healthy and operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Service is healthy",
                        "timestamp": "2024-01-15T12:35:00Z",
                        "service": "Poon AI Service",
                        "version": "1.0.0",
                        "environment": "production",
                    }
                }
            },
        }
    },
    tags=["Health"],
)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Basic health check endpoint for monitoring service availability."""
    return HealthResponse(
        status="success",
        message="Service is healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get(
    "/detailed",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed Health Check",
    description="""
    **Comprehensive health check** with dependency status and feature availability.

    This endpoint provides detailed information about all service dependencies,
    feature flags, and system capabilities. It's designed for comprehensive
    monitoring and troubleshooting.

    **Dependency Checks:**
    - **Database**: SQLite connection and query capability
    - **Llama AI**: Ollama service availability and model status
    - **OCR**: Tesseract availability and language support

    **Feature Flags:**
    - AI enhancement capabilities
    - Batch processing availability
    - OCR processing status
    - Metrics collection status

    **Status Levels:**
    - `healthy`: All systems operational
    - `degraded`: Some non-critical services unavailable
    - `unhealthy`: Critical services failing
    """,
    responses={
        200: {
            "description": "Detailed health status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Detailed health check completed",
                        "timestamp": "2024-01-15T12:35:00Z",
                        "service": "Poon AI Service",
                        "version": "1.0.0",
                        "environment": "production",
                        "dependencies": {
                            "database": {"status": "healthy", "type": "sqlite"},
                            "llama": {
                                "status": "healthy",
                                "model": "llama3.2:3b",
                                "url": "http://localhost:11434",
                            },
                            "ocr": {"status": "healthy", "type": "tesseract"},
                        },
                        "features": {
                            "ai_enhancement": True,
                            "batch_processing": True,
                            "ocr_processing": True,
                            "metrics_enabled": True,
                        },
                    }
                }
            },
        },
        503: {
            "description": "Service degraded - some dependencies unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "message": "Some services are unavailable",
                        "dependencies": {
                            "database": {"status": "healthy", "type": "sqlite"},
                            "llama": {
                                "status": "unavailable",
                                "error": "Connection refused",
                            },
                            "ocr": {"status": "healthy", "type": "tesseract"},
                        },
                    }
                }
            },
        },
    },
    tags=["Health"],
)
async def detailed_health_check(
    request: Request, settings: Settings = Depends(get_settings)
) -> DetailedHealthResponse:
    """Comprehensive health check with dependency status and feature availability."""
    overall_status = "healthy"

    # Initialize dependency statuses
    db_status = ServiceStatus(status="unknown")
    llama_status = ServiceStatus(status="unknown")
    ocr_status = ServiceStatus(status="unknown")

    # Check database
    try:
        if (
            hasattr(request.app.state, "spending_repository")
            and request.app.state.spending_repository
        ):
            await request.app.state.spending_repository.count_total()
            db_status = ServiceStatus(status="healthy", type="sqlite")
        else:
            db_status = ServiceStatus(status="not_initialized", type="sqlite")
    except Exception as e:
        db_status = ServiceStatus(status="unhealthy", type="sqlite", error=str(e))
        overall_status = "degraded"

    # Check Llama client
    try:
        if (
            hasattr(request.app.state, "llama_client")
            and request.app.state.llama_client
        ):
            is_available = await request.app.state.llama_client.health_check()
            llama_status = ServiceStatus(
                status="healthy" if is_available else "unavailable",
                type="llama3.2",
                model=settings.llama_model,
                url=settings.get_ollama_url(),
            )
            if not is_available:
                overall_status = "degraded"
        else:
            llama_status = ServiceStatus(status="disabled")
    except Exception as e:
        llama_status = ServiceStatus(status="unhealthy", error=str(e))
        overall_status = "degraded"

    # Check OCR client
    try:
        if hasattr(request.app.state, "ocr_client") and request.app.state.ocr_client:
            is_available = request.app.state.ocr_client.is_available()
            ocr_status = ServiceStatus(
                status="healthy" if is_available else "unavailable",
                type="tesseract",
            )
            if not is_available:
                overall_status = "degraded"
        else:
            ocr_status = ServiceStatus(status="disabled")
    except Exception as e:
        ocr_status = ServiceStatus(status="unhealthy", error=str(e))
        overall_status = "degraded"

    # Create dependency status
    dependencies = DependencyStatus(
        database=db_status, llama=llama_status, ocr=ocr_status
    )

    # Get feature flags
    features = FeatureFlags(
        ai_enhancement=settings.use_llama,
        batch_processing=True,  # Always available
        ocr_processing=ocr_status.status in ["healthy", "unavailable"],
        metrics_enabled=settings.enable_metrics,
    )

    return DetailedHealthResponse(
        status=overall_status,
        message="Detailed health check completed",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        dependencies=dependencies,
        features=features,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="""
    **Kubernetes readiness probe** endpoint.

    This endpoint checks if the service is ready to accept traffic.
    It verifies that essential services (like the database) are initialized
    and the service can handle requests.

    **Readiness Criteria:**
    - Database repository is initialized
    - Core services are available

    **Usage:**
    - Kubernetes readiness probes
    - Load balancer health checks
    - Deployment verification
    """,
    responses={
        200: {
            "description": "Service is ready to accept traffic",
            "content": {
                "application/json": {"example": {"status": "ready", "ready": True}}
            },
        },
        503: {
            "description": "Service is not ready",
            "content": {
                "application/json": {"example": {"status": "not_ready", "ready": False}}
            },
        },
    },
    tags=["Health"],
)
async def readiness_check(request: Request) -> ReadinessResponse:
    """Kubernetes readiness probe - checks if service is ready to accept traffic."""
    # Check if essential services are ready
    ready = True

    # Database must be ready
    if not (
        hasattr(request.app.state, "spending_repository")
        and request.app.state.spending_repository
    ):
        ready = False

    return ReadinessResponse(status="ready" if ready else "not_ready", ready=ready)


@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness Check",
    description="""
    **Kubernetes liveness probe** endpoint.

    This endpoint confirms the service process is alive and responding.
    If this endpoint fails to respond, it indicates the service should be restarted.

    **Purpose:**
    - Kubernetes liveness probes
    - Process monitoring
    - Restart triggers for unhealthy services

    **Response:**
    - Always returns "alive" if the service is responding
    - Non-response indicates service failure
    """,
    responses={
        200: {
            "description": "Service is alive and responding",
            "content": {"application/json": {"example": {"status": "alive"}}},
        }
    },
    tags=["Health"],
)
async def liveness_check() -> LivenessResponse:
    """Kubernetes liveness probe - confirms service process is alive."""
    return LivenessResponse(status="alive")
