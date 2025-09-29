"""
Simple in-memory cache for AI service
Reduces API calls for repeated patterns
"""

import hashlib
import json
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache with TTL support"""

    def __init__(self, default_ttl: int = 3600):
        self.cache: dict[str, dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "evictions": 0}

    def _generate_key(self, data: Any) -> str:
        """Generate cache key from data"""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)

        return hashlib.md5(content.encode()).hexdigest()

    def _is_expired(self, entry: dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        return time.time() > entry["expires_at"]

    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self.cache.items()
            if current_time > entry["expires_at"]
        ]

        for key in expired_keys:
            del self.cache[key]
            self.stats["evictions"] += 1

    def get(self, key_data: Any) -> Optional[Any]:
        """Get value from cache"""
        key = self._generate_key(key_data)

        if key not in self.cache:
            self.stats["misses"] += 1
            return None

        entry = self.cache[key]

        if self._is_expired(entry):
            del self.cache[key]
            self.stats["misses"] += 1
            self.stats["evictions"] += 1
            return None

        self.stats["hits"] += 1
        logger.debug(f"Cache hit for key: {key[:8]}...")
        return entry["value"]

    def set(self, key_data: Any, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        key = self._generate_key(key_data)
        ttl = ttl or self.default_ttl

        self.cache[key] = {
            "value": value,
            "created_at": time.time(),
            "expires_at": time.time() + ttl,
        }

        self.stats["sets"] += 1
        logger.debug(f"Cache set for key: {key[:8]}... (TTL: {ttl}s)")

        # Cleanup expired entries periodically
        if len(self.cache) % 100 == 0:
            self._cleanup_expired()

    def delete(self, key_data: Any) -> bool:
        """Delete entry from cache"""
        key = self._generate_key(key_data)

        if key in self.cache:
            del self.cache[key]
            return True

        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            **self.stats,
            "total_entries": len(self.cache),
            "hit_rate_percent": round(hit_rate, 2),
            "memory_usage_mb": self._estimate_memory_usage(),
        }

    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB (rough calculation)"""
        import sys

        total_size = 0
        for entry in self.cache.values():
            total_size += sys.getsizeof(entry) + sys.getsizeof(entry["value"])

        return round(total_size / (1024 * 1024), 2)


# Global cache instances
nlp_cache = SimpleCache(default_ttl=3600)  # 1 hour for NLP results
ocr_cache = SimpleCache(default_ttl=7200)  # 2 hours for OCR results
ai_cache = SimpleCache(default_ttl=1800)  # 30 minutes for AI results


class CacheManager:
    """Manage different cache types"""

    def __init__(self):
        self.caches = {"nlp": nlp_cache, "ocr": ocr_cache, "ai": ai_cache}

    def get_nlp_result(self, text: str, language: str = "en") -> Optional[Any]:
        """Get cached NLP result"""
        cache_key = f"nlp:{language}:{text}"
        return nlp_cache.get(cache_key)

    def set_nlp_result(
        self, text: str, result: Any, language: str = "en", ttl: int = 3600
    ) -> None:
        """Cache NLP result"""
        cache_key = f"nlp:{language}:{text}"
        nlp_cache.set(cache_key, result, ttl)

    def get_ocr_result(self, image_hash: str) -> Optional[Any]:
        """Get cached OCR result"""
        cache_key = f"ocr:{image_hash}"
        return ocr_cache.get(cache_key)

    def set_ocr_result(self, image_hash: str, result: Any, ttl: int = 7200) -> None:
        """Cache OCR result"""
        cache_key = f"ocr:{image_hash}"
        ocr_cache.set(cache_key, result, ttl)

    def get_ai_result(self, prompt_hash: str) -> Optional[Any]:
        """Get cached AI result"""
        cache_key = f"ai:{prompt_hash}"
        return ai_cache.get(cache_key)

    def set_ai_result(self, prompt_hash: str, result: Any, ttl: int = 1800) -> None:
        """Cache AI result"""
        cache_key = f"ai:{prompt_hash}"
        ai_cache.set(cache_key, result, ttl)

    def get_merchant_category(self, merchant: str) -> Optional[str]:
        """Get cached merchant category mapping"""
        cache_key = f"merchant:{merchant.lower()}"
        return nlp_cache.get(cache_key)

    def set_merchant_category(
        self, merchant: str, category: str, ttl: int = 86400
    ) -> None:
        """Cache merchant category mapping (24 hours)"""
        cache_key = f"merchant:{merchant.lower()}"
        nlp_cache.set(cache_key, category, ttl)

    def clear_all(self) -> None:
        """Clear all caches"""
        for cache in self.caches.values():
            cache.clear()
        logger.info("All caches cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get statistics for all caches"""
        stats = {}
        total_entries = 0
        total_hits = 0
        total_misses = 0

        for name, cache in self.caches.items():
            cache_stats = cache.get_stats()
            stats[name] = cache_stats
            total_entries += cache_stats["total_entries"]
            total_hits += cache_stats["hits"]
            total_misses += cache_stats["misses"]

        total_requests = total_hits + total_misses
        overall_hit_rate = (
            (total_hits / total_requests * 100) if total_requests > 0 else 0
        )

        stats["overall"] = {
            "total_entries": total_entries,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "hit_rate_percent": round(overall_hit_rate, 2),
        }

        return stats


# Global cache manager instance
cache_manager = CacheManager()
