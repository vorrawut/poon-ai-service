"""Intelligent mapping service with caching, retry logic, and auto-learning."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any

import structlog

from ...domain.entities.category_mapping import (
    CategoryMapping,
    CategoryMappingId,
    MappingCandidate,
    MappingSource,
    MappingType,
)
from ...domain.repositories.category_mapping_repository import CategoryMappingRepository

logger = structlog.get_logger(__name__)


class MappingResult:
    """Result of a mapping lookup operation."""

    def __init__(
        self,
        category: str | None = None,
        confidence: float = 0.0,
        source: str = "unknown",
        mapping_id: CategoryMappingId | None = None,
        fallback_used: bool = False,
        cached: bool = False,
    ) -> None:
        self.category = category
        self.confidence = confidence
        self.source = source
        self.mapping_id = mapping_id
        self.fallback_used = fallback_used
        self.cached = cached

    def is_successful(self) -> bool:
        """Check if mapping was successful."""
        return self.category is not None and self.confidence > 0.0

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if mapping has high confidence."""
        return self.confidence >= threshold


class IntelligentMappingService:
    """Service for intelligent category mapping with caching and learning."""

    def __init__(
        self,
        repository: CategoryMappingRepository,
        cache_ttl: int = 3600,  # 1 hour
        max_retries: int = 3,
        fuzzy_threshold: float = 0.8,
        auto_learn_threshold: int = 3,  # Auto-create after 3 occurrences
    ) -> None:
        self._repository = repository
        self._cache_ttl = cache_ttl
        self._max_retries = max_retries
        self._fuzzy_threshold = fuzzy_threshold
        self._auto_learn_threshold = auto_learn_threshold

        # In-memory cache
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_version: str = ""
        self._last_cache_refresh = datetime.utcnow()

        # Fallback mappings for when DB is unavailable
        self._fallback_mappings = self._get_fallback_mappings()

    async def initialize(self) -> None:
        """Initialize the mapping service."""
        try:
            await self._repository.initialize()
            await self._refresh_cache()
            logger.info("Intelligent mapping service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize mapping service: {e}")
            raise

    async def map_category(
        self,
        text: str,
        language: str = "en",
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> MappingResult:
        """Map text to category using intelligent lookup with retry logic."""
        normalized_text = self._normalize_text(text)
        cache_key = self._generate_cache_key(normalized_text, language)

        # Try cache first
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for '{text}' -> {cached_result['category']}")
            return MappingResult(
                category=cached_result["category"],
                confidence=cached_result["confidence"],
                source=cached_result["source"],
                mapping_id=CategoryMappingId.from_string(cached_result["mapping_id"])
                if cached_result.get("mapping_id")
                else None,
                cached=True,
            )

        # Try database lookup with retry logic
        for attempt in range(self._max_retries):
            try:
                result = await self._lookup_mapping(
                    normalized_text, language, user_id, session_id
                )

                if result.is_successful():
                    # Cache successful result
                    self._cache_result(cache_key, result)

                    # Update usage stats if mapping found
                    if result.mapping_id:
                        # Fire and forget task for stats update
                        asyncio.create_task(
                            self._repository.update_usage_stats(result.mapping_id, True)
                        ).add_done_callback(lambda _: None)  # Suppress warning

                    return result

                # If no mapping found and this is the last attempt
                if attempt == self._max_retries - 1:
                    return await self._handle_unmapped_text(
                        text, normalized_text, language, user_id, session_id
                    )

                # Refresh cache and try again
                if attempt == 0:
                    await self._refresh_cache()

            except Exception as e:
                logger.warning(f"Mapping attempt {attempt + 1} failed: {e}")

                if attempt == self._max_retries - 1:
                    # Final fallback
                    return self._get_fallback_mapping(normalized_text, language)

                # Wait before retry
                await asyncio.sleep(0.1 * (2**attempt))  # Exponential backoff

        # Should not reach here, but just in case
        return self._get_fallback_mapping(normalized_text, language)

    async def _lookup_mapping(
        self,
        text: str,
        language: str,
        _user_id: str | None = None,
        _session_id: str | None = None,
    ) -> MappingResult:
        """Perform database lookup for mapping."""
        # 1. Exact key match
        mapping = await self._repository.find_by_key(text, language)
        if mapping and mapping.is_active():
            return MappingResult(
                category=mapping.target_category,
                confidence=mapping.confidence,
                source="exact_match",
                mapping_id=mapping.id,
            )

        # 2. Find potential matches (aliases, patterns, text search)
        potential_mappings = await self._repository.find_by_text(
            text, language, limit=10
        )

        # Score and rank potential matches
        scored_mappings = []
        for mapping in potential_mappings:
            if not mapping.is_active():
                continue

            confidence = mapping.calculate_match_confidence(text)
            if confidence > 0:
                scored_mappings.append((mapping, confidence))

        # Sort by confidence (descending)
        scored_mappings.sort(key=lambda x: x[1], reverse=True)

        if scored_mappings:
            best_mapping, best_confidence = scored_mappings[0]
            return MappingResult(
                category=best_mapping.target_category,
                confidence=best_confidence,
                source="pattern_match",
                mapping_id=best_mapping.id,
            )

        # 3. Fuzzy string matching
        fuzzy_result = await self._fuzzy_match(text, language)
        if fuzzy_result.is_successful():
            return fuzzy_result

        # 4. No mapping found
        return MappingResult()

    async def _fuzzy_match(self, text: str, language: str) -> MappingResult:
        """Perform fuzzy string matching against existing mappings."""
        try:
            # Get all active mappings for the language
            all_mappings = await self._repository.get_all_active_mappings(language)

            best_match = None
            best_ratio = 0.0

            for mapping in all_mappings:
                # Check against key
                ratio = SequenceMatcher(None, text.lower(), mapping.key.lower()).ratio()
                if ratio > best_ratio and ratio >= self._fuzzy_threshold:
                    best_ratio = ratio
                    best_match = mapping

                # Check against aliases
                for alias in mapping.aliases:
                    ratio = SequenceMatcher(None, text.lower(), alias.lower()).ratio()
                    if ratio > best_ratio and ratio >= self._fuzzy_threshold:
                        best_ratio = ratio
                        best_match = mapping

            if best_match:
                confidence = best_match.confidence * best_ratio
                return MappingResult(
                    category=best_match.target_category,
                    confidence=confidence,
                    source="fuzzy_match",
                    mapping_id=best_match.id,
                )

        except Exception as e:
            logger.warning(f"Fuzzy matching failed: {e}")

        return MappingResult()

    async def _handle_unmapped_text(
        self,
        original_text: str,
        normalized_text: str,
        language: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> MappingResult:
        """Handle text that couldn't be mapped."""
        try:
            # Check if we have similar candidates
            similar_candidates = await self._repository.find_similar_candidates(
                normalized_text, language, limit=5
            )

            # Check if this text has been seen before
            existing_candidate = None
            for candidate in similar_candidates:
                if candidate.normalized_text == normalized_text:
                    existing_candidate = candidate
                    break

            if existing_candidate:
                # Increment attempt count
                existing_candidate.increment_attempts()
                await self._repository.save_candidate(existing_candidate)

                # Check if we should auto-learn
                if existing_candidate.attempt_count >= self._auto_learn_threshold:
                    return await self._try_auto_learn(existing_candidate)
            else:
                # Create new candidate
                candidate = MappingCandidate(
                    original_text=original_text,
                    normalized_text=normalized_text,
                    language=language,
                    user_id=user_id,
                    session_id=session_id,
                )

                # Try to suggest a category using heuristics
                suggested_category = self._suggest_category_heuristic(
                    normalized_text, language
                )
                if suggested_category:
                    candidate.suggested_category = suggested_category
                    candidate.suggested_confidence = 0.6
                    candidate.suggestion_source = "heuristic"

                await self._repository.save_candidate(candidate)

                logger.info(
                    f"Created mapping candidate for unmapped text: '{original_text}'"
                )

        except Exception as e:
            logger.error(f"Failed to handle unmapped text: {e}")

        # Return fallback mapping
        return self._get_fallback_mapping(normalized_text, language)

    async def _try_auto_learn(self, candidate: MappingCandidate) -> MappingResult:
        """Try to auto-learn a mapping from repeated candidate."""
        try:
            if candidate.suggested_category and candidate.suggested_confidence > 0.5:
                # Create new mapping
                new_mapping = CategoryMapping(
                    key=candidate.normalized_text,
                    mapping_type=MappingType.CATEGORY,
                    language=candidate.language,
                    target_category=candidate.suggested_category,
                    confidence=candidate.suggested_confidence,
                    source=MappingSource.AUTO_LEARNED,
                    priority=5,  # Lower priority for auto-learned
                )

                await self._repository.save_mapping(new_mapping)

                # Update candidate status
                candidate.approve(candidate.suggested_category, "auto_learn_system")
                await self._repository.save_candidate(candidate)

                logger.info(
                    f"Auto-learned mapping: '{candidate.normalized_text}' -> {candidate.suggested_category}"
                )

                return MappingResult(
                    category=candidate.suggested_category,
                    confidence=candidate.suggested_confidence,
                    source="auto_learned",
                    mapping_id=new_mapping.id,
                )

        except Exception as e:
            logger.error(f"Failed to auto-learn mapping: {e}")

        return MappingResult()

    def _suggest_category_heuristic(self, text: str, language: str) -> str | None:
        """Suggest category using heuristic rules."""
        text_lower = text.lower()

        # Define keyword mappings for different languages
        if language == "th":
            keyword_mappings = {
                "Food & Dining": [
                    "อาหาร",
                    "ร้าน",
                    "กิน",
                    "ทาน",
                    "กาแฟ",
                    "เครื่องดื่ม",
                    "ข้าว",
                ],
                "Transportation": ["แท็กซี่", "รถ", "เดินทาง", "วิน", "grab", "bolt"],
                "Shopping": ["ซื้อ", "ช้อป", "ห้าง", "ตลาด"],
                "Travel": ["โรงแรม", "ที่พัก", "เที่ยว", "จอง"],
                "Groceries": ["ซุปเปอร์", "เซเว่น", "บิ๊กซี", "ท็อปส์"],
                "Healthcare": ["โรงพยาบาล", "หมอ", "ยา", "คลินิก"],
                "Entertainment": ["หนัง", "เกม", "บันเทิง"],
                "Utilities": ["ไฟฟ้า", "น้ำ", "บิล", "อินเทอร์เน็ต"],
            }
        else:
            keyword_mappings = {
                "Food & Dining": [
                    "food",
                    "restaurant",
                    "cafe",
                    "coffee",
                    "meal",
                    "dining",
                ],
                "Transportation": ["taxi", "uber", "transport", "bus", "train", "ride"],
                "Shopping": ["shop", "store", "mall", "buy", "purchase"],
                "Travel": ["hotel", "booking", "travel", "flight", "accommodation"],
                "Groceries": ["grocery", "supermarket", "market"],
                "Healthcare": ["hospital", "doctor", "medical", "pharmacy"],
                "Entertainment": ["movie", "game", "entertainment", "cinema"],
                "Utilities": ["electric", "water", "internet", "phone", "utility"],
            }

        # Find best matching category
        for category, keywords in keyword_mappings.items():
            if any(keyword in text_lower for keyword in keywords):
                return category

        return None

    def _get_fallback_mapping(self, text: str, language: str) -> MappingResult:
        """Get fallback mapping when all else fails."""
        # Try fallback mappings
        fallback_category = self._fallback_mappings.get(language, {}).get(text.lower())

        if fallback_category:
            return MappingResult(
                category=fallback_category,
                confidence=0.5,
                source="fallback",
                fallback_used=True,
            )

        # Final fallback to Miscellaneous
        return MappingResult(
            category="Miscellaneous",
            confidence=0.3,
            source="default_fallback",
            fallback_used=True,
        )

    def _get_fallback_mappings(self) -> dict[str, dict[str, str]]:
        """Get hardcoded fallback mappings for when DB is unavailable."""
        return {
            "en": {
                "food": "Food & Dining",
                "restaurant": "Food & Dining",
                "coffee": "Food & Dining",
                "taxi": "Transportation",
                "uber": "Transportation",
                "hotel": "Travel",
                "shopping": "Shopping",
                "grocery": "Groceries",
                "hospital": "Healthcare",
                "movie": "Entertainment",
            },
            "th": {
                "อาหาร": "Food & Dining",
                "ร้านอาหาร": "Food & Dining",
                "กาแฟ": "Food & Dining",
                "แท็กซี่": "Transportation",
                "โรงแรม": "Travel",
                "ซื้อของ": "Shopping",
                "ตลาด": "Groceries",
                "โรงพยาบาล": "Healthcare",
                "หนัง": "Entertainment",
            },
        }

    async def _refresh_cache(self) -> None:
        """Refresh the in-memory cache from database."""
        try:
            current_version = await self._repository.get_cache_version()

            # Only refresh if version changed or cache is old
            if (
                current_version != self._cache_version
                or datetime.utcnow() - self._last_cache_refresh
                > timedelta(seconds=self._cache_ttl)
            ):
                # Get all active mappings
                all_mappings = await self._repository.get_all_active_mappings()

                # Rebuild cache
                new_cache = {}
                for mapping in all_mappings:
                    cache_key = self._generate_cache_key(mapping.key, mapping.language)
                    new_cache[cache_key] = {
                        "category": mapping.target_category,
                        "confidence": mapping.confidence,
                        "source": "database",
                        "mapping_id": mapping.id.value,
                        "timestamp": datetime.utcnow().timestamp(),
                    }

                self._cache = new_cache
                self._cache_version = current_version
                self._last_cache_refresh = datetime.utcnow()

                logger.info(f"Cache refreshed with {len(new_cache)} mappings")

        except Exception as e:
            logger.error(f"Failed to refresh cache: {e}")

    def _get_from_cache(self, cache_key: str) -> dict[str, Any] | None:
        """Get result from cache if valid."""
        cached_item = self._cache.get(cache_key)

        if cached_item:
            # Check if cache item is still valid
            age = datetime.utcnow().timestamp() - cached_item["timestamp"]
            if age < self._cache_ttl:
                return cached_item
            else:
                # Remove expired item
                del self._cache[cache_key]

        return None

    def _cache_result(self, cache_key: str, result: MappingResult) -> None:
        """Cache a mapping result."""
        if result.is_successful():
            self._cache[cache_key] = {
                "category": result.category,
                "confidence": result.confidence,
                "source": result.source,
                "mapping_id": result.mapping_id.value if result.mapping_id else None,
                "timestamp": datetime.utcnow().timestamp(),
            }

    def _generate_cache_key(self, text: str, language: str) -> str:
        """Generate cache key for text and language."""
        content = f"{text}:{language}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent matching."""
        import re

        # Convert to lowercase and strip
        text = text.lower().strip()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common punctuation
        text = re.sub(r"[^\w\s]", "", text)

        return text

    # Management methods
    async def create_mapping(
        self,
        key: str,
        target_category: str,
        language: str = "en",
        aliases: list[str] | None = None,
        patterns: list[str] | None = None,
        confidence: float = 0.9,
        created_by: str | None = None,
    ) -> CategoryMapping:
        """Create a new category mapping."""
        mapping = CategoryMapping(
            key=self._normalize_text(key),
            mapping_type=MappingType.CATEGORY,
            language=language,
            target_category=target_category,
            aliases=aliases or [],
            patterns=patterns or [],
            confidence=confidence,
            source=MappingSource.MANUAL,
            created_by=created_by,
        )

        await self._repository.save_mapping(mapping)

        # Invalidate cache
        await self._refresh_cache()

        logger.info(f"Created mapping: {key} -> {target_category}")
        return mapping

    async def update_mapping(
        self,
        mapping_id: CategoryMappingId,
        **updates: Any,
    ) -> CategoryMapping | None:
        """Update an existing mapping."""
        mapping = await self._repository.find_by_id(mapping_id)
        if not mapping:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(mapping, key):
                setattr(mapping, key, value)

        mapping.increment_version(updates.get("updated_by"))
        await self._repository.save_mapping(mapping)

        # Invalidate cache
        await self._refresh_cache()

        return mapping

    async def get_mapping_stats(self) -> dict[str, Any]:
        """Get statistics about mappings."""
        try:
            analytics = await self._repository.get_mapping_analytics()
            candidate_stats = await self._repository.get_candidate_stats()
            category_distribution = await self._repository.get_category_distribution()

            return {
                "mappings": analytics,
                "candidates": candidate_stats,
                "categories": category_distribution,
                "cache_size": len(self._cache),
                "cache_version": self._cache_version,
            }
        except Exception as e:
            logger.error(f"Failed to get mapping stats: {e}")
            return {}

    async def approve_candidate(
        self,
        candidate_id: CategoryMappingId,
        approved_category: str,
        reviewed_by: str | None = None,
    ) -> bool:
        """Approve a mapping candidate and create the mapping."""
        try:
            candidate = await self._repository.find_candidate_by_id(candidate_id)
            if not candidate:
                return False

            # Create the mapping
            mapping = CategoryMapping(
                key=candidate.normalized_text,
                mapping_type=MappingType.CATEGORY,
                language=candidate.language,
                target_category=approved_category,
                confidence=0.8,  # Manual approval gets high confidence
                source=MappingSource.USER_CORRECTION,
                created_by=reviewed_by,
            )

            await self._repository.save_mapping(mapping)

            # Update candidate
            candidate.approve(approved_category, reviewed_by)
            await self._repository.save_candidate(candidate)

            # Refresh cache
            await self._refresh_cache()

            logger.info(
                f"Approved candidate: {candidate.original_text} -> {approved_category}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to approve candidate {candidate_id}: {e}")
            return False

    async def get_pending_candidates(
        self, limit: int = 50, offset: int = 0
    ) -> list[MappingCandidate]:
        """Get candidates pending review."""
        return await self._repository.get_pending_candidates(limit, offset)
