"""Advanced Redis caching layer for AI service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger(__name__)


@dataclass
class CacheConfig:
    """Configuration for cache behavior."""

    ttl: int = 3600  # Default TTL in seconds
    serialize_method: str = "json"  # json, pickle
    compress: bool = False
    namespace: str = "ai_service"


class RedisCache:
    """Advanced Redis caching with multiple serialization methods and compression."""

    def __init__(self, redis_client: Redis, config: CacheConfig = None) -> None:
        """Initialize Redis cache."""
        self.redis = redis_client
        self.config = config or CacheConfig()

    def _get_key(self, key: str) -> str:
        """Get namespaced cache key."""
        return f"{self.config.namespace}:{key}"

    def _serialize(self, value: Any) -> bytes:
        """Serialize value based on configuration."""
        if self.config.serialize_method == "json":
            serialized = json.dumps(value, default=str).encode()
        else:
            raise ValueError(
                f"Unsupported serialization method: {self.config.serialize_method}"
            )

        if self.config.compress:
            import gzip

            serialized = gzip.compress(serialized)

        return serialized

    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value based on configuration."""
        if self.config.compress:
            import gzip

            value = gzip.decompress(value)

        if self.config.serialize_method == "json":
            return json.loads(value.decode())
        else:
            raise ValueError(
                f"Unsupported serialization method: {self.config.serialize_method}"
            )

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        try:
            cache_key = self._get_key(key)
            value = await self.redis.get(cache_key)

            if value is None:
                return None

            return self._deserialize(value)

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache."""
        try:
            cache_key = self._get_key(key)
            serialized_value = self._serialize(value)
            ttl = ttl or self.config.ttl

            await self.redis.setex(cache_key, ttl, serialized_value)
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            cache_key = self._get_key(key)
            result = await self.redis.delete(cache_key)
            return result > 0

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            cache_key = self._get_key(key)
            result = await self.redis.exists(cache_key)
            return result > 0

        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for existing key."""
        try:
            cache_key = self._get_key(key)
            result = await self.redis.expire(cache_key, ttl)
            return result

        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        """Get TTL for key."""
        try:
            cache_key = self._get_key(key)
            return await self.redis.ttl(cache_key)

        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value."""
        try:
            cache_key = self._get_key(key)
            return await self.redis.incrby(cache_key, amount)

        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache."""
        try:
            cache_keys = [self._get_key(key) for key in keys]
            values = await self.redis.mget(cache_keys)

            result = {}
            for _i, (key, value) in enumerate(zip(keys, values, strict=False)):
                if value is not None:
                    try:
                        result[key] = self._deserialize(value)
                    except Exception as e:
                        logger.error(f"Deserialization error for key {key}: {e}")
                        result[key] = None
                else:
                    result[key] = None

            return result

        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return dict.fromkeys(keys)

    async def set_many(self, mapping: dict[str, Any], ttl: int | None = None) -> bool:
        """Set multiple values in cache."""
        try:
            pipe = self.redis.pipeline()
            ttl = ttl or self.config.ttl

            for key, value in mapping.items():
                cache_key = self._get_key(key)
                serialized_value = self._serialize(value)
                pipe.setex(cache_key, ttl, serialized_value)

            await pipe.execute()
            return True

        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        try:
            cache_pattern = self._get_key(pattern)
            keys = []

            async for key in self.redis.scan_iter(match=cache_pattern):
                keys.append(key)

            if keys:
                return await self.redis.delete(*keys)

            return 0

        except Exception as e:
            logger.error(f"Cache clear_pattern error for pattern {pattern}: {e}")
            return 0


class AICache:
    """High-level caching interface for AI service."""

    def __init__(self, redis_cache: RedisCache) -> None:
        """Initialize AI cache."""
        self.cache = redis_cache

    async def get_category_mappings(self) -> dict[str, str] | None:
        """Get cached category mappings."""
        return await self.cache.get("category_mappings")

    async def set_category_mappings(self, mappings: dict[str, str]) -> bool:
        """Cache category mappings."""
        return await self.cache.set(
            "category_mappings", mappings, ttl=900
        )  # 15 minutes

    async def get_ai_insights(self) -> dict[str, Any] | None:
        """Get cached AI insights."""
        return await self.cache.get("ai_insights")

    async def set_ai_insights(self, insights: dict[str, Any]) -> bool:
        """Cache AI insights."""
        return await self.cache.set("ai_insights", insights, ttl=300)  # 5 minutes

    async def get_model_performance(self, model_version: str) -> dict[str, Any] | None:
        """Get cached model performance data."""
        return await self.cache.get(f"model_performance:{model_version}")

    async def set_model_performance(
        self, model_version: str, performance: dict[str, Any]
    ) -> bool:
        """Cache model performance data."""
        return await self.cache.set(
            f"model_performance:{model_version}",
            performance,
            ttl=1800,  # 30 minutes
        )

    async def get_user_feedback_stats(self, user_id: str) -> dict[str, Any] | None:
        """Get cached user feedback statistics."""
        return await self.cache.get(f"user_feedback:{user_id}")

    async def set_user_feedback_stats(
        self, user_id: str, stats: dict[str, Any]
    ) -> bool:
        """Cache user feedback statistics."""
        return await self.cache.set(
            f"user_feedback:{user_id}", stats, ttl=3600
        )  # 1 hour

    async def increment_api_calls(self, endpoint: str) -> int:
        """Increment API call counter."""
        key = f"api_calls:{endpoint}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        count = await self.cache.increment(key)

        # Set expiration for hourly counters
        if count == 1:  # First increment, set expiration
            await self.cache.expire(
                f"api_calls:{endpoint}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}",
                7200,
            )  # 2 hours

        return count

    async def get_api_call_stats(
        self, endpoint: str, hours_back: int = 24
    ) -> dict[str, int]:
        """Get API call statistics for the last N hours."""
        now = datetime.utcnow()
        keys = []

        for i in range(hours_back):
            hour = now - timedelta(hours=i)
            keys.append(f"api_calls:{endpoint}:{hour.strftime('%Y-%m-%d-%H')}")

        results = await self.cache.get_many(keys)

        # Convert to hourly stats
        stats = {}
        for i, key in enumerate(keys):
            hour = (now - timedelta(hours=i)).strftime("%Y-%m-%d-%H")
            stats[hour] = results.get(key, 0) or 0

        return stats

    async def cache_similar_inputs(
        self, input_text: str, language: str, similar_cases: list[dict[str, Any]]
    ) -> bool:
        """Cache similar input cases for faster lookup."""
        import hashlib

        # Create hash of input for cache key
        input_hash = hashlib.sha256(f"{input_text}:{language}".encode()).hexdigest()
        key = f"similar_inputs:{input_hash}"

        return await self.cache.set(key, similar_cases, ttl=1800)  # 30 minutes

    async def get_similar_inputs(
        self, input_text: str, language: str
    ) -> list[dict[str, Any]] | None:
        """Get cached similar input cases."""
        import hashlib

        input_hash = hashlib.sha256(f"{input_text}:{language}".encode()).hexdigest()
        key = f"similar_inputs:{input_hash}"

        return await self.cache.get(key)

    async def clear_ai_caches(self) -> int:
        """Clear all AI-related caches."""
        patterns = [
            "category_mappings*",
            "ai_insights*",
            "model_performance*",
            "similar_inputs*",
        ]

        total_cleared = 0
        for pattern in patterns:
            cleared = await self.cache.clear_pattern(pattern)
            total_cleared += cleared

        logger.info(f"Cleared {total_cleared} AI cache entries")
        return total_cleared
