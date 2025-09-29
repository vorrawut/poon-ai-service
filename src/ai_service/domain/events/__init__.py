"""Domain events for AI spending analysis service."""

from .base import DomainEvent
from .spending_events import (
    SpendingEntryCreated,
    SpendingEntryDeleted,
    SpendingEntryUpdated,
)

__all__ = [
    "DomainEvent",
    "SpendingEntryCreated",
    "SpendingEntryDeleted",
    "SpendingEntryUpdated",
]
