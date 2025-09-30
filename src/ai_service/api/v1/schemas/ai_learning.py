"""Schemas for AI learning endpoints."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .common import BaseResponse


class FeedbackTypeEnum(str, Enum):
    """Type of feedback provided."""

    USER_CORRECTION = "user_correction"
    ADMIN_VALIDATION = "admin_validation"
    SYSTEM_VALIDATION = "system_validation"
    AUTO_LEARNING = "auto_learning"


class FeedbackRequest(BaseModel):
    """Request model for adding feedback."""

    training_data_id: str = Field(
        description="ID of the training data to provide feedback for"
    )
    corrected_data: dict[str, Any] = Field(description="Corrected data from user")
    feedback_type: FeedbackTypeEnum = Field(
        default=FeedbackTypeEnum.USER_CORRECTION,
        description="Type of feedback being provided",
    )
    admin_notes: str | None = Field(
        default=None, description="Optional admin notes about the correction"
    )


class FeedbackResponse(BaseResponse):
    """Response model for feedback submission."""

    training_data_id: str = Field(
        description="ID of the training data that received feedback"
    )


class AIInsightsResponse(BaseResponse):
    """Response model for AI insights."""

    insights: dict[str, Any] = Field(
        description="AI processing insights and statistics"
    )


class ImprovementSuggestionsResponse(BaseResponse):
    """Response model for improvement suggestions."""

    suggestions: list[dict[str, Any]] = Field(
        description="List of improvement suggestions"
    )


class TrainingDataItem(BaseModel):
    """Individual training data item."""

    id: str = Field(description="Training data ID")
    input_text: str = Field(description="Original input text")
    language: str = Field(description="Language of the input")
    status: str = Field(description="Processing status")
    ai_confidence: float = Field(description="AI confidence score")
    accuracy_score: float | None = Field(description="Actual accuracy score")
    error_message: str | None = Field(description="Error message if failed")
    validation_errors: list[str] = Field(description="List of validation errors")
    feedback_provided: bool = Field(description="Whether feedback was provided")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class TrainingDataResponse(BaseResponse):
    """Response model for training data queries."""

    training_data: list[dict[str, Any]] = Field(
        description="List of training data items"
    )
    total_count: int = Field(description="Total number of items returned")


class CategoryMappingResponse(BaseResponse):
    """Response model for category mappings."""

    mappings: dict[str, str] = Field(
        description="Category mappings learned from feedback"
    )
    total_mappings: int = Field(description="Total number of mappings")


class ConfidenceReportResponse(BaseResponse):
    """Response model for confidence calibration report."""

    report: dict[str, Any] = Field(description="Confidence calibration analysis")


class CleanupResponse(BaseResponse):
    """Response model for data cleanup operations."""

    deleted_count: int = Field(description="Number of records deleted")
    days_kept: int = Field(description="Number of days of data kept")
