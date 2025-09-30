"""Base domain event classes."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DomainEvent(ABC):
    """
    Base class for all domain events.

    Domain events represent something important that happened in the domain
    that other parts of the system might want to know about.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_version: int = field(default=1)

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Get the event type identifier."""
        pass

    @abstractmethod
    def get_event_data(self) -> dict[str, Any]:
        """Get the event data payload."""
        pass

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "event_version": self.event_version,
            "event_data": self.get_event_data(),
        }

    def __str__(self) -> str:
        """String representation."""
        return f"{self.event_type}({self.event_id})"


@dataclass(frozen=True)
class SpendingDomainEvent:
    """Base class for spending-related domain events."""

    entry_id: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    event_version: int = field(default=1)

    @property
    def event_type(self) -> str:
        """Get the event type identifier."""
        return "base_spending_event"

    def get_event_data(self) -> dict[str, Any]:
        """Get the event data payload."""
        return {"entry_id": self.entry_id}

    def get_aggregate_id(self) -> str:
        """Get the aggregate root ID."""
        return self.entry_id

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "event_version": self.event_version,
            "event_data": self.get_event_data(),
        }
