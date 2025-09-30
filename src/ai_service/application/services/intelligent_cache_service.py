"""Intelligent caching service for ultra-fast spending text processing."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class IntelligentCacheService:
    """Intelligent caching service with pattern recognition and learning."""

    def __init__(self) -> None:
        """Initialize intelligent cache service."""
        self._text_cache: dict[str, dict[str, Any]] = {}
        self._pattern_cache: dict[str, dict[str, Any]] = {}
        self._similarity_cache: dict[str, list[str]] = {}
        self._cache_ttl = 3600  # 1 hour
        self._max_cache_size = 10000
        self._hit_count = 0
        self._miss_count = 0

    def get_cached_result(self, text: str, language: str) -> dict[str, Any] | None:
        """Get cached result for text processing."""
        cache_key = self._generate_cache_key(text, language)

        if cache_key in self._text_cache:
            cached_item = self._text_cache[cache_key]

            # Check if cache is still valid
            if self._is_cache_valid(cached_item):
                self._hit_count += 1
                logger.debug(f"Cache hit for text: {text[:50]}...")
                return cached_item["result"]
            else:
                # Remove expired cache
                del self._text_cache[cache_key]

        # Try similarity matching
        similar_result = self._find_similar_cached_result(text, language)
        if similar_result:
            self._hit_count += 1
            logger.debug(f"Similarity cache hit for text: {text[:50]}...")
            return similar_result

        self._miss_count += 1
        return None

    def cache_result(self, text: str, language: str, result: dict[str, Any]) -> None:
        """Cache processing result with intelligent features."""
        cache_key = self._generate_cache_key(text, language)

        # Manage cache size
        if len(self._text_cache) >= self._max_cache_size:
            self._evict_old_entries()

        # Store in text cache
        self._text_cache[cache_key] = {
            "result": result,
            "timestamp": datetime.utcnow(),
            "text": text,
            "language": language,
            "access_count": 1,
            "confidence": result.get("confidence", 0.5),
        }

        # Store pattern for similarity matching
        self._cache_pattern(text, language, result)

        logger.debug(f"Cached result for text: {text[:50]}...")

    def _generate_cache_key(self, text: str, language: str) -> str:
        """Generate cache key for text and language."""
        # Normalize text for better cache hits
        normalized_text = self._normalize_text(text)
        content = f"{normalized_text}:{language}"
        return hashlib.sha256(content.encode()).hexdigest()[
            :16
        ]  # Use SHA-256 for security

    def _normalize_text(self, text: str) -> str:
        """Normalize text for better cache matching."""
        import re

        # Convert to lowercase
        text = text.lower().strip()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Normalize currency symbols
        text = text.replace("฿", "บาท")
        text = text.replace("$", "dollar")

        # Normalize common variations
        text = re.sub(r"(?:จ่าย|pay|paid)", "จ่าย", text)
        text = re.sub(r"(?:ซื้อ|buy|bought)", "ซื้อ", text)
        text = re.sub(r"(?:กิน|ทาน|eat)", "กิน", text)

        return text

    def _is_cache_valid(self, cached_item: dict[str, Any]) -> bool:
        """Check if cached item is still valid."""
        timestamp = cached_item["timestamp"]
        age = (datetime.utcnow() - timestamp).total_seconds()

        # Extend TTL for high-confidence results
        confidence = cached_item.get("confidence", 0.5)
        ttl = self._cache_ttl * (1 + confidence)  # Up to 2x TTL for high confidence

        return age < ttl

    def _cache_pattern(self, text: str, _language: str, result: dict[str, Any]) -> None:
        """Cache patterns for similarity matching."""
        # Extract key features for pattern matching
        pattern_key = self._extract_pattern_key(text, result)

        if pattern_key:
            self._pattern_cache[pattern_key] = {
                "result": result,
                "timestamp": datetime.utcnow(),
                "examples": [text],
                "confidence": result.get("confidence", 0.5),
            }

    def _extract_pattern_key(self, text: str, result: dict[str, Any]) -> str | None:
        """Extract pattern key from text and result."""

        try:
            amount = result.get("amount", 0)
            category = result.get("category", "")

            # Extract merchant pattern
            merchant_pattern = ""
            if result.get("merchant"):
                # Try to find merchant in text
                merchant = result["merchant"]
                if merchant.lower() in text.lower():
                    merchant_pattern = "merchant_explicit"
                else:
                    merchant_pattern = "merchant_inferred"

            # Extract amount pattern
            amount_pattern = ""
            if amount > 0:
                amount_str = str(int(amount))
                if amount_str in text:
                    amount_pattern = "amount_explicit"
                else:
                    amount_pattern = "amount_inferred"

            # Create pattern signature
            pattern_parts = [
                category.lower() if category else "unknown",
                merchant_pattern,
                amount_pattern,
                "thai" if any(ord(c) > 127 for c in text) else "english",
            ]

            return "_".join(filter(None, pattern_parts))

        except Exception:
            return None

    def _find_similar_cached_result(
        self, text: str, language: str
    ) -> dict[str, Any] | None:
        """Find similar cached result using pattern matching."""
        try:
            # Simple similarity check based on keywords
            text_words = set(self._normalize_text(text).split())

            best_match = None
            best_similarity = 0.0

            for _cache_key, cached_item in self._text_cache.items():
                if not self._is_cache_valid(cached_item):
                    continue

                cached_text = cached_item.get("text", "")
                cached_words = set(self._normalize_text(cached_text).split())

                # Calculate Jaccard similarity
                intersection = len(text_words & cached_words)
                union = len(text_words | cached_words)

                if union > 0:
                    similarity = intersection / union

                    # Boost similarity for same language
                    if cached_item.get("language") == language:
                        similarity *= 1.2

                    # Boost similarity for high confidence results
                    confidence_boost = cached_item.get("confidence", 0.5)
                    similarity *= 1 + confidence_boost * 0.5

                    if similarity > best_similarity and similarity > 0.7:
                        best_similarity = similarity
                        best_match = cached_item["result"].copy()

            if best_match:
                # Adjust confidence based on similarity
                best_match["confidence"] = min(
                    best_match.get("confidence", 0.5) * best_similarity,
                    0.9,  # Cap at 0.9 for similarity matches
                )
                best_match["method"] = "similarity_cache"

            return best_match

        except Exception as e:
            logger.warning(f"Error in similarity matching: {e}")
            return None

    def _evict_old_entries(self) -> None:
        """Evict old cache entries to manage memory."""
        # Sort by timestamp and access count
        sorted_items = sorted(
            self._text_cache.items(),
            key=lambda x: (x[1]["timestamp"], x[1].get("access_count", 0)),
        )

        # Remove oldest 20% of entries
        remove_count = max(1, len(sorted_items) // 5)
        for i in range(remove_count):
            cache_key = sorted_items[i][0]
            del self._text_cache[cache_key]

        logger.info(f"Evicted {remove_count} old cache entries")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_size": len(self._text_cache),
            "pattern_cache_size": len(self._pattern_cache),
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_ttl_seconds": self._cache_ttl,
            "max_cache_size": self._max_cache_size,
        }

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._text_cache.clear()
        self._pattern_cache.clear()
        self._similarity_cache.clear()
        self._hit_count = 0
        self._miss_count = 0
        logger.info("All caches cleared")

    def warm_cache_with_common_patterns(self) -> None:
        """Pre-warm cache with common spending patterns."""
        common_patterns = [
            # Thai patterns
            (
                "กาแฟ สตาร์บัคส์ 150 บาท",
                "th",
                {
                    "amount": 150.0,
                    "currency": "THB",
                    "merchant": "สตาร์บัคส์",
                    "category": "Food & Dining",
                    "payment_method": "Cash",
                    "description": "กาแฟ สตาร์บัคส์",
                    "confidence": 0.9,
                },
            ),
            (
                "ข้าว ร้านอาหาร 80 บาท",
                "th",
                {
                    "amount": 80.0,
                    "currency": "THB",
                    "merchant": "ร้านอาหาร",
                    "category": "Food & Dining",
                    "payment_method": "Cash",
                    "description": "ข้าว ร้านอาหาร",
                    "confidence": 0.9,
                },
            ),
            (
                "แท็กซี่ 120 บาท",
                "th",
                {
                    "amount": 120.0,
                    "currency": "THB",
                    "merchant": "แท็กซี่",
                    "category": "Transportation",
                    "payment_method": "Cash",
                    "description": "แท็กซี่",
                    "confidence": 0.9,
                },
            ),
            # English patterns
            (
                "coffee starbucks 150 baht",
                "en",
                {
                    "amount": 150.0,
                    "currency": "THB",
                    "merchant": "Starbucks",
                    "category": "Food & Dining",
                    "payment_method": "Cash",
                    "description": "Coffee at Starbucks",
                    "confidence": 0.9,
                },
            ),
            (
                "lunch restaurant 200 baht",
                "en",
                {
                    "amount": 200.0,
                    "currency": "THB",
                    "merchant": "Restaurant",
                    "category": "Food & Dining",
                    "payment_method": "Cash",
                    "description": "Lunch at restaurant",
                    "confidence": 0.9,
                },
            ),
            (
                "taxi 100 baht",
                "en",
                {
                    "amount": 100.0,
                    "currency": "THB",
                    "merchant": "Taxi",
                    "category": "Transportation",
                    "payment_method": "Cash",
                    "description": "Taxi ride",
                    "confidence": 0.9,
                },
            ),
        ]

        for text, language, result in common_patterns:
            self.cache_result(text, language, result)

        logger.info(f"Cache warmed with {len(common_patterns)} common patterns")


# Global cache instance
_global_cache = IntelligentCacheService()


def get_intelligent_cache() -> IntelligentCacheService:
    """Get global intelligent cache instance."""
    return _global_cache
