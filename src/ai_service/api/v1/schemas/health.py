"""Health check API schemas."""

from pydantic import BaseModel, Field

from .common import BaseResponse


class ServiceStatus(BaseModel):
    """Service status information."""

    status: str = Field(
        description="Service status",
        examples=["healthy", "unhealthy", "degraded", "unavailable"],
    )
    type: str | None = Field(
        default=None,
        description="Service type or implementation",
        examples=["sqlite", "tesseract", "llama3.2"],
    )
    url: str | None = Field(
        default=None,
        description="Service URL if applicable",
        examples=["http://localhost:11434"],
    )
    model: str | None = Field(
        default=None,
        description="AI model name if applicable",
        examples=["llama3.2:3b"],
    )
    error: str | None = Field(
        default=None, description="Error message if service is unhealthy"
    )


class DependencyStatus(BaseModel):
    """Dependency status for detailed health checks."""

    database: ServiceStatus = Field(description="Database service status")
    llama: ServiceStatus = Field(description="Llama AI service status")
    ocr: ServiceStatus = Field(description="OCR service status")


class FeatureFlags(BaseModel):
    """Feature flags and capabilities."""

    ai_enhancement: bool = Field(
        description="Whether AI text enhancement is enabled", examples=[True, False]
    )
    batch_processing: bool = Field(
        description="Whether batch processing is available", examples=[True, False]
    )
    ocr_processing: bool = Field(
        description="Whether OCR processing is available", examples=[True, False]
    )
    metrics_enabled: bool = Field(
        description="Whether metrics collection is enabled", examples=[True, False]
    )


class HealthResponse(BaseResponse):
    """Basic health check response."""

    service: str = Field(description="Service name", examples=["Poon AI Service"])
    version: str = Field(
        description="Service version", examples=["1.0.0", "2.1.3-beta"]
    )
    environment: str = Field(
        description="Deployment environment",
        examples=["development", "staging", "production"],
    )


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response with dependencies."""

    dependencies: DependencyStatus = Field(
        description="Status of all service dependencies"
    )
    features: FeatureFlags = Field(description="Available features and capabilities")


class ReadinessResponse(BaseModel):
    """Readiness check response for Kubernetes."""

    status: str = Field(description="Readiness status", examples=["ready", "not_ready"])
    ready: bool = Field(description="Whether the service is ready to accept traffic")


class LivenessResponse(BaseModel):
    """Liveness check response for Kubernetes."""

    status: str = Field(
        default="alive", description="Liveness status - always 'alive' if responding"
    )
