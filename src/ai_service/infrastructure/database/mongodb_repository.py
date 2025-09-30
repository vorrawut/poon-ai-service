"""MongoDB repository implementation for spending entries."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from pymongo.errors import DuplicateKeyError, PyMongoError

from ...core.config.settings import Settings
from ...domain.entities.spending_entry import SpendingEntry, SpendingEntryId
from ...domain.repositories.spending_repository import SpendingRepository

logger = logging.getLogger(__name__)


class MongoDBSpendingRepository(SpendingRepository):
    """MongoDB implementation of the spending repository."""

    def __init__(self, settings: Settings) -> None:
        """Initialize MongoDB repository."""
        self.settings = settings
        self._client: AsyncIOMotorClient[Any] | None = None
        self._database: AsyncIOMotorDatabase[Any] | None = None
        self._collection: AsyncIOMotorCollection[Any] | None = None

    async def initialize(self) -> None:
        """Initialize MongoDB connection and ensure indexes."""
        try:
            self._client = AsyncIOMotorClient(
                self.settings.get_mongodb_url(),
                serverSelectionTimeoutMS=self.settings.mongodb_timeout * 1000,
            )

            # Test connection
            await self._client.admin.command("ping")
            logger.info("Successfully connected to MongoDB")

            self._database = self._client[self.settings.get_mongodb_database()]
            self._collection = self._database[self.settings.mongodb_collection]

            # Create indexes for better performance
            await self._ensure_indexes()

        except Exception as e:
            logger.error(f"Failed to initialize MongoDB connection: {e}")
            raise

    async def _ensure_indexes(self) -> None:
        """Ensure required indexes exist."""
        if not self._collection:
            return

        try:
            # Create unique index on entry_id
            await self._collection.create_index("entry_id", unique=True)

            # Create indexes for common query patterns
            await self._collection.create_index("category")
            await self._collection.create_index("merchant")
            await self._collection.create_index("transaction_date")
            await self._collection.create_index("created_at")

            # Compound index for date range queries
            await self._collection.create_index(
                [("transaction_date", 1), ("category", 1)]
            )

            logger.info("MongoDB indexes created successfully")

        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")

    async def close(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")

    def _spending_entry_to_document(self, entry: SpendingEntry) -> dict[str, Any]:
        """Convert SpendingEntry to MongoDB document."""
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
        """Convert MongoDB document to SpendingEntry."""
        from ...domain.value_objects.confidence import ConfidenceScore
        from ...domain.value_objects.money import Currency, Money
        from ...domain.value_objects.processing_method import ProcessingMethod
        from ...domain.value_objects.spending_category import (
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
            processing_method=processing_method or ProcessingMethod.MANUAL_ENTRY,
            confidence=confidence or ConfidenceScore(0.5),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
        )

    async def save(self, entry: SpendingEntry) -> None:
        """Save a spending entry to MongoDB."""
        if not self._collection:
            raise RuntimeError("Repository not initialized")

        document = self._spending_entry_to_document(entry)

        try:
            # Use upsert to handle both insert and update
            await self._collection.replace_one(
                {"entry_id": entry.id.value}, document, upsert=True
            )
            logger.debug(f"Saved spending entry: {entry.id.value}")

        except DuplicateKeyError as e:
            logger.error(f"Duplicate entry ID: {entry.id.value}")
            raise ValueError(f"Entry with ID {entry.id.value} already exists") from e
        except PyMongoError as e:
            logger.error(f"Failed to save entry {entry.id.value}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def find_by_id(self, entry_id: SpendingEntryId) -> SpendingEntry | None:
        """Find a spending entry by ID."""
        if not self._collection:
            raise RuntimeError("Repository not initialized")

        try:
            document = await self._collection.find_one({"entry_id": entry_id.value})
            if document:
                return self._document_to_spending_entry(document)
            return None

        except PyMongoError as e:
            logger.error(f"Failed to find entry {entry_id.value}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def find_all(
        self,
        limit: int = 100,
        offset: int = 0,
        category: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[SpendingEntry]:
        """Find spending entries with optional filtering."""
        if not self._collection:
            raise RuntimeError("Repository not initialized")

        try:
            # Build query filter
            query_filter: dict[str, Any] = {}

            if category:
                query_filter["category"] = category

            if date_from or date_to:
                date_filter: dict[str, Any] = {}
                if date_from:
                    date_filter["$gte"] = date_from
                if date_to:
                    date_filter["$lte"] = date_to
                query_filter["transaction_date"] = date_filter

            # Execute query with pagination
            cursor = (
                self._collection.find(query_filter)
                .sort("created_at", -1)
                .skip(offset)
                .limit(limit)
            )
            documents = await cursor.to_list(length=limit)

            return [self._document_to_spending_entry(doc) for doc in documents]

        except PyMongoError as e:
            logger.error(f"Failed to find entries: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def delete(self, entry_id: SpendingEntryId) -> bool:
        """Delete a spending entry by ID."""
        if not self._collection:
            raise RuntimeError("Repository not initialized")

        try:
            result = await self._collection.delete_one({"entry_id": entry_id.value})
            deleted = result.deleted_count > 0

            if deleted:
                logger.debug(f"Deleted spending entry: {entry_id.value}")
            else:
                logger.debug(f"Entry not found for deletion: {entry_id.value}")

            return deleted

        except PyMongoError as e:
            logger.error(f"Failed to delete entry {entry_id.value}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def exists(self, entry_id: SpendingEntryId) -> bool:
        """Check if a spending entry exists."""
        if not self._collection:
            raise RuntimeError("Repository not initialized")

        try:
            count = await self._collection.count_documents(
                {"entry_id": entry_id.value}, limit=1
            )
            return count > 0

        except PyMongoError as e:
            logger.error(f"Failed to check existence of entry {entry_id.value}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def count_total(self) -> int:
        """Count total number of spending entries."""
        if not self._collection:
            raise RuntimeError("Repository not initialized")

        try:
            return await self._collection.count_documents({})

        except PyMongoError as e:
            logger.error(f"Failed to count entries: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def count_by_category(self, category: Any) -> int:
        """Count spending entries by category."""
        if not self._collection:
            raise RuntimeError("Repository not initialized")

        try:
            category_str = (
                category.value if hasattr(category, "value") else str(category)
            )
            return await self._collection.count_documents({"category": category_str})

        except PyMongoError as e:
            logger.error(f"Failed to count entries by category {category}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def find_by_category(
        self, category: Any, limit: int = 100, offset: int = 0
    ) -> list[SpendingEntry]:
        """Find spending entries by category."""
        category_str = category.value if hasattr(category, "value") else str(category)
        return await self.find_all(limit=limit, offset=offset, category=category_str)

    async def find_by_merchant(
        self, merchant: str, limit: int = 100, offset: int = 0
    ) -> list[SpendingEntry]:
        """Find spending entries by merchant name."""
        if not self._collection:
            raise RuntimeError("Repository not initialized")

        try:
            # Use regex for case-insensitive partial matching
            query_filter = {"merchant": {"$regex": merchant, "$options": "i"}}

            cursor = (
                self._collection.find(query_filter)
                .sort("created_at", -1)
                .skip(offset)
                .limit(limit)
            )
            documents = await cursor.to_list(length=limit)

            return [self._document_to_spending_entry(doc) for doc in documents]

        except PyMongoError as e:
            logger.error(f"Failed to find entries by merchant {merchant}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def search_by_text(
        self, search_text: str, limit: int = 100, offset: int = 0
    ) -> list[SpendingEntry]:
        """Search spending entries by text in merchant or description."""
        if not self._collection:
            raise RuntimeError("Repository not initialized")

        try:
            # Use regex for case-insensitive text search in merchant and description
            query_filter = {
                "$or": [
                    {"merchant": {"$regex": search_text, "$options": "i"}},
                    {"description": {"$regex": search_text, "$options": "i"}},
                ]
            }

            cursor = (
                self._collection.find(query_filter)
                .sort("created_at", -1)
                .skip(offset)
                .limit(limit)
            )
            documents = await cursor.to_list(length=limit)

            return [self._document_to_spending_entry(doc) for doc in documents]

        except PyMongoError as e:
            logger.error(f"Failed to search entries by text '{search_text}': {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SpendingEntry]:
        """Find spending entries within a date range."""
        return await self.find_all(
            limit=limit, offset=offset, date_from=start_date, date_to=end_date
        )

    async def get_categories(self) -> list[str]:
        """Get all unique categories."""
        if not self._collection:
            raise RuntimeError("Repository not initialized")

        try:
            categories = await self._collection.distinct("category")
            return sorted(categories)

        except PyMongoError as e:
            logger.error(f"Failed to get categories: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def get_merchants(self) -> list[str]:
        """Get all unique merchants."""
        if not self._collection:
            raise RuntimeError("Repository not initialized")

        try:
            merchants = await self._collection.distinct("merchant")
            return sorted(merchants)

        except PyMongoError as e:
            logger.error(f"Failed to get merchants: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        try:
            if not self._client:
                return False
            await self._client.admin.command("ping")
            return True
        except Exception:
            return False
