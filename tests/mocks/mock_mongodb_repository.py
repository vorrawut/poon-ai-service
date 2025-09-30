"""Mock MongoDB repository for testing without requiring a real MongoDB instance."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ai_service.core.config.settings import Settings
from ai_service.domain.entities.spending_entry import SpendingEntry, SpendingEntryId
from ai_service.domain.repositories.spending_repository import SpendingRepository

logger = logging.getLogger(__name__)


class MockMongoDBSpendingRepository(SpendingRepository):
    """In-memory mock implementation of MongoDB repository for testing."""

    def __init__(self, settings: Settings) -> None:
        """Initialize mock repository."""
        self.settings = settings
        self._data: dict[str, dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize mock repository."""
        self._initialized = True
        logger.info("Mock MongoDB repository initialized")

    async def close(self) -> None:
        """Close mock repository."""
        self._data.clear()
        self._initialized = False
        logger.info("Mock MongoDB repository closed")

    def _spending_entry_to_document(self, entry: SpendingEntry) -> dict[str, Any]:
        """Convert SpendingEntry to document format."""
        return {
            "entry_id": entry.id.value,
            "amount": float(entry.amount.amount),
            "currency": entry.amount.currency.value,
            "merchant": entry.merchant,
            "description": entry.description,
            "category": entry.category.value,
            "payment_method": entry.payment_method.value,
            "transaction_date": entry.transaction_date,
            "processing_method": entry.processing_method.value
            if entry.processing_method
            else None,
            "confidence": float(entry.confidence.value) if entry.confidence else None,
            "created_at": entry.created_at,
            "updated_at": entry.updated_at,
        }

    def _document_to_spending_entry(self, document: dict[str, Any]) -> SpendingEntry:
        """Convert document to SpendingEntry."""
        from ai_service.domain.value_objects.confidence import ConfidenceScore
        from ai_service.domain.value_objects.money import Currency, Money
        from ai_service.domain.value_objects.processing_method import ProcessingMethod
        from ai_service.domain.value_objects.spending_category import (
            PaymentMethod,
            SpendingCategory,
        )

        # Create Money object
        currency = Currency(document["currency"])
        amount = Money.from_float(document["amount"], currency)

        # Create other value objects
        category = SpendingCategory(document["category"])
        payment_method = PaymentMethod(document["payment_method"])

        processing_method = None
        if document.get("processing_method"):
            processing_method = ProcessingMethod(document["processing_method"])

        confidence = None
        if document.get("confidence") is not None:
            confidence = ConfidenceScore(document["confidence"])

        return SpendingEntry(
            id=SpendingEntryId(document["entry_id"]),
            amount=amount,
            merchant=document["merchant"],
            description=document["description"],
            category=category,
            payment_method=payment_method,
            transaction_date=document["transaction_date"],
            processing_method=processing_method,
            confidence=confidence,
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )

    async def save(self, entry: SpendingEntry) -> None:
        """Save a spending entry."""
        if not self._initialized:
            raise RuntimeError("Repository not initialized")

        document = self._spending_entry_to_document(entry)
        self._data[entry.id.value] = document
        logger.debug(f"Saved spending entry: {entry.id.value}")

    async def find_by_id(self, entry_id: SpendingEntryId) -> SpendingEntry | None:
        """Find a spending entry by ID."""
        if not self._initialized:
            raise RuntimeError("Repository not initialized")

        document = self._data.get(entry_id.value)
        if document:
            return self._document_to_spending_entry(document)
        return None

    async def find_all(
        self,
        limit: int = 100,
        offset: int = 0,
        category: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[SpendingEntry]:
        """Find spending entries with optional filtering."""
        if not self._initialized:
            raise RuntimeError("Repository not initialized")

        # Filter documents
        filtered_docs = []
        for doc in self._data.values():
            if category and doc["category"] != category:
                continue
            if date_from and doc["transaction_date"] < date_from:
                continue
            if date_to and doc["transaction_date"] > date_to:
                continue
            filtered_docs.append(doc)

        # Sort by created_at descending
        filtered_docs.sort(key=lambda x: x["created_at"], reverse=True)

        # Apply pagination
        paginated_docs = filtered_docs[offset : offset + limit]

        return [self._document_to_spending_entry(doc) for doc in paginated_docs]

    async def delete(self, entry_id: SpendingEntryId) -> bool:
        """Delete a spending entry by ID."""
        if not self._initialized:
            raise RuntimeError("Repository not initialized")

        if entry_id.value in self._data:
            del self._data[entry_id.value]
            logger.debug(f"Deleted spending entry: {entry_id.value}")
            return True
        return False

    async def exists(self, entry_id: SpendingEntryId) -> bool:
        """Check if a spending entry exists."""
        if not self._initialized:
            raise RuntimeError("Repository not initialized")

        return entry_id.value in self._data

    async def count_total(self) -> int:
        """Count total number of spending entries."""
        if not self._initialized:
            raise RuntimeError("Repository not initialized")

        return len(self._data)

    async def count_by_category(self, category) -> int:
        """Count spending entries by category."""
        if not self._initialized:
            raise RuntimeError("Repository not initialized")

        category_str = category.value if hasattr(category, "value") else str(category)
        return sum(1 for doc in self._data.values() if doc["category"] == category_str)

    async def find_by_category(
        self, category, limit: int = 100, offset: int = 0
    ) -> list[SpendingEntry]:
        """Find spending entries by category."""
        category_str = category.value if hasattr(category, "value") else str(category)
        return await self.find_all(limit=limit, offset=offset, category=category_str)

    async def find_by_merchant(
        self, merchant: str, limit: int = 100, offset: int = 0
    ) -> list[SpendingEntry]:
        """Find spending entries by merchant name."""
        if not self._initialized:
            raise RuntimeError("Repository not initialized")

        # Filter documents by merchant
        filtered_docs = []
        for doc in self._data.values():
            if merchant.lower() in doc["merchant"].lower():
                filtered_docs.append(doc)

        # Sort by created_at descending
        filtered_docs.sort(key=lambda x: x["created_at"], reverse=True)

        # Apply pagination
        paginated_docs = filtered_docs[offset : offset + limit]

        return [self._document_to_spending_entry(doc) for doc in paginated_docs]

    async def search_by_text(
        self, search_text: str, limit: int = 100, offset: int = 0
    ) -> list[SpendingEntry]:
        """Search spending entries by text in merchant or description."""
        if not self._initialized:
            raise RuntimeError("Repository not initialized")

        search_lower = search_text.lower()

        # Filter documents by text search
        filtered_docs = []
        for doc in self._data.values():
            if (
                search_lower in doc["merchant"].lower()
                or search_lower in doc["description"].lower()
            ):
                filtered_docs.append(doc)

        # Sort by created_at descending
        filtered_docs.sort(key=lambda x: x["created_at"], reverse=True)

        # Apply pagination
        paginated_docs = filtered_docs[offset : offset + limit]

        return [self._document_to_spending_entry(doc) for doc in paginated_docs]

    async def find_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 100
    ) -> list[SpendingEntry]:
        """Find spending entries within a date range."""
        return await self.find_all(limit=limit, date_from=start_date, date_to=end_date)

    async def get_categories(self) -> list[str]:
        """Get all unique categories."""
        if not self._initialized:
            raise RuntimeError("Repository not initialized")

        categories = {doc["category"] for doc in self._data.values()}
        return sorted(categories)

    async def get_merchants(self) -> list[str]:
        """Get all unique merchants."""
        if not self._initialized:
            raise RuntimeError("Repository not initialized")

        merchants = {doc["merchant"] for doc in self._data.values()}
        return sorted(merchants)

    async def health_check(self) -> bool:
        """Check if the repository is healthy."""
        return self._initialized
