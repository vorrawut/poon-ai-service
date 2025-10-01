"""MongoDB implementation of category mapping repository."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

import structlog
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError

from ...domain.entities.category_mapping import (
    CategoryMapping,
    CategoryMappingId,
    MappingCandidate,
    MappingStatus,
    MappingType,
)
from ...domain.repositories.category_mapping_repository import CategoryMappingRepository

logger = structlog.get_logger(__name__)


class MongoCategoryMappingRepository(CategoryMappingRepository):
    """MongoDB implementation of category mapping repository."""

    def __init__(self, client: Any, database_name: str) -> None:
        """Initialize repository with database connection."""
        self._client = client
        self._db = client[database_name]
        self._mappings: AsyncIOMotorCollection[
            dict[str, Any]
        ] = self._db.category_mappings
        self._candidates: AsyncIOMotorCollection[
            dict[str, Any]
        ] = self._db.mapping_candidates

    async def initialize(self) -> None:
        """Initialize database indexes and collections."""
        try:
            # Mappings collection indexes
            await self._mappings.create_index(
                [("key", ASCENDING), ("language", ASCENDING)]
            )
            await self._mappings.create_index([("target_category", ASCENDING)])
            await self._mappings.create_index([("status", ASCENDING)])
            await self._mappings.create_index([("mapping_type", ASCENDING)])
            await self._mappings.create_index([("language", ASCENDING)])
            await self._mappings.create_index([("priority", DESCENDING)])
            await self._mappings.create_index([("usage_count", DESCENDING)])
            await self._mappings.create_index([("last_used", DESCENDING)])
            await self._mappings.create_index([("created_at", DESCENDING)])

            # Text search index for aliases and patterns
            await self._mappings.create_index(
                [("key", TEXT), ("aliases", TEXT), ("target_category", TEXT)]
            )

            # Candidates collection indexes
            await self._candidates.create_index([("status", ASCENDING)])
            await self._candidates.create_index([("original_text", ASCENDING)])
            await self._candidates.create_index([("language", ASCENDING)])
            await self._candidates.create_index([("created_at", DESCENDING)])
            await self._candidates.create_index([("attempt_count", ASCENDING)])

            logger.info("Category mapping repository initialized with indexes")

        except Exception as e:
            logger.error(f"Failed to initialize category mapping repository: {e}")
            raise

    # Abstract method implementations (required by base class)
    async def save(self, mapping: CategoryMapping) -> CategoryMapping:
        """Save or update a category mapping (abstract method implementation)."""
        await self.save_mapping(mapping)
        return mapping

    async def find_all(
        self,
        language: str | None = None,
        mapping_type: MappingType | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CategoryMapping]:
        """Find all mappings with filters (abstract method implementation)."""
        try:
            query = {}
            if language:
                query["language"] = language
            if mapping_type:
                query["mapping_type"] = mapping_type.value
            if is_active is not None:
                query["status"] = (
                    MappingStatus.ACTIVE.value
                    if is_active
                    else MappingStatus.DEPRECATED.value
                )

            cursor = (
                self._mappings.find(query)
                .sort("priority", DESCENDING)
                .skip(offset)
                .limit(limit)
            )

            mappings = []
            async for doc in cursor:
                mappings.append(CategoryMapping.from_dict(doc))

            return mappings
        except Exception as e:
            logger.error(f"Failed to find all mappings: {e}")
            raise

    async def delete(self, mapping_id: CategoryMappingId) -> None:
        """Delete mapping by ID (abstract method implementation)."""
        result = await self.delete_mapping(mapping_id)
        if not result:
            logger.warning(f"No mapping found with ID {mapping_id}")

    async def count_mappings(
        self,
        language: str | None = None,
        mapping_type: MappingType | None = None,
        is_active: bool | None = None,
    ) -> int:
        """Count mappings with filters (abstract method implementation)."""
        try:
            query = {}
            if language:
                query["language"] = language
            if mapping_type:
                query["mapping_type"] = mapping_type.value
            if is_active is not None:
                query["status"] = (
                    MappingStatus.ACTIVE.value
                    if is_active
                    else MappingStatus.DEPRECATED.value
                )

            return await self._mappings.count_documents(query)
        except Exception as e:
            logger.error(f"Failed to count mappings: {e}")
            raise

    async def save_mapping(self, mapping: CategoryMapping) -> None:
        """Save or update a category mapping."""
        try:
            mapping_dict = mapping.to_dict()

            # Use upsert to handle both create and update
            await self._mappings.replace_one(
                {"id": mapping.id.value}, mapping_dict, upsert=True
            )

            logger.debug(f"Saved mapping: {mapping.key} -> {mapping.target_category}")

        except DuplicateKeyError as e:
            logger.warning(f"Duplicate mapping key: {mapping.key}")
            raise ValueError(f"Mapping with key '{mapping.key}' already exists") from e
        except Exception as e:
            logger.error(f"Failed to save mapping {mapping.id}: {e}")
            raise

    async def get_by_id(self, mapping_id: CategoryMappingId) -> CategoryMapping | None:
        """Find mapping by ID."""
        try:
            doc = await self._mappings.find_one({"id": mapping_id.value})
            return CategoryMapping.from_dict(doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to find mapping by ID {mapping_id}: {e}")
            return None

    async def find_by_key(
        self, key: str, language: str, mapping_type: MappingType = MappingType.CATEGORY
    ) -> list[CategoryMapping]:
        """Find mapping by exact key match."""
        try:
            cursor = self._mappings.find(
                {
                    "key": key.lower().strip(),
                    "language": language,
                    "mapping_type": mapping_type.value,
                    "status": MappingStatus.ACTIVE.value,
                }
            )
            docs = await cursor.to_list(length=None)
            return [CategoryMapping.from_dict(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to find mapping by key {key}: {e}")
            return []

    async def find_by_text(
        self, text: str, language: str = "en", limit: int = 10
    ) -> list[CategoryMapping]:
        """Find mappings that could match the given text."""
        try:
            text_lower = text.lower().strip()

            # Build query for multiple matching strategies
            query = {
                "language": language,
                "status": MappingStatus.ACTIVE.value,
                "$or": [
                    {"key": text_lower},  # Exact key match
                    {"aliases": {"$in": [text_lower]}},  # Alias match
                    {"$text": {"$search": text_lower}},  # Text search
                ],
            }

            # Add pattern matching for entries with patterns
            pattern_conditions: list[dict[str, Any]] = []
            async for doc in self._mappings.find(
                {
                    "patterns": {"$exists": True, "$ne": []},
                    "language": language,
                    "status": MappingStatus.ACTIVE.value,
                }
            ):
                for pattern in doc.get("patterns", []):
                    try:
                        if re.search(pattern, text, re.IGNORECASE):
                            pattern_conditions.append({"id": doc["id"]})
                    except re.error:
                        continue

            if pattern_conditions:
                query["$or"].extend(pattern_conditions)

            cursor = (
                self._mappings.find(query).sort("priority", DESCENDING).limit(limit)
            )
            docs = await cursor.to_list(length=limit)

            return [CategoryMapping.from_dict(doc) for doc in docs]

        except Exception as e:
            logger.error(f"Failed to find mappings by text '{text}': {e}")
            return []

    async def search_mappings(
        self,
        query: str | None = None,
        mapping_type: MappingType | None = None,
        language: str | None = None,
        status: MappingStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CategoryMapping]:
        """Search mappings with filters."""
        try:
            filter_dict: dict[str, Any] = {}

            if query:
                filter_dict["$text"] = {"$search": query}
            if mapping_type:
                filter_dict["mapping_type"] = mapping_type.value
            if language:
                filter_dict["language"] = language
            if status:
                filter_dict["status"] = status.value

            cursor = (
                self._mappings.find(filter_dict)
                .sort("priority", DESCENDING)
                .skip(offset)
                .limit(limit)
            )

            docs = await cursor.to_list(length=limit)
            return [CategoryMapping.from_dict(doc) for doc in docs]

        except Exception as e:
            logger.error(f"Failed to search mappings: {e}")
            return []

    async def get_all_active_mappings(
        self, language: str | None = None
    ) -> list[CategoryMapping]:
        """Get all active mappings, optionally filtered by language."""
        try:
            filter_dict = {"status": MappingStatus.ACTIVE.value}
            if language:
                filter_dict["language"] = language

            cursor = self._mappings.find(filter_dict).sort("priority", DESCENDING)
            docs = await cursor.to_list(length=None)

            return [CategoryMapping.from_dict(doc) for doc in docs]

        except Exception as e:
            logger.error(f"Failed to get active mappings: {e}")
            return []

    async def delete_mapping(self, mapping_id: CategoryMappingId) -> bool:
        """Delete a mapping by ID."""
        try:
            result = await self._mappings.delete_one({"id": mapping_id.value})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete mapping {mapping_id}: {e}")
            return False

    async def update_usage_stats(
        self, mapping_id: CategoryMappingId, success: bool
    ) -> None:
        """Update usage statistics for a mapping."""
        try:
            # Get current mapping to calculate new success rate
            mapping = await self.get_by_id(mapping_id)
            if not mapping:
                return

            mapping.update_usage_stats(success)
            await self.save_mapping(mapping)

        except Exception as e:
            logger.error(f"Failed to update usage stats for {mapping_id}: {e}")

    async def get_mappings_by_category(
        self, category: str, language: str = "en"
    ) -> list[CategoryMapping]:
        """Get all mappings for a specific category."""
        try:
            cursor = self._mappings.find(
                {
                    "target_category": category,
                    "language": language,
                    "status": MappingStatus.ACTIVE.value,
                }
            ).sort("priority", DESCENDING)

            docs = await cursor.to_list(length=None)
            return [CategoryMapping.from_dict(doc) for doc in docs]

        except Exception as e:
            logger.error(f"Failed to get mappings for category {category}: {e}")
            return []

    async def get_low_confidence_mappings(
        self, threshold: float = 0.7
    ) -> list[CategoryMapping]:
        """Get mappings with confidence below threshold."""
        try:
            cursor = self._mappings.find(
                {"confidence": {"$lt": threshold}, "status": MappingStatus.ACTIVE.value}
            ).sort("confidence", ASCENDING)

            docs = await cursor.to_list(length=None)
            return [CategoryMapping.from_dict(doc) for doc in docs]

        except Exception as e:
            logger.error(f"Failed to get low confidence mappings: {e}")
            return []

    async def get_unused_mappings(self, days: int = 30) -> list[CategoryMapping]:
        """Get mappings not used in the last N days."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            cursor = self._mappings.find(
                {
                    "$or": [{"last_used": {"$lt": cutoff_date}}, {"last_used": None}],
                    "status": MappingStatus.ACTIVE.value,
                }
            ).sort("last_used", ASCENDING)

            docs = await cursor.to_list(length=None)
            return [CategoryMapping.from_dict(doc) for doc in docs]

        except Exception as e:
            logger.error(f"Failed to get unused mappings: {e}")
            return []

    # Mapping candidates methods
    async def save_candidate(self, candidate: MappingCandidate) -> None:
        """Save a mapping candidate for review."""
        try:
            candidate_dict = candidate.to_dict()

            await self._candidates.replace_one(
                {"id": candidate.id.value}, candidate_dict, upsert=True
            )

            logger.debug(f"Saved candidate: {candidate.original_text}")

        except Exception as e:
            logger.error(f"Failed to save candidate {candidate.id}: {e}")
            raise

    async def find_candidate_by_id(
        self, candidate_id: CategoryMappingId
    ) -> MappingCandidate | None:
        """Find candidate by ID."""
        try:
            doc = await self._candidates.find_one({"id": candidate_id.value})
            return MappingCandidate.from_dict(doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to find candidate by ID {candidate_id}: {e}")
            return None

    async def get_pending_candidates(
        self, limit: int = 50, offset: int = 0
    ) -> list[MappingCandidate]:
        """Get candidates pending review."""
        try:
            cursor = (
                self._candidates.find({"status": MappingStatus.PENDING_REVIEW.value})
                .sort("created_at", ASCENDING)
                .skip(offset)
                .limit(limit)
            )

            docs = await cursor.to_list(length=limit)
            return [MappingCandidate.from_dict(doc) for doc in docs]

        except Exception as e:
            logger.error(f"Failed to get pending candidates: {e}")
            return []

    async def find_similar_candidates(
        self, text: str, language: str = "en", limit: int = 5
    ) -> list[MappingCandidate]:
        """Find similar candidates for the given text."""
        try:
            text_lower = text.lower().strip()

            cursor = (
                self._candidates.find(
                    {
                        "$or": [
                            {
                                "original_text": {
                                    "$regex": re.escape(text_lower),
                                    "$options": "i",
                                }
                            },
                            {
                                "normalized_text": {
                                    "$regex": re.escape(text_lower),
                                    "$options": "i",
                                }
                            },
                        ],
                        "language": language,
                    }
                )
                .sort("created_at", DESCENDING)
                .limit(limit)
            )

            docs = await cursor.to_list(length=limit)
            return [MappingCandidate.from_dict(doc) for doc in docs]

        except Exception as e:
            logger.error(f"Failed to find similar candidates: {e}")
            return []

    async def update_candidate_status(
        self, candidate_id: CategoryMappingId, status: MappingStatus
    ) -> None:
        """Update candidate status."""
        try:
            await self._candidates.update_one(
                {"id": candidate_id.value},
                {
                    "$set": {
                        "status": status.value,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                },
            )
        except Exception as e:
            logger.error(f"Failed to update candidate status {candidate_id}: {e}")

    async def get_candidate_stats(self) -> dict[str, Any]:
        """Get statistics about mapping candidates."""
        try:
            pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]

            cursor = self._candidates.aggregate(pipeline)
            stats = {doc["_id"]: doc["count"] async for doc in cursor}

            # Get total count
            total = await self._candidates.count_documents({})
            stats["total"] = total

            return stats

        except Exception as e:
            logger.error(f"Failed to get candidate stats: {e}")
            return {}

    async def find_candidates_for_review(self, limit: int = 100) -> list[Any]:
        """Find mapping candidates that need review."""
        try:
            cursor = (
                self._candidates.find({"status": "pending"})
                .sort("created_at", -1)
                .limit(limit)
            )
            candidates = []
            async for doc in cursor:
                doc["id"] = doc.pop("_id")
                from ...domain.entities.category_mapping import MappingCandidate

                candidates.append(MappingCandidate.from_dict(doc))
            return candidates
        except Exception as e:
            logger.error(f"Failed to find candidates for review: {e}")
            return []

    async def get_candidate_by_id(self, candidate_id: Any) -> Any | None:
        """Get a mapping candidate by ID."""
        try:
            data = await self._candidates.find_one({"_id": str(candidate_id)})
            if data:
                data["id"] = data.pop("_id")
                from ...domain.entities.category_mapping import MappingCandidate

                return MappingCandidate.from_dict(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get candidate by ID '{candidate_id}': {e}")
            return None

    async def approve_candidate(self, candidate_id: Any) -> None:
        """Mark a candidate as approved."""
        try:
            from datetime import datetime

            await self._candidates.update_one(
                {"_id": str(candidate_id)},
                {
                    "$set": {
                        "status": "approved",
                        "reviewed_at": datetime.utcnow().isoformat(),
                    }
                },
            )
            logger.info(f"Approved candidate {candidate_id}")
        except Exception as e:
            logger.error(f"Failed to approve candidate {candidate_id}: {e}")
            raise

    async def reject_candidate(self, candidate_id: Any) -> None:
        """Mark a candidate as rejected."""
        try:
            from datetime import datetime

            await self._candidates.update_one(
                {"_id": str(candidate_id)},
                {
                    "$set": {
                        "status": "rejected",
                        "reviewed_at": datetime.utcnow().isoformat(),
                    }
                },
            )
            logger.info(f"Rejected candidate {candidate_id}")
        except Exception as e:
            logger.error(f"Failed to reject candidate {candidate_id}: {e}")
            raise

    # Bulk operations
    async def bulk_create_mappings(self, mappings: list[CategoryMapping]) -> int:
        """Bulk create mappings, returns count of created mappings."""
        try:
            if not mappings:
                return 0

            mapping_dicts = [mapping.to_dict() for mapping in mappings]
            result = await self._mappings.insert_many(mapping_dicts, ordered=False)

            return len(result.inserted_ids)

        except Exception as e:
            logger.error(f"Failed to bulk create mappings: {e}")
            return 0

    async def bulk_update_mappings(self, mappings: list[CategoryMapping]) -> int:
        """Bulk update mappings, returns count of updated mappings."""
        try:
            if not mappings:
                return 0

            operations = []
            for mapping in mappings:
                operations.append(
                    {
                        "replaceOne": {
                            "filter": {"id": mapping.id.value},
                            "replacement": mapping.to_dict(),
                            "upsert": True,
                        }
                    }
                )

            result = await self._mappings.bulk_write(operations, ordered=False)
            return result.upserted_count + result.modified_count

        except Exception as e:
            logger.error(f"Failed to bulk update mappings: {e}")
            return 0

    # Analytics and insights
    async def get_mapping_analytics(self, days: int = 30) -> dict[str, Any]:
        """Get analytics about mapping usage and performance."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            pipeline = [
                {
                    "$match": {
                        "status": MappingStatus.ACTIVE.value,
                        "last_used": {"$gte": cutoff_date.isoformat()},
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_mappings": {"$sum": 1},
                        "total_usage": {"$sum": "$usage_count"},
                        "avg_confidence": {"$avg": "$confidence"},
                        "avg_success_rate": {"$avg": "$success_rate"},
                    }
                },
            ]

            cursor = self._mappings.aggregate(pipeline)
            result = await cursor.to_list(length=1)

            return result[0] if result else {}

        except Exception as e:
            logger.error(f"Failed to get mapping analytics: {e}")
            return {}

    async def get_popular_mappings(
        self, limit: int = 20, language: str | None = None
    ) -> list[CategoryMapping]:
        """Get most frequently used mappings."""
        try:
            filter_dict = {"status": MappingStatus.ACTIVE.value}
            if language:
                filter_dict["language"] = language

            cursor = (
                self._mappings.find(filter_dict)
                .sort("usage_count", DESCENDING)
                .limit(limit)
            )

            docs = await cursor.to_list(length=limit)
            return [CategoryMapping.from_dict(doc) for doc in docs]

        except Exception as e:
            logger.error(f"Failed to get popular mappings: {e}")
            return []

    async def get_category_distribution(
        self, language: str | None = None
    ) -> dict[str, int]:
        """Get distribution of mappings by category."""
        try:
            match_filter = {"status": MappingStatus.ACTIVE.value}
            if language:
                match_filter["language"] = language

            pipeline = [
                {"$match": match_filter},
                {"$group": {"_id": "$target_category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]

            cursor = self._mappings.aggregate(pipeline)
            return {doc["_id"]: doc["count"] async for doc in cursor}

        except Exception as e:
            logger.error(f"Failed to get category distribution: {e}")
            return {}

    # Cache management
    async def get_cache_version(self) -> str:
        """Get current cache version/timestamp for invalidation."""
        try:
            # Use the latest updated_at timestamp as cache version
            cursor = self._mappings.find({}).sort("updated_at", DESCENDING).limit(1)
            docs = await cursor.to_list(length=1)

            if docs:
                return docs[0].get("updated_at", datetime.utcnow().isoformat())
            else:
                return datetime.utcnow().isoformat()

        except Exception as e:
            logger.error(f"Failed to get cache version: {e}")
            return datetime.utcnow().isoformat()

    async def cleanup_old_data(self, days: int = 365) -> int:
        """Clean up old mapping data, returns count of deleted items."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Clean up old rejected candidates
            result = await self._candidates.delete_many(
                {
                    "status": MappingStatus.REJECTED.value,
                    "updated_at": {"$lt": cutoff_date.isoformat()},
                }
            )

            deleted_count = result.deleted_count
            logger.info(f"Cleaned up {deleted_count} old mapping candidates")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0
