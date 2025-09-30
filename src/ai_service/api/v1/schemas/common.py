"""Common API schemas and base models."""

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response model for all API endpoints."""

    status: str = Field(
        description="Response status", examples=["success", "error", "partial"]
    )
    message: str = Field(
        description="Human-readable message",
        examples=["Operation completed successfully", "Validation error occurred"],
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp in UTC"
    )


class SuccessResponse(BaseResponse):
    """Success response model."""

    status: str = Field(
        default="success", description="Always 'success' for successful operations"
    )


class ErrorResponse(BaseResponse):
    """Error response model."""

    status: str = Field(
        default="error", description="Always 'error' for failed operations"
    )
    error_code: str | None = Field(
        default=None,
        description="Machine-readable error code",
        examples=["VALIDATION_ERROR", "SERVICE_UNAVAILABLE", "NOT_FOUND"],
    )
    details: dict[str, Any] | None = Field(
        default=None, description="Additional error details and context"
    )


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of items to return",
        examples=[10, 25, 50],
    )
    offset: int = Field(
        default=0, ge=0, description="Number of items to skip", examples=[0, 10, 20]
    )


class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response model for list endpoints."""

    data: list[T] = Field(description="List of items")
    total_count: int = Field(
        description="Total number of items available", examples=[0, 42, 1337]
    )
    has_more: bool = Field(description="Whether there are more items available")
    pagination: dict[str, int] = Field(
        description="Pagination information",
        examples=[{"limit": 10, "offset": 0, "total": 42}],
    )


class IDResponse(SuccessResponse):
    """Response model for operations that return an ID."""

    id: UUID | str = Field(
        description="Generated or affected resource ID",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
