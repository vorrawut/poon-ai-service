"""Category mapping entities for dynamic, database-driven mapping system."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MappingType(str, Enum):
    """Type of mapping entry."""

    MERCHANT = "merchant"
    CATEGORY = "category"
    RULE = "rule"
    ALIAS = "alias"
    PATTERN = "pattern"


class MappingSource(str, Enum):
    """Source of the mapping."""

    MANUAL = "manual"
    AUTO_LEARNED = "auto_learned"
    MODEL_SUGGESTION = "model_suggestion"
    USER_CORRECTION = "user_correction"
    ADMIN_REVIEW = "admin_review"


class MappingStatus(str, Enum):
    """Status of the mapping."""

    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


@dataclass(frozen=True)
class CategoryMappingId:
    """Unique identifier for category mapping."""

    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def generate(cls) -> CategoryMappingId:
        """Generate a new mapping ID."""
        return cls()

    @classmethod
    def from_string(cls, value: str) -> CategoryMappingId:
        """Create ID from string value."""
        if not value or not value.strip():
            raise ValueError("CategoryMappingId must be a non-empty string")
        return cls(value=value)

    def __str__(self) -> str:
        """Return string representation."""
        return self.value

    def __hash__(self) -> int:
        """Make the ID hashable."""
        return hash(self.value)


@dataclass
class CategoryMapping:
    """Entity representing a category mapping with metadata."""

    id: CategoryMappingId = field(default_factory=CategoryMappingId.generate)

    # Core mapping data
    key: str = ""  # Primary lookup key (normalized)
    mapping_type: MappingType = MappingType.CATEGORY
    language: str = "en"
    target_category: str = ""

    # Alternative lookup methods
    aliases: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)

    # Metadata
    priority: int = 10  # Higher number = higher priority
    confidence: float = 0.8
    source: MappingSource = MappingSource.MANUAL
    status: MappingStatus = MappingStatus.ACTIVE

    # Usage statistics
    usage_count: int = 0
    success_rate: float = 0.0
    last_used: datetime | None = None

    # Versioning and audit
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str | None = None
    updated_by: str | None = None

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def update_usage_stats(self, success: bool) -> None:
        """Update usage statistics."""
        self.usage_count += 1
        self.last_used = datetime.utcnow()

        # Update success rate using exponential moving average
        alpha = 0.1  # Learning rate
        if self.usage_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            current_success = 1.0 if success else 0.0
            self.success_rate = (
                1 - alpha
            ) * self.success_rate + alpha * current_success

        self.updated_at = datetime.utcnow()

    def increment_version(self, updated_by: str | None = None) -> None:
        """Increment version for tracking changes."""
        self.version += 1
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by

    def add_alias(self, alias: str) -> None:
        """Add a new alias if not already present."""
        normalized_alias = alias.lower().strip()
        if normalized_alias and normalized_alias not in [
            a.lower() for a in self.aliases
        ]:
            self.aliases.append(alias)
            self.increment_version()

    def add_pattern(self, pattern: str) -> None:
        """Add a new regex pattern if not already present."""
        if pattern and pattern not in self.patterns:
            self.patterns.append(pattern)
            self.increment_version()

    def is_active(self) -> bool:
        """Check if mapping is active and usable."""
        return self.status == MappingStatus.ACTIVE

    def matches_key(self, text: str) -> bool:
        """Check if text matches the primary key."""
        return self.key.lower() == text.lower().strip()

    def matches_alias(self, text: str) -> bool:
        """Check if text matches any alias."""
        text_lower = text.lower().strip()
        return any(alias.lower() == text_lower for alias in self.aliases)

    def matches_pattern(self, text: str) -> bool:
        """Check if text matches any regex pattern."""
        import re

        for pattern in self.patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error:
                # Skip invalid regex patterns
                continue
        return False

    def calculate_match_confidence(self, text: str) -> float:
        """Calculate confidence score for a text match."""
        if self.matches_key(text):
            return min(self.confidence * 1.0, 1.0)  # Exact key match
        elif self.matches_alias(text):
            return min(self.confidence * 0.9, 1.0)  # Alias match
        elif self.matches_pattern(text):
            return min(self.confidence * 0.8, 1.0)  # Pattern match
        else:
            return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id.value,
            "key": self.key,
            "mapping_type": self.mapping_type.value,
            "language": self.language,
            "target_category": self.target_category,
            "aliases": self.aliases,
            "patterns": self.patterns,
            "priority": self.priority,
            "confidence": self.confidence,
            "source": self.source.value,
            "status": self.status.value,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "metadata": self.metadata,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CategoryMapping:
        """Create from dictionary."""
        return cls(
            id=CategoryMappingId.from_string(data["id"]),
            key=data.get("key", ""),
            mapping_type=MappingType(
                data.get("mapping_type", MappingType.CATEGORY.value)
            ),
            language=data.get("language", "en"),
            target_category=data.get("target_category", ""),
            aliases=data.get("aliases", []),
            patterns=data.get("patterns", []),
            priority=data.get("priority", 10),
            confidence=data.get("confidence", 0.8),
            source=MappingSource(data.get("source", MappingSource.MANUAL.value)),
            status=MappingStatus(data.get("status", MappingStatus.ACTIVE.value)),
            usage_count=data.get("usage_count", 0),
            success_rate=data.get("success_rate", 0.0),
            last_used=datetime.fromisoformat(data["last_used"])
            if isinstance(data.get("last_used"), str)
            else data.get("last_used"),
            version=data.get("version", 1),
            created_at=datetime.fromisoformat(data["created_at"])
            if isinstance(data.get("created_at"), str)
            else data.get("created_at", datetime.utcnow()),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if isinstance(data.get("updated_at"), str)
            else data.get("updated_at", datetime.utcnow()),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )


@dataclass
class MappingCandidate:
    """Entity for mapping candidates that need review."""

    id: CategoryMappingId = field(default_factory=CategoryMappingId.generate)

    # Input data
    original_text: str = ""
    normalized_text: str = ""
    language: str = "en"

    # Suggested mapping
    suggested_category: str = ""
    suggested_confidence: float = 0.0
    suggestion_source: str = ""  # "llm", "pattern", "fuzzy_match"

    # Context
    user_id: str | None = None
    session_id: str | None = None
    attempt_count: int = 1

    # Review status
    status: MappingStatus = MappingStatus.PENDING_REVIEW
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    approved_mapping: str | None = None
    rejection_reason: str | None = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def approve(self, approved_category: str, reviewed_by: str | None = None) -> None:
        """Approve the mapping candidate."""
        self.status = MappingStatus.ACTIVE
        self.approved_mapping = approved_category
        self.reviewed_by = reviewed_by
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def reject(self, reason: str, reviewed_by: str | None = None) -> None:
        """Reject the mapping candidate."""
        self.status = MappingStatus.REJECTED
        self.rejection_reason = reason
        self.reviewed_by = reviewed_by
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_attempts(self) -> None:
        """Increment attempt count."""
        self.attempt_count += 1
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id.value,
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "language": self.language,
            "suggested_category": self.suggested_category,
            "suggested_confidence": self.suggested_confidence,
            "suggestion_source": self.suggestion_source,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "attempt_count": self.attempt_count,
            "status": self.status.value,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "approved_mapping": self.approved_mapping,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MappingCandidate:
        """Create from dictionary."""
        return cls(
            id=CategoryMappingId.from_string(data["id"]),
            original_text=data.get("original_text", ""),
            normalized_text=data.get("normalized_text", ""),
            language=data.get("language", "en"),
            suggested_category=data.get("suggested_category", ""),
            suggested_confidence=data.get("suggested_confidence", 0.0),
            suggestion_source=data.get("suggestion_source", ""),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            attempt_count=data.get("attempt_count", 1),
            status=MappingStatus(
                data.get("status", MappingStatus.PENDING_REVIEW.value)
            ),
            reviewed_by=data.get("reviewed_by"),
            reviewed_at=datetime.fromisoformat(data["reviewed_at"])
            if isinstance(data.get("reviewed_at"), str)
            else data.get("reviewed_at"),
            approved_mapping=data.get("approved_mapping"),
            rejection_reason=data.get("rejection_reason"),
            created_at=datetime.fromisoformat(data["created_at"])
            if isinstance(data.get("created_at"), str)
            else data.get("created_at", datetime.utcnow()),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if isinstance(data.get("updated_at"), str)
            else data.get("updated_at", datetime.utcnow()),
            metadata=data.get("metadata", {}),
        )
