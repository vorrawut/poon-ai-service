"""Pydantic schemas for category mapping APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from ....domain.entities.category_mapping import (
    CategoryMapping,
    MappingSource,
    MappingType,
)


class CategoryMappingCreateRequest(BaseModel):
    """Request schema for creating a category mapping."""

    key: str = Field(..., description="The input text/pattern to map")
    target_category: str = Field(..., description="The standardized category")
    mapping_type: MappingType = Field(
        default=MappingType.CATEGORY, description="Type of mapping"
    )
    language: str = Field(default="en", description="Language of the key")
    aliases: list[str] | None = Field(default=None, description="Alternative keys")
    patterns: list[str] | None = Field(default=None, description="Regex patterns")
    priority: int = Field(
        default=5, ge=1, le=10, description="Priority (1-10, higher is first)"
    )
    confidence: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Confidence in mapping"
    )
    source: MappingSource = Field(
        default=MappingSource.MANUAL, description="Source of mapping"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )


class CategoryMappingUpdateRequest(BaseModel):
    """Request schema for updating a category mapping."""

    target_category: str | None = Field(
        default=None, description="The standardized category"
    )
    aliases: list[str] | None = Field(default=None, description="Alternative keys")
    patterns: list[str] | None = Field(default=None, description="Regex patterns")
    priority: int | None = Field(
        default=None, ge=1, le=10, description="Priority (1-10)"
    )
    confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Confidence"
    )
    is_active: bool | None = Field(
        default=None, description="Whether mapping is active"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )


class CategoryMappingResponse(BaseModel):
    """Response schema for category mapping."""

    id: str = Field(..., description="Unique mapping ID")
    key: str = Field(..., description="The input text/pattern")
    target_category: str = Field(..., description="The standardized category")
    mapping_type: str = Field(..., description="Type of mapping")
    language: str = Field(..., description="Language of the key")
    aliases: list[str] = Field(..., description="Alternative keys")
    patterns: list[str] = Field(..., description="Regex patterns")
    priority: int = Field(..., description="Priority")
    version: int = Field(..., description="Version number")
    source: str = Field(..., description="Source of mapping")
    confidence: float = Field(..., description="Confidence in mapping")
    is_active: bool = Field(..., description="Whether mapping is active")
    metadata: dict[str, Any] = Field(..., description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_used_at: datetime | None = Field(..., description="Last usage timestamp")

    @classmethod
    def from_entity(cls, mapping: CategoryMapping) -> CategoryMappingResponse:
        """Create response from domain entity."""
        return cls(
            id=str(mapping.id),
            key=mapping.key,
            target_category=mapping.target_category,
            mapping_type=mapping.mapping_type.value,
            language=mapping.language,
            aliases=mapping.aliases,
            patterns=mapping.patterns,
            priority=mapping.priority,
            version=mapping.version,
            source=mapping.source.value,
            confidence=mapping.confidence,
            is_active=mapping.is_active(),
            metadata=mapping.metadata,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
            last_used_at=mapping.last_used,
        )


class MappingCandidateResponse(BaseModel):
    """Response schema for mapping candidates."""

    id: str = Field(..., description="Unique candidate ID")
    original_text: str = Field(..., description="Original input text")
    normalized_text: str = Field(..., description="Normalized text for mapping")
    language: str = Field(..., description="Language of the text")
    suggested_category: str = Field(..., description="AI-suggested category")
    suggested_confidence: float = Field(..., description="AI confidence score")
    suggestion_source: str = Field(..., description="Source of suggestion")
    status: str = Field(..., description="Candidate status")
    created_at: datetime = Field(..., description="Creation timestamp")
    reviewed_at: datetime | None = Field(..., description="Review timestamp")

    @classmethod
    def from_entity(cls, candidate: Any) -> MappingCandidateResponse:
        """Create response from domain entity."""
        return cls(
            id=str(candidate.id),
            original_text=candidate.original_text,
            normalized_text=candidate.normalized_text,
            language=candidate.language,
            suggested_category=candidate.suggested_category,
            suggested_confidence=candidate.suggested_confidence,
            suggestion_source=candidate.suggestion_source.value,
            status=candidate.status.value,
            created_at=candidate.created_at,
            reviewed_at=candidate.reviewed_at,
        )


class MappingStatsResponse(BaseModel):
    """Response schema for mapping statistics."""

    total_mappings: int = Field(..., description="Total number of mappings")
    active_mappings: int = Field(..., description="Number of active mappings")
    inactive_mappings: int = Field(..., description="Number of inactive mappings")
    english_mappings: int = Field(..., description="Number of English mappings")
    thai_mappings: int = Field(..., description="Number of Thai mappings")
    pending_candidates: int = Field(..., description="Number of pending candidates")
    languages: list[str] = Field(..., description="Supported languages")
    mapping_types: list[str] = Field(..., description="Available mapping types")


class MappingTestRequest(BaseModel):
    """Request schema for testing mappings."""

    text: str = Field(..., description="Text to test mapping")
    language: str = Field(default="en", description="Language")


class MappingTestResponse(BaseModel):
    """Response schema for mapping tests."""

    input_text: str = Field(..., description="Input text")
    language: str = Field(..., description="Language")
    mapped_category: str | None = Field(..., description="Mapped category")
    confidence: float = Field(..., description="Mapping confidence")
    method: str = Field(..., description="Mapping method used")
    is_successful: bool = Field(..., description="Whether mapping was successful")
    error: str | None = Field(..., description="Error message if failed")


class BulkCreateResponse(BaseModel):
    """Response schema for bulk create operations."""

    created_count: int = Field(..., description="Number of mappings created")
    error_count: int = Field(..., description="Number of errors")
    created_mappings: list[str] = Field(..., description="Keys of created mappings")
    errors: list[dict[str, str]] = Field(..., description="List of errors")


# Configuration for Pydantic models
class CategoryMappingConfig:
    """Configuration for category mapping models."""

    model_config: ClassVar[dict[str, Any]] = {
        "from_attributes": True,
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
        },
    }
