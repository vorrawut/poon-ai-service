"""Confidence score value object for AI processing results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConfidenceScore:
    """Immutable confidence score value object (0.0 to 1.0)."""

    value: float

    def __post_init__(self) -> None:
        """Validate confidence score constraints."""
        if not isinstance(self.value, (int, float)):
            msg = f"Confidence score must be numeric, got {type(self.value)}"
            raise TypeError(msg)

        if not 0.0 <= self.value <= 1.0:
            msg = f"Confidence score must be between 0.0 and 1.0, got {self.value}"
            raise ValueError(msg)

    @classmethod
    def from_percentage(cls, percentage: float) -> ConfidenceScore:
        """Create confidence score from percentage (0-100)."""
        if not 0.0 <= percentage <= 100.0:
            msg = f"Percentage must be between 0 and 100, got {percentage}"
            raise ValueError(msg)
        return cls(value=percentage / 100.0)

    @classmethod
    def low(cls) -> ConfidenceScore:
        """Create low confidence score (0.3)."""
        return cls(value=0.3)

    @classmethod
    def medium(cls) -> ConfidenceScore:
        """Create medium confidence score (0.6)."""
        return cls(value=0.6)

    @classmethod
    def high(cls) -> ConfidenceScore:
        """Create high confidence score (0.9)."""
        return cls(value=0.9)

    @classmethod
    def perfect(cls) -> ConfidenceScore:
        """Create perfect confidence score (1.0)."""
        return cls(value=1.0)

    @classmethod
    def zero(cls) -> ConfidenceScore:
        """Create zero confidence score (0.0)."""
        return cls(value=0.0)

    def to_percentage(self) -> float:
        """Convert to percentage (0-100)."""
        return self.value * 100.0

    def is_high(self) -> bool:
        """Check if confidence is high (>= 0.8)."""
        return self.value >= 0.8

    def is_medium(self) -> bool:
        """Check if confidence is medium (>= 0.6 and < 0.8)."""
        return 0.6 <= self.value < 0.8

    def is_low(self) -> bool:
        """Check if confidence is low (< 0.6)."""
        return self.value < 0.6

    def is_acceptable(self) -> bool:
        """Check if confidence is acceptable for production use (>= 0.7)."""
        return self.value >= 0.7

    def boost(self, factor: float = 0.1) -> ConfidenceScore:
        """Boost confidence by a factor (capped at 1.0)."""
        if factor < 0:
            msg = "Boost factor cannot be negative"
            raise ValueError(msg)

        new_value = min(1.0, self.value + factor)
        return ConfidenceScore(value=new_value)

    def reduce(self, factor: float = 0.1) -> ConfidenceScore:
        """Reduce confidence by a factor (floored at 0.0)."""
        if factor < 0:
            msg = "Reduction factor cannot be negative"
            raise ValueError(msg)

        new_value = max(0.0, self.value - factor)
        return ConfidenceScore(value=new_value)

    def combine_with(self, other: ConfidenceScore) -> ConfidenceScore:
        """Combine two confidence scores using geometric mean."""
        combined_value = (self.value * other.value) ** 0.5
        return ConfidenceScore(value=combined_value)

    def __str__(self) -> str:
        """String representation of confidence score."""
        percentage = self.to_percentage()
        if self.is_high():
            return f"{percentage:.1f}% (High)"
        elif self.is_medium():
            return f"{percentage:.1f}% (Medium)"
        else:
            return f"{percentage:.1f}% (Low)"

    def __eq__(self, other: Any) -> bool:
        """Check equality with tolerance for floating point."""
        if not isinstance(other, ConfidenceScore):
            return False
        return abs(self.value - other.value) < 1e-9

    def __lt__(self, other: ConfidenceScore) -> bool:
        """Less than comparison."""
        return self.value < other.value

    def __le__(self, other: ConfidenceScore) -> bool:
        """Less than or equal comparison."""
        return self.value <= other.value

    def __gt__(self, other: ConfidenceScore) -> bool:
        """Greater than comparison."""
        return self.value > other.value

    def __ge__(self, other: ConfidenceScore) -> bool:
        """Greater than or equal comparison."""
        return self.value >= other.value
