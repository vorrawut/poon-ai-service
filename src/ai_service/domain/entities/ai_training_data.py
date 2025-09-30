"""AI Training Data entities for continuous learning system."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..value_objects.confidence import ConfidenceScore


class ProcessingStatus(str, Enum):
    """Status of AI processing attempts."""

    SUCCESS = "success"
    FAILED_VALIDATION = "failed_validation"
    FAILED_PARSING = "failed_parsing"
    FAILED_MAPPING = "failed_mapping"
    MANUAL_CORRECTION = "manual_correction"
    PENDING_REVIEW = "pending_review"


class FeedbackType(str, Enum):
    """Type of feedback provided."""

    USER_CORRECTION = "user_correction"
    ADMIN_VALIDATION = "admin_validation"
    SYSTEM_VALIDATION = "system_validation"
    AUTO_LEARNING = "auto_learning"


@dataclass(frozen=True)
class AITrainingDataId:
    """Unique identifier for AI training data."""

    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def generate(cls) -> AITrainingDataId:
        """Generate a new training data ID."""
        return cls()

    @classmethod
    def from_string(cls, value: str) -> AITrainingDataId:
        """Create ID from string value."""
        if not value or not value.strip():
            raise ValueError("AITrainingDataId must be a non-empty string")
        return cls(value=value)

    def __str__(self) -> str:
        """Return string representation."""
        return self.value

    def __hash__(self) -> int:
        """Make the ID hashable."""
        return hash(self.value)


@dataclass
class AITrainingData:
    """Entity for storing AI training data and feedback."""

    id: AITrainingDataId = field(default_factory=AITrainingDataId.generate)

    # Input data
    input_text: str = ""
    language: str = "en"
    user_id: str | None = None
    session_id: str | None = None

    # AI Response
    raw_ai_response: str = ""
    parsed_ai_data: dict[str, Any] = field(default_factory=dict)
    ai_confidence: ConfidenceScore = field(default_factory=lambda: ConfidenceScore(0.5))
    processing_time_ms: int = 0
    model_version: str = ""

    # Processing Status
    status: ProcessingStatus = ProcessingStatus.SUCCESS
    error_message: str | None = None
    validation_errors: list[str] = field(default_factory=list)

    # Final Result
    final_spending_data: dict[str, Any] = field(default_factory=dict)
    spending_entry_id: str | None = None

    # Feedback and Learning
    feedback_provided: bool = False
    feedback_type: FeedbackType | None = None
    corrected_data: dict[str, Any] = field(default_factory=dict)
    admin_notes: str | None = None

    # Learning Metrics
    accuracy_score: float | None = None
    improvement_suggestions: list[str] = field(default_factory=list)
    category_mapping_learned: dict[str, str] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_at: datetime | None = None

    def mark_as_failed(
        self, error: str, validation_errors: list[str] | None = None
    ) -> None:
        """Mark this training data as failed."""
        self.status = ProcessingStatus.FAILED_VALIDATION
        self.error_message = error
        self.validation_errors = validation_errors or []
        self.updated_at = datetime.utcnow()

    def add_feedback(
        self,
        feedback_type: FeedbackType,
        corrected_data: dict[str, Any],
        admin_notes: str | None = None,
    ) -> None:
        """Add feedback and corrections."""
        self.feedback_provided = True
        self.feedback_type = feedback_type
        self.corrected_data = corrected_data
        self.admin_notes = admin_notes
        self.updated_at = datetime.utcnow()

        # Calculate accuracy score
        self._calculate_accuracy_score()

        # Extract category mappings from corrections
        self._extract_category_mappings()

    def _calculate_accuracy_score(self) -> None:
        """Calculate accuracy score based on corrections needed."""
        if not self.corrected_data or not self.parsed_ai_data:
            return

        total_fields = len(self.parsed_ai_data)
        correct_fields = 0

        for key, ai_value in self.parsed_ai_data.items():
            corrected_value = self.corrected_data.get(key)
            if corrected_value is None or ai_value == corrected_value:
                correct_fields += 1

        self.accuracy_score = correct_fields / total_fields if total_fields > 0 else 0.0

    def generate_learning_insights(self) -> dict[str, Any]:
        """Generate insights for model improvement."""
        insights = {
            "input_text": self.input_text,
            "language": self.language,
            "status": self.status.value,
            "ai_confidence": self.ai_confidence.value,
            "accuracy_score": self.accuracy_score,
            "feedback_provided": self.feedback_provided,
            "feedback_type": self.feedback_type.value if self.feedback_type else None,
            "error_message": self.error_message,
            "validation_errors": self.validation_errors,
            "category_mapping_learned": self.category_mapping_learned,
            "input_patterns": self._analyze_input_patterns(),
            "common_errors": self._identify_common_errors(),
            "category_mappings": self.category_mapping_learned,
            "confidence_accuracy_analysis": self._analyze_confidence_accuracy(),
        }
        return insights

    def _analyze_input_patterns(self) -> dict[str, Any]:
        """Analyze patterns in input text."""
        return {
            "text_length": len(self.input_text),
            "language": self.language,
            "contains_numbers": any(c.isdigit() for c in self.input_text),
            "contains_currency": any(
                curr in self.input_text.lower()
                for curr in ["บาท", "baht", "$", "€", "¥"]
            ),
            "word_count": len(self.input_text.split()),
        }

    def _identify_common_errors(self) -> list[str]:
        """Identify common error patterns."""
        errors = []
        if self.error_message:
            errors.append(self.error_message)
        # Include validation errors regardless of status if they exist
        if self.validation_errors:
            errors.extend(self.validation_errors)
        return errors

    def _extract_category_mappings(self) -> None:
        """Extract category mapping learnings and update the learned mappings."""
        if not self.corrected_data or not self.parsed_ai_data:
            return

        ai_category = self.parsed_ai_data.get("category")
        corrected_category = self.corrected_data.get("category")

        if ai_category and corrected_category and ai_category != corrected_category:
            self.category_mapping_learned[ai_category] = corrected_category

    def _analyze_confidence_accuracy(self) -> dict[str, Any]:
        """Analyze how well AI confidence correlates with actual accuracy."""
        return {
            "ai_confidence": float(self.ai_confidence.value),
            "actual_accuracy": self.accuracy_score,
            "confidence_gap": abs(
                float(self.ai_confidence.value) - (self.accuracy_score or 0.0)
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id.value,
            "input_text": self.input_text,
            "language": self.language,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "raw_ai_response": self.raw_ai_response,
            "parsed_ai_data": self.parsed_ai_data,
            "ai_confidence": float(self.ai_confidence.value),
            "processing_time_ms": self.processing_time_ms,
            "model_version": self.model_version,
            "status": self.status.value,
            "error_message": self.error_message,
            "validation_errors": self.validation_errors,
            "final_spending_data": self.final_spending_data,
            "spending_entry_id": self.spending_entry_id,
            "feedback_provided": self.feedback_provided,
            "feedback_type": self.feedback_type.value if self.feedback_type else None,
            "corrected_data": self.corrected_data,
            "admin_notes": self.admin_notes,
            "accuracy_score": self.accuracy_score,
            "improvement_suggestions": self.improvement_suggestions,
            "category_mapping_learned": self.category_mapping_learned,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AITrainingData:
        """Create from dictionary."""
        return cls(
            id=AITrainingDataId.from_string(data["id"]),
            input_text=data.get("input_text", ""),
            language=data.get("language", "en"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            raw_ai_response=data.get("raw_ai_response", ""),
            parsed_ai_data=data.get("parsed_ai_data", {}),
            ai_confidence=ConfidenceScore(data.get("ai_confidence", 0.5)),
            processing_time_ms=data.get("processing_time_ms", 0),
            model_version=data.get("model_version", ""),
            status=ProcessingStatus(data.get("status", ProcessingStatus.SUCCESS.value)),
            error_message=data.get("error_message"),
            validation_errors=data.get("validation_errors", []),
            final_spending_data=data.get("final_spending_data", {}),
            spending_entry_id=data.get("spending_entry_id"),
            feedback_provided=data.get("feedback_provided", False),
            feedback_type=FeedbackType(data["feedback_type"])
            if data.get("feedback_type")
            else None,
            corrected_data=data.get("corrected_data", {}),
            admin_notes=data.get("admin_notes"),
            accuracy_score=data.get("accuracy_score"),
            improvement_suggestions=data.get("improvement_suggestions", []),
            category_mapping_learned=data.get("category_mapping_learned", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if isinstance(data.get("created_at"), str)
            else data.get("created_at", datetime.utcnow()),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if isinstance(data.get("updated_at"), str)
            else data.get("updated_at", datetime.utcnow()),
            reviewed_at=datetime.fromisoformat(data["reviewed_at"])
            if isinstance(data.get("reviewed_at"), str)
            else data.get("reviewed_at"),
        )
