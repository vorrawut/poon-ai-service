"""Repository interface for AI training data."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from ..entities.ai_training_data import (
    AITrainingData,
    AITrainingDataId,
    ProcessingStatus,
)


class AITrainingRepository(ABC):
    """Repository interface for AI training data operations."""

    @abstractmethod
    async def save(self, training_data: AITrainingData) -> None:
        """Save AI training data."""
        pass

    @abstractmethod
    async def find_by_id(self, training_id: AITrainingDataId) -> AITrainingData | None:
        """Find training data by ID."""
        pass

    @abstractmethod
    async def find_by_status(
        self, status: ProcessingStatus, limit: int = 100, offset: int = 0
    ) -> list[AITrainingData]:
        """Find training data by processing status."""
        pass

    @abstractmethod
    async def find_failed_cases(
        self, limit: int = 100, offset: int = 0
    ) -> list[AITrainingData]:
        """Find failed processing cases for review."""
        pass

    @abstractmethod
    async def find_by_language(
        self, language: str, limit: int = 100, offset: int = 0
    ) -> list[AITrainingData]:
        """Find training data by language."""
        pass

    @abstractmethod
    async def find_low_accuracy_cases(
        self, accuracy_threshold: float = 0.7, limit: int = 100, offset: int = 0
    ) -> list[AITrainingData]:
        """Find cases with low accuracy scores."""
        pass

    @abstractmethod
    async def get_accuracy_stats(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> dict[str, Any]:
        """Get accuracy statistics over time."""
        pass

    @abstractmethod
    async def get_category_mapping_insights(self) -> dict[str, str]:
        """Get learned category mappings from feedback."""
        pass

    @abstractmethod
    async def get_common_error_patterns(self) -> list[dict[str, Any]]:
        """Get common error patterns for model improvement."""
        pass

    @abstractmethod
    async def find_similar_inputs(
        self, input_text: str, language: str, limit: int = 10
    ) -> list[AITrainingData]:
        """Find similar input texts for learning."""
        pass

    @abstractmethod
    async def count_by_status(self) -> dict[str, int]:
        """Count training data by status."""
        pass

    @abstractmethod
    async def delete_old_data(self, older_than_days: int = 365) -> int:
        """Delete old training data (returns count deleted)."""
        pass
