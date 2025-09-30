"""Spending-related domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import SpendingDomainEvent


@dataclass(frozen=True)
class SpendingEntryCreated(SpendingDomainEvent):
    """Event fired when a new spending entry is created."""

    amount: float = field(default=0.0)
    merchant: str = field(default="")
    category: str = field(default="")

    @property
    def event_type(self) -> str:
        """Get the event type identifier."""
        return "spending_entry.created"

    def get_event_data(self) -> dict[str, Any]:
        """Get the event data payload."""
        return {
            "entry_id": self.entry_id,
            "amount": self.amount,
            "merchant": self.merchant,
            "category": self.category,
        }


@dataclass(frozen=True)
class SpendingEntryUpdated(SpendingDomainEvent):
    """Event fired when a spending entry is updated."""

    field_updated: str = field(default="")
    old_value: Any = field(default=None)
    new_value: Any = field(default=None)

    @property
    def event_type(self) -> str:
        """Get the event type identifier."""
        return "spending_entry.updated"

    def get_event_data(self) -> dict[str, Any]:
        """Get the event data payload."""
        return {
            "entry_id": self.entry_id,
            "field_updated": self.field_updated,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


@dataclass(frozen=True)
class SpendingEntryDeleted(SpendingDomainEvent):
    """Event fired when a spending entry is deleted."""

    reason: str | None = None

    @property
    def event_type(self) -> str:
        """Get the event type identifier."""
        return "spending_entry.deleted"

    def get_event_data(self) -> dict[str, Any]:
        """Get the event data payload."""
        return {
            "entry_id": self.entry_id,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class SpendingEntryAIEnhanced(SpendingDomainEvent):
    """Event fired when a spending entry is enhanced with AI."""

    ai_model: str = field(default="")
    confidence_before: float = field(default=0.0)
    confidence_after: float = field(default=0.0)
    processing_time_ms: int = field(default=0)

    @property
    def event_type(self) -> str:
        """Get the event type identifier."""
        return "spending_entry.ai_enhanced"

    def get_event_data(self) -> dict[str, Any]:
        """Get the event data payload."""
        return {
            "entry_id": self.entry_id,
            "ai_model": self.ai_model,
            "confidence_before": self.confidence_before,
            "confidence_after": self.confidence_after,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass(frozen=True)
class SpendingBatchProcessed(SpendingDomainEvent):
    """Event fired when a batch of spending entries is processed."""

    batch_id: str = field(default="")
    total_entries: int = field(default=0)
    successful_entries: int = field(default=0)
    failed_entries: int = field(default=0)
    processing_method: str = field(default="")

    @property
    def event_type(self) -> str:
        """Get the event type identifier."""
        return "spending_batch.processed"

    def get_event_data(self) -> dict[str, Any]:
        """Get the event data payload."""
        return {
            "batch_id": self.batch_id,
            "entry_id": self.entry_id,  # Representative entry from batch
            "total_entries": self.total_entries,
            "successful_entries": self.successful_entries,
            "failed_entries": self.failed_entries,
            "processing_method": self.processing_method,
        }
