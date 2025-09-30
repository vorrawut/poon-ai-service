"""Repository interface for category mapping operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..entities.category_mapping import (
    CategoryMapping,
    CategoryMappingId,
    MappingCandidate,
    MappingStatus,
    MappingType,
)


class CategoryMappingRepository(ABC):
    """Abstract repository for category mapping operations."""

    @abstractmethod
    async def save_mapping(self, mapping: CategoryMapping) -> None:
        """Save or update a category mapping."""

    @abstractmethod
    async def find_by_id(self, mapping_id: CategoryMappingId) -> CategoryMapping | None:
        """Find mapping by ID."""

    @abstractmethod
    async def find_by_key(
        self, key: str, language: str = "en"
    ) -> CategoryMapping | None:
        """Find mapping by exact key match."""

    @abstractmethod
    async def find_by_text(
        self, text: str, language: str = "en", limit: int = 10
    ) -> list[CategoryMapping]:
        """Find mappings that could match the given text."""

    @abstractmethod
    async def search_mappings(
        self,
        query: str | None = None,
        mapping_type: MappingType | None = None,
        language: str | None = None,
        status: MappingStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CategoryMapping]:
        """Search mappings with filters."""

    @abstractmethod
    async def get_all_active_mappings(
        self, language: str | None = None
    ) -> list[CategoryMapping]:
        """Get all active mappings, optionally filtered by language."""

    @abstractmethod
    async def delete_mapping(self, mapping_id: CategoryMappingId) -> bool:
        """Delete a mapping by ID."""

    @abstractmethod
    async def update_usage_stats(
        self, mapping_id: CategoryMappingId, success: bool
    ) -> None:
        """Update usage statistics for a mapping."""

    @abstractmethod
    async def get_mappings_by_category(
        self, category: str, language: str = "en"
    ) -> list[CategoryMapping]:
        """Get all mappings for a specific category."""

    @abstractmethod
    async def get_low_confidence_mappings(
        self, threshold: float = 0.7
    ) -> list[CategoryMapping]:
        """Get mappings with confidence below threshold."""

    @abstractmethod
    async def get_unused_mappings(self, days: int = 30) -> list[CategoryMapping]:
        """Get mappings not used in the last N days."""

    # Mapping candidates methods
    @abstractmethod
    async def save_candidate(self, candidate: MappingCandidate) -> None:
        """Save a mapping candidate for review."""

    @abstractmethod
    async def find_candidate_by_id(
        self, candidate_id: CategoryMappingId
    ) -> MappingCandidate | None:
        """Find candidate by ID."""

    @abstractmethod
    async def get_pending_candidates(
        self, limit: int = 50, offset: int = 0
    ) -> list[MappingCandidate]:
        """Get candidates pending review."""

    @abstractmethod
    async def find_similar_candidates(
        self, text: str, language: str = "en", limit: int = 5
    ) -> list[MappingCandidate]:
        """Find similar candidates for the given text."""

    @abstractmethod
    async def update_candidate_status(
        self, candidate_id: CategoryMappingId, status: MappingStatus
    ) -> None:
        """Update candidate status."""

    @abstractmethod
    async def get_candidate_stats(self) -> dict[str, Any]:
        """Get statistics about mapping candidates."""

    # Bulk operations
    @abstractmethod
    async def bulk_create_mappings(self, mappings: list[CategoryMapping]) -> int:
        """Bulk create mappings, returns count of created mappings."""

    @abstractmethod
    async def bulk_update_mappings(self, mappings: list[CategoryMapping]) -> int:
        """Bulk update mappings, returns count of updated mappings."""

    # Analytics and insights
    @abstractmethod
    async def get_mapping_analytics(self, days: int = 30) -> dict[str, Any]:
        """Get analytics about mapping usage and performance."""

    @abstractmethod
    async def get_popular_mappings(
        self, limit: int = 20, language: str | None = None
    ) -> list[CategoryMapping]:
        """Get most frequently used mappings."""

    @abstractmethod
    async def get_category_distribution(
        self, language: str | None = None
    ) -> dict[str, int]:
        """Get distribution of mappings by category."""

    # Cache management
    @abstractmethod
    async def get_cache_version(self) -> str:
        """Get current cache version/timestamp for invalidation."""

    @abstractmethod
    async def cleanup_old_data(self, days: int = 365) -> int:
        """Clean up old mapping data, returns count of deleted items."""
