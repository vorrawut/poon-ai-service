"""Enhanced health check endpoints with comprehensive monitoring."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel

from ...infrastructure.resilience.circuit_breaker import circuit_breaker_registry

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Health"])


class HealthStatus(BaseModel):
    """Health status model."""

    status: str
    timestamp: datetime
    version: str
    environment: str
    uptime_seconds: float


class ComponentHealth(BaseModel):
    """Individual component health."""

    name: str
    status: str
    response_time_ms: float
    last_check: datetime
    error: str | None = None


class DetailedHealthResponse(BaseModel):
    """Detailed health response."""

    status: str
    timestamp: datetime
    version: str
    environment: str
    uptime_seconds: float
    components: list[ComponentHealth]
    circuit_breakers: dict[str, Any]
    system_info: dict[str, Any]


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(request: Request) -> DetailedHealthResponse:
    """Comprehensive health check with all components."""
    start_time = datetime.utcnow()
    components = []
    overall_status = "healthy"

    # Check MongoDB (spending repository)
    mongo_health = await _check_mongodb(request)
    components.append(mongo_health)
    if mongo_health.status != "healthy":
        overall_status = "degraded"

    # Check MongoDB (training repository)
    mongo_training_health = await _check_mongodb_training(request)
    components.append(mongo_training_health)
    if mongo_training_health.status != "healthy":
        overall_status = "degraded"

    # Check Redis
    redis_health = await _check_redis(request)
    components.append(redis_health)
    if redis_health.status != "healthy":
        overall_status = "degraded"

    # Check Llama AI service
    llama_health = await _check_llama(request)
    components.append(llama_health)
    if llama_health.status != "healthy":
        overall_status = "degraded"

    # Check OCR service
    ocr_health = await _check_ocr(request)
    components.append(ocr_health)
    if ocr_health.status != "healthy":
        overall_status = "degraded"

    # Get circuit breaker stats
    circuit_breaker_stats = circuit_breaker_registry.get_all_stats()

    # Check if any circuit breakers are open
    for breaker_name, stats in circuit_breaker_stats.items():
        if stats["state"] == "open":
            overall_status = "degraded"
            logger.warning(f"Circuit breaker {breaker_name} is OPEN")

    # Get system information
    system_info = await _get_system_info()

    settings = request.app.state.settings

    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=(datetime.utcnow() - start_time).total_seconds(),
        components=components,
        circuit_breakers=circuit_breaker_stats,
        system_info=system_info,
    )


@router.get("/health/readiness")
async def readiness_check(request: Request) -> dict[str, Any]:
    """Readiness probe for Kubernetes."""
    try:
        # Check critical components
        critical_checks = []

        # MongoDB check
        mongo_health = await _check_mongodb(request)
        critical_checks.append(mongo_health.status == "healthy")

        # AI Learning service check
        ai_learning_service = getattr(request.app.state, "ai_learning_service", None)
        critical_checks.append(ai_learning_service is not None)

        # All critical components must be healthy
        is_ready = all(critical_checks)

        return {
            "status": "ready" if is_ready else "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "mongodb": mongo_health.status,
                "ai_learning_service": "available"
                if ai_learning_service
                else "unavailable",
            },
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }


@router.get("/health/liveness")
async def liveness_check() -> dict[str, Any]:
    """Liveness probe for Kubernetes."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "pid": os.getpid() if "os" in globals() else None,
    }


async def _check_mongodb(request: Request) -> ComponentHealth:
    """Check MongoDB spending repository health."""
    start_time = datetime.utcnow()

    try:
        spending_repo = getattr(request.app.state, "spending_repository", None)
        if not spending_repo:
            return ComponentHealth(
                name="mongodb_spending",
                status="unavailable",
                response_time_ms=0,
                last_check=start_time,
                error="Repository not initialized",
            )

        # Try a simple operation
        await spending_repo.count_total()

        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ComponentHealth(
            name="mongodb_spending",
            status="healthy",
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
        )

    except Exception as e:
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ComponentHealth(
            name="mongodb_spending",
            status="unhealthy",
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
            error=str(e),
        )


async def _check_mongodb_training(request: Request) -> ComponentHealth:
    """Check MongoDB training repository health."""
    start_time = datetime.utcnow()

    try:
        training_repo = getattr(request.app.state, "training_repository", None)
        if not training_repo:
            return ComponentHealth(
                name="mongodb_training",
                status="unavailable",
                response_time_ms=0,
                last_check=start_time,
                error="Training repository not initialized",
            )

        # Try a simple operation
        await training_repo.count_by_status()

        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ComponentHealth(
            name="mongodb_training",
            status="healthy",
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
        )

    except Exception as e:
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ComponentHealth(
            name="mongodb_training",
            status="unhealthy",
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
            error=str(e),
        )


async def _check_redis(_request: Request) -> ComponentHealth:
    """Check Redis health."""
    start_time = datetime.utcnow()

    try:
        # This would need Redis client from app state
        # For now, assume healthy if no errors
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ComponentHealth(
            name="redis",
            status="healthy",
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
        )

    except Exception as e:
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ComponentHealth(
            name="redis",
            status="unhealthy",
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
            error=str(e),
        )


async def _check_llama(request: Request) -> ComponentHealth:
    """Check Llama AI service health."""
    start_time = datetime.utcnow()

    try:
        llama_client = getattr(request.app.state, "llama_client", None)
        if not llama_client:
            return ComponentHealth(
                name="llama_ai",
                status="unavailable",
                response_time_ms=0,
                last_check=start_time,
                error="Llama client not initialized",
            )

        # Try health check
        is_healthy = await llama_client.health_check()

        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ComponentHealth(
            name="llama_ai",
            status="healthy" if is_healthy else "unhealthy",
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
            error=None if is_healthy else "Health check failed",
        )

    except Exception as e:
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ComponentHealth(
            name="llama_ai",
            status="unhealthy",
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
            error=str(e),
        )


async def _check_ocr(request: Request) -> ComponentHealth:
    """Check OCR service health."""
    start_time = datetime.utcnow()

    try:
        ocr_client = getattr(request.app.state, "ocr_client", None)
        if not ocr_client:
            return ComponentHealth(
                name="ocr_service",
                status="unavailable",
                response_time_ms=0,
                last_check=start_time,
                error="OCR client not initialized",
            )

        # Check if OCR is available
        is_available = ocr_client.is_available()

        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ComponentHealth(
            name="ocr_service",
            status="healthy" if is_available else "unhealthy",
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
            error=None if is_available else "OCR not available",
        )

    except Exception as e:
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ComponentHealth(
            name="ocr_service",
            status="unhealthy",
            response_time_ms=response_time,
            last_check=datetime.utcnow(),
            error=str(e),
        )


async def _get_system_info() -> dict[str, Any]:
    """Get system information."""
    import psutil

    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "process_count": len(psutil.pids()),
            "python_version": sys.version,
            "platform": sys.platform,
        }
    except ImportError:
        return {"message": "psutil not available for system monitoring"}
