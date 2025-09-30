"""Database infrastructure implementations."""

from .mongodb_repository import MongoDBSpendingRepository

__all__ = [
    "MongoDBSpendingRepository",
]
