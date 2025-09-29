"""Repository interfaces for domain layer."""

from .ai_model_repository import AIModelRepository
from .spending_repository import SpendingRepository

__all__ = [
    "AIModelRepository",
    "SpendingRepository",
]
