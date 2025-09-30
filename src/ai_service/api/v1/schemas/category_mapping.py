"""Pydantic schemas for category mapping API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from ....domain.entities.category_mapping import CategoryMapping, MappingCandidate


class CategoryMappingCreateRequest(BaseModel):
    """Request schema for creating a category mapping."""

    key: str = Field(..., description="Primary lookup key")
    target_category: str = Field(..., description="Target category")
    language: str = Field("en", description="Language code")
    aliases: list[str] = Field(
        default_factory=list, description="Alternative lookup keys"
    )
    patterns: list[str] = Field(default_factory=list, description="Regex patterns")
    confidence: float = Field(0.9, ge=0.0, le=1.0, description="Confidence score")
    created_by: str | None = Field(None, description="Creator identifier")

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Validate key is not empty."""
        if not v or not v.strip():
            raise ValueError("Key cannot be empty")
        return v.strip()

    @field_validator("target_category")
    @classmethod
    def validate_target_category(cls, v: str) -> str:
        """Validate target category is not empty."""
        if not v or not v.strip():
            raise ValueError("Target category cannot be empty")
        return v.strip()

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code."""
        if not v or len(v) < 2:
            raise ValueError("Language code must be at least 2 characters")
        return v.lower()


class CategoryMappingUpdateRequest(BaseModel):
    """Request schema for updating a category mapping."""

    target_category: str | None = Field(None, description="Target category")
    aliases: list[str] | None = Field(None, description="Alternative lookup keys")
    patterns: list[str] | None = Field(None, description="Regex patterns")
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence score"
    )
    status: str | None = Field(None, description="Mapping status")
    updated_by: str | None = Field(None, description="Updater identifier")

    @field_validator("target_category")
    @classmethod
    def validate_target_category(cls, v: str | None) -> str | None:
        """Validate target category is not empty."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Target category cannot be empty")
        return v.strip() if v else None


class CategoryMappingResponse(BaseModel):
    """Response schema for category mapping."""

    id: str = Field(..., description="Mapping ID")
    key: str = Field(..., description="Primary lookup key")
    mapping_type: str = Field(..., description="Type of mapping")
    language: str = Field(..., description="Language code")
    target_category: str = Field(..., description="Target category")
    aliases: list[str] = Field(..., description="Alternative lookup keys")
    patterns: list[str] = Field(..., description="Regex patterns")
    priority: int = Field(..., description="Priority for ordering")
    confidence: float = Field(..., description="Confidence score")
    source: str = Field(..., description="Source of mapping")
    status: str = Field(..., description="Mapping status")
    usage_count: int = Field(..., description="Number of times used")
    success_rate: float = Field(..., description="Success rate")
    last_used: datetime | None = Field(None, description="Last used timestamp")
    version: int = Field(..., description="Version number")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: str | None = Field(None, description="Creator identifier")
    updated_by: str | None = Field(None, description="Last updater identifier")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    tags: list[str] = Field(default_factory=list, description="Tags")

    @classmethod
    def from_entity(cls, mapping: CategoryMapping) -> CategoryMappingResponse:
        """Create response from domain entity."""
        return cls(
            id=mapping.id.value,
            key=mapping.key,
            mapping_type=mapping.mapping_type.value,
            language=mapping.language,
            target_category=mapping.target_category,
            aliases=mapping.aliases,
            patterns=mapping.patterns,
            priority=mapping.priority,
            confidence=mapping.confidence,
            source=mapping.source.value,
            status=mapping.status.value,
            usage_count=mapping.usage_count,
            success_rate=mapping.success_rate,
            last_used=mapping.last_used,
            version=mapping.version,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
            created_by=mapping.created_by,
            updated_by=mapping.updated_by,
            metadata=mapping.metadata,
            tags=mapping.tags,
        )


