"""
Cache service for AI microservice
Simple in-memory cache for development, Redis for production
"""

import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class CacheService:
    """Simple cache service with in-memory fallback"""

    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url
        self.redis_client = None
        self.memory_cache: dict[str, dict[str, Any]] = {}
        self.default_ttl = 3600  # 1 hour

        # Try to initialize Redis if URL provided
        if redis_url:
            try:
                import redis

                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("✅ Redis cache connected")
            except Exception as e:
                logger.warning(
                    f"❌ Redis connection failed, using in-memory cache: {e!s}"
                )
                self.redis_client = None
        else:
            logger.info("📋 Using in-memory cache")

    def _generate_key(self, key: str) -> str:
        """Generate consistent cache key"""
        return hashlib.md5(key.encode()).hexdigest()

    async def get(self, key: str) -> dict[str, Any] | None:
        """Get value from cache"""
        cache_key = self._generate_key(key)

        try:
            if self.redis_client:
                # Try Redis first
                value = await self._get_from_redis(cache_key)
                if value:
                    return value

            # Fallback to memory cache
            return self._get_from_memory(cache_key)

        except Exception as e:
            logger.error(f"Cache get error: {e!s}")
            return None

    async def set(self, key: str, value: dict[str, Any], ttl: int = None) -> bool:
        """Set value in cache"""
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl

        try:
            if self.redis_client:
                # Try Redis first
                success = await self._set_to_redis(cache_key, value, ttl)
                if success:
                    return True

            # Fallback to memory cache
            return self._set_to_memory(cache_key, value, ttl)

        except Exception as e:
            logger.error(f"Cache set error: {e!s}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete from cache"""
        cache_key = self._generate_key(key)

        try:
            if self.redis_client:
                await self._delete_from_redis(cache_key)

            return self._delete_from_memory(cache_key)

        except Exception as e:
            logger.error(f"Cache delete error: {e!s}")
            return False

    async def clear(self) -> bool:
        """Clear all cache"""
        try:
            if self.redis_client:
                await self._clear_redis()

            self.memory_cache.clear()
            logger.info("Cache cleared")
            return True

        except Exception as e:
            logger.error(f"Cache clear error: {e!s}")
            return False

    async def close(self):
        """Close cache connections"""
        if self.redis_client:
            await self.redis_client.close()
        self.memory_cache.clear()

    # Redis methods
    async def _get_from_redis(self, key: str) -> dict[str, Any] | None:
        """Get from Redis"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value.decode())
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e!s}")
            return None

    async def _set_to_redis(self, key: str, value: dict[str, Any], ttl: int) -> bool:
        """Set to Redis"""
        try:
            serialized = json.dumps(value)
            return self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Redis set error: {e!s}")
            return False

    async def _delete_from_redis(self, key: str) -> bool:
        """Delete from Redis"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e!s}")
            return False

    async def _clear_redis(self) -> bool:
        """Clear Redis"""
        try:
            return self.redis_client.flushdb()
        except Exception as e:
            logger.error(f"Redis clear error: {e!s}")
            return False

    # Memory cache methods
    def _get_from_memory(self, key: str) -> dict[str, Any] | None:
        """Get from memory cache"""
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if time.time() < entry["expires_at"]:
                return entry["value"]
            else:
                # Expired, remove it
                del self.memory_cache[key]
        return None

    def _set_to_memory(self, key: str, value: dict[str, Any], ttl: int) -> bool:
        """Set to memory cache"""
        try:
            self.memory_cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
                "created_at": time.time(),
            }
            return True
        except Exception as e:
            logger.error(f"Memory cache set error: {e!s}")
            return False

    def _delete_from_memory(self, key: str) -> bool:
        """Delete from memory cache"""
        if key in self.memory_cache:
            del self.memory_cache[key]
            return True
        return False

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        memory_entries = len(self.memory_cache)

        # Clean expired entries
        current_time = time.time()
        expired_keys = [
            k for k, v in self.memory_cache.items() if current_time >= v["expires_at"]
        ]

        for key in expired_keys:
            del self.memory_cache[key]

        return {
            "type": "redis" if self.redis_client else "memory",
            "memory_entries": len(self.memory_cache),
            "expired_cleaned": len(expired_keys),
            "redis_connected": self.redis_client is not None,
        }
