"""MongoDB implementation of AI training repository."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import structlog
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from pymongo.errors import PyMongoError

from ...core.config.settings import Settings
from ...domain.entities.ai_training_data import (
    AITrainingData,
    AITrainingDataId,
    ProcessingStatus,
)
from ...domain.repositories.ai_training_repository import AITrainingRepository

logger = structlog.get_logger(__name__)


class MongoDBTrainingRepository(AITrainingRepository):
    """MongoDB implementation of AI training repository."""

    def __init__(self, settings: Settings) -> None:
        """Initialize MongoDB training repository."""
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
                authSource=self.settings.get_mongodb_database(),
                username=self.settings.mongodb_username,
                password=self.settings.mongodb_password,
            )

            # Test connection
            await self._client.admin.command("ping")
            logger.info("Successfully connected to MongoDB for AI training")

            self._database = self._client[self.settings.get_mongodb_database()]
            self._collection = self._database["ai_training_data"]

            # Create indexes for better performance
            await self._ensure_indexes()

        except Exception as e:
            logger.error(f"Failed to initialize MongoDB training connection: {e}")
            raise

    async def close(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            logger.info("MongoDB training connection closed")

    async def _ensure_indexes(self) -> None:
        """Ensure required indexes exist."""
        if self._collection is None:
            return

        # Indexes are created by the MongoDB init script
        # Skip verification to avoid authentication issues during startup
        logger.info("MongoDB AI training indexes assumed to be created by init script")

    def _training_data_to_document(
        self, training_data: AITrainingData
    ) -> dict[str, Any]:
        """Convert AITrainingData to MongoDB document."""
        return training_data.to_dict()

    def _document_to_training_data(self, document: dict[str, Any]) -> AITrainingData:
        """Convert MongoDB document to AITrainingData."""
        return AITrainingData.from_dict(document)

    async def save(self, training_data: AITrainingData) -> None:
        """Save AI training data."""
        if self._collection is None:
            raise RuntimeError("Repository not initialized")

        document = self._training_data_to_document(training_data)

        try:
            # Use upsert to handle both insert and update
            await self._collection.replace_one(
                {"id": training_data.id.value}, document, upsert=True
            )
            logger.debug(f"Saved AI training data: {training_data.id.value}")

        except PyMongoError as e:
            logger.error(f"Failed to save training data {training_data.id.value}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def find_by_id(self, training_id: AITrainingDataId) -> AITrainingData | None:
        """Find training data by ID."""
        if self._collection is None:
            raise RuntimeError("Repository not initialized")

        try:
            document = await self._collection.find_one({"id": training_id.value})
            if document:
                return self._document_to_training_data(document)
            return None

        except PyMongoError as e:
            logger.error(f"Failed to find training data {training_id.value}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def find_by_status(
        self, status: ProcessingStatus, limit: int = 100, offset: int = 0
    ) -> list[AITrainingData]:
        """Find training data by processing status."""
        if self._collection is None:
            raise RuntimeError("Repository not initialized")

        try:
            cursor = (
                self._collection.find({"status": status.value})
                .skip(offset)
                .limit(limit)
            )
            documents = await cursor.to_list(length=limit)
            return [self._document_to_training_data(doc) for doc in documents]

        except PyMongoError as e:
            logger.error(f"Failed to find training data by status {status}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def find_failed_cases(
        self, limit: int = 100, offset: int = 0
    ) -> list[AITrainingData]:
        """Find failed processing cases for review."""
        if self._collection is None:
            raise RuntimeError("Repository not initialized")

        try:
            failed_statuses = [
                ProcessingStatus.FAILED_VALIDATION.value,
                ProcessingStatus.FAILED_PARSING.value,
                ProcessingStatus.FAILED_MAPPING.value,
            ]

            cursor = (
                self._collection.find({"status": {"$in": failed_statuses}})
                .skip(offset)
                .limit(limit)
                .sort("created_at", -1)
            )

            documents = await cursor.to_list(length=limit)
            return [self._document_to_training_data(doc) for doc in documents]

        except PyMongoError as e:
            logger.error(f"Failed to find failed cases: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def find_by_language(
        self, language: str, limit: int = 100, offset: int = 0
    ) -> list[AITrainingData]:
        """Find training data by language."""
        if self._collection is None:
            raise RuntimeError("Repository not initialized")

        try:
            cursor = (
                self._collection.find({"language": language}).skip(offset).limit(limit)
            )
            documents = await cursor.to_list(length=limit)
            return [self._document_to_training_data(doc) for doc in documents]

        except PyMongoError as e:
            logger.error(f"Failed to find training data by language {language}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def find_low_accuracy_cases(
        self, accuracy_threshold: float = 0.7, limit: int = 100, offset: int = 0
    ) -> list[AITrainingData]:
        """Find cases with low accuracy scores."""
        if self._collection is None:
            raise RuntimeError("Repository not initialized")

        try:
            cursor = (
                self._collection.find(
                    {"accuracy_score": {"$lt": accuracy_threshold, "$ne": None}}
                )
                .skip(offset)
                .limit(limit)
                .sort("accuracy_score", 1)
            )

            documents = await cursor.to_list(length=limit)
            return [self._document_to_training_data(doc) for doc in documents]

        except PyMongoError as e:
            logger.error(f"Failed to find low accuracy cases: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def get_accuracy_stats(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> dict[str, Any]:
        """Get accuracy statistics over time."""
        if self._collection is None:
            raise RuntimeError("Repository not initialized")

        try:
            match_filter = {}
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                match_filter["created_at"] = date_filter

            pipeline: list[dict[str, Any]] = [
                {"$match": match_filter},
                {
                    "$group": {
                        "_id": None,
                        "total_cases": {"$sum": 1},
                        "avg_accuracy": {"$avg": "$accuracy_score"},
                        "avg_confidence": {"$avg": "$ai_confidence"},
                        "success_rate": {
                            "$avg": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
                        },
                        "avg_processing_time": {"$avg": "$processing_time_ms"},
                    }
                },
            ]

            result = await self._collection.aggregate(pipeline).to_list(length=1)
            if result:
                stats: dict[str, Any] = result[0]
                stats.pop("_id", None)
                return stats

            return {
                "total_cases": 0,
                "avg_accuracy": 0.0,
                "avg_confidence": 0.0,
                "success_rate": 0.0,
                "avg_processing_time": 0.0,
            }

        except PyMongoError as e:
            logger.error(f"Failed to get accuracy stats: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def get_category_mapping_insights(self) -> dict[str, str]:
        """Get learned category mappings from feedback."""
        if self._collection is None:
            raise RuntimeError("Repository not initialized")

        try:
            pipeline: list[dict[str, Any]] = [
                {"$match": {"category_mapping_learned": {"$ne": {}}}},
                {"$group": {"_id": "$category_mapping_learned", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]

            results = await self._collection.aggregate(pipeline).to_list(length=100)

            # Flatten the mappings
            category_mappings = {}
            for result in results:
                mappings = result["_id"]
                if isinstance(mappings, dict):
                    category_mappings.update(mappings)

            return category_mappings

        except PyMongoError as e:
            logger.error(f"Failed to get category mapping insights: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def get_common_error_patterns(self) -> list[dict[str, Any]]:
        """Get common error patterns for model improvement."""
        if self._collection is None:
            raise RuntimeError("Repository not initialized")

        try:
            pipeline: list[dict[str, Any]] = [
                {"$match": {"validation_errors": {"$ne": []}}},
                {"$unwind": "$validation_errors"},
                {
                    "$group": {
                        "_id": "$validation_errors",
                        "count": {"$sum": 1},
                        "languages": {"$addToSet": "$language"},
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 50},
            ]

            results = await self._collection.aggregate(pipeline).to_list(length=50)
            return [
                {
                    "error_pattern": result["_id"],
                    "frequency": result["count"],
                    "languages": result["languages"],
                }
                for result in results
            ]

        except PyMongoError as e:
            logger.error(f"Failed to get error patterns: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def find_similar_inputs(
        self, input_text: str, language: str, limit: int = 10
    ) -> list[AITrainingData]:
        """Find similar input texts for learning."""
        if self._collection is None:
            raise RuntimeError("Repository not initialized")

        try:
            # Simple text similarity using regex (can be enhanced with vector search)
            words = input_text.lower().split()[:5]  # Use first 5 words
            regex_pattern = "|".join(words)

            cursor = (
                self._collection.find(
                    {
                        "language": language,
                        "input_text": {"$regex": regex_pattern, "$options": "i"},
                    }
                )
                .limit(limit)
                .sort("created_at", -1)
            )

            documents = await cursor.to_list(length=limit)
            return [self._document_to_training_data(doc) for doc in documents]

        except PyMongoError as e:
            logger.error(f"Failed to find similar inputs: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def count_by_status(self) -> dict[str, int]:
        """Count training data by status."""
        if self._collection is None:
            raise RuntimeError("Repository not initialized")

        try:
            pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]

            results = await self._collection.aggregate(pipeline).to_list(length=10)
            return {result["_id"]: result["count"] for result in results}

        except PyMongoError as e:
            logger.error(f"Failed to count by status: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    async def delete_old_data(self, older_than_days: int = 365) -> int:
        """Delete old training data (returns count deleted)."""
        if self._collection is None:
            raise RuntimeError("Repository not initialized")

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            result = await self._collection.delete_many(
                {"created_at": {"$lt": cutoff_date}}
            )

            logger.info(f"Deleted {result.deleted_count} old training records")
            return result.deleted_count

        except PyMongoError as e:
            logger.error(f"Failed to delete old data: {e}")
            raise RuntimeError(f"Database error: {e}") from e