class MappingCandidateResponse(BaseModel):
    """Response schema for mapping candidate."""

    id: str = Field(..., description="Candidate ID")
    original_text: str = Field(..., description="Original text")
    normalized_text: str = Field(..., description="Normalized text")
    language: str = Field(..., description="Language code")
    suggested_category: str = Field(..., description="Suggested category")
    suggested_confidence: float = Field(..., description="Suggestion confidence")
    suggestion_source: str = Field(..., description="Source of suggestion")
    user_id: str | None = Field(None, description="User ID")
    session_id: str | None = Field(None, description="Session ID")
    attempt_count: int = Field(..., description="Number of attempts")
    status: str = Field(..., description="Review status")
    reviewed_by: str | None = Field(None, description="Reviewer ID")
    reviewed_at: datetime | None = Field(None, description="Review timestamp")
    approved_mapping: str | None = Field(None, description="Approved mapping")
    rejection_reason: str | None = Field(None, description="Rejection reason")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @classmethod
    def from_entity(cls, candidate: MappingCandidate) -> MappingCandidateResponse:
        """Create response from domain entity."""
        return cls(
            id=candidate.id.value,
            original_text=candidate.original_text,
            normalized_text=candidate.normalized_text,
            language=candidate.language,
            suggested_category=candidate.suggested_category,
            suggested_confidence=candidate.suggested_confidence,
            suggestion_source=candidate.suggestion_source,
            user_id=candidate.user_id,
            session_id=candidate.session_id,
            attempt_count=candidate.attempt_count,
            status=candidate.status.value,
            reviewed_by=candidate.reviewed_by,
            reviewed_at=candidate.reviewed_at,
            approved_mapping=candidate.approved_mapping,
            rejection_reason=candidate.rejection_reason,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at,
            metadata=candidate.metadata,
        )


class MappingResultResponse(BaseModel):
    """Response schema for mapping result."""

    category: str | None = Field(None, description="Mapped category")
    confidence: float = Field(..., description="Confidence score")
    source: str = Field(..., description="Source of mapping")
    mapping_id: str | None = Field(None, description="Mapping ID used")
    fallback_used: bool = Field(False, description="Whether fallback was used")
    cached: bool = Field(False, description="Whether result was cached")


class ApproveCandidateRequest(BaseModel):
    """Request schema for approving a candidate."""

    approved_category: str = Field(..., description="Approved category")
    reviewed_by: str | None = Field(None, description="Reviewer identifier")

    @field_validator("approved_category")
    @classmethod
    def validate_approved_category(cls, v: str) -> str:
        """Validate approved category is not empty."""
        if not v or not v.strip():
            raise ValueError("Approved category cannot be empty")
        return v.strip()


class MappingStatsResponse(BaseModel):
    """Response schema for mapping statistics."""

    mappings: dict[str, Any] = Field(
        default_factory=dict, description="Mapping analytics"
    )
    candidates: dict[str, Any] = Field(
        default_factory=dict, description="Candidate statistics"
    )
    categories: dict[str, int] = Field(
        default_factory=dict, description="Category distribution"
    )
    cache_size: int = Field(0, description="Cache size")
    cache_version: str = Field("", description="Cache version")


class BulkImportRequest(BaseModel):
    """Request schema for bulk importing mappings."""

    mappings: list[CategoryMappingCreateRequest] = Field(
        ..., description="List of mappings to import"
    )
    overwrite_existing: bool = Field(
        False, description="Whether to overwrite existing mappings"
    )


class MappingSearchRequest(BaseModel):
    """Request schema for searching mappings."""

    query: str | None = Field(None, description="Search query")
    mapping_type: str | None = Field(None, description="Filter by mapping type")
    language: str | None = Field(None, description="Filter by language")
    status: str | None = Field(None, description="Filter by status")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class CategoryDistributionResponse(BaseModel):
    """Response schema for category distribution."""

    categories: dict[str, int] = Field(..., description="Category counts")
    total_mappings: int = Field(..., description="Total number of mappings")
    languages: list[str] = Field(..., description="Available languages")


class MappingAnalyticsResponse(BaseModel):
    """Response schema for mapping analytics."""

    total_mappings: int = Field(0, description="Total number of mappings")
    active_mappings: int = Field(0, description="Number of active mappings")
    pending_candidates: int = Field(0, description="Number of pending candidates")
    auto_learned_mappings: int = Field(0, description="Number of auto-learned mappings")
    success_rate: float = Field(0.0, description="Overall success rate")
    cache_hit_rate: float = Field(0.0, description="Cache hit rate")
    popular_categories: list[str] = Field(
        default_factory=list, description="Most popular categories"
    )
    recent_activity: dict[str, int] = Field(
        default_factory=dict, description="Recent activity stats"
    )


class MappingHealthResponse(BaseModel):
    """Response schema for mapping system health."""

    status: str = Field(..., description="Overall health status")
    database_connected: bool = Field(..., description="Database connection status")
    cache_operational: bool = Field(..., description="Cache operational status")
    last_cache_refresh: datetime | None = Field(
        None, description="Last cache refresh time"
    )
    pending_candidates_count: int = Field(0, description="Number of pending candidates")
    low_confidence_mappings: int = Field(
        0, description="Number of low confidence mappings"
    )
    unused_mappings: int = Field(0, description="Number of unused mappings")
    recommendations: list[str] = Field(
        default_factory=list, description="Health recommendations"
    )
