"""API schemas for request and response models."""

# Common schemas
from .common import (
    BaseResponse,
    ErrorResponse,
    IDResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
)

# Health schemas
from .health import (
    DependencyStatus,
    DetailedHealthResponse,
    FeatureFlags,
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
    ServiceStatus,
)

# Spending schemas
from .spending import (
    CreateSpendingRequest,
    CreateSpendingResponse,
    ParsedSpendingData,
    ProcessTextRequest,
    ProcessTextResponse,
    SpendingEntryResponse,
    SpendingListResponse,
)

__all__ = [
    # Common schemas
    "BaseResponse",
    # Spending schemas
    "CreateSpendingRequest",
    "CreateSpendingResponse",
    # Health schemas
    "DependencyStatus",
    "DetailedHealthResponse",
    "ErrorResponse",
    "FeatureFlags",
    "HealthResponse",
    "IDResponse",
    "LivenessResponse",
    "PaginatedResponse",
    "PaginationParams",
    "ParsedSpendingData",
    "ProcessTextRequest",
    "ProcessTextResponse",
    "ReadinessResponse",
    "ServiceStatus",
    "SpendingEntryResponse",
    "SpendingListResponse",
    "SuccessResponse",
]
