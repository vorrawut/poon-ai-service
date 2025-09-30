"""AI Learning Service for continuous improvement."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

import structlog

from ...domain.entities.ai_training_data import (
    AITrainingData,
    FeedbackType,
    ProcessingStatus,
)
from ...domain.value_objects.confidence import ConfidenceScore
from ...infrastructure.resilience.circuit_breaker import (
    CircuitBreakerConfig,
    circuit_breaker,
)

if TYPE_CHECKING:
    from ...domain.repositories.ai_training_repository import AITrainingRepository
    from ...infrastructure.cache.redis_cache import AICache
    from ...infrastructure.events.event_stream import AIEventPublisher

logger = structlog.get_logger(__name__)


class AILearningService:
    """Service for AI learning and continuous improvement."""

    def __init__(
        self,
        training_repository: AITrainingRepository,
        cache: AICache | None = None,
        event_publisher: AIEventPublisher | None = None,
    ) -> None:
        """Initialize AI learning service."""
        self._training_repository = training_repository
        self._cache = cache
        self._event_publisher = event_publisher
        self._category_mappings_cache: dict[str, str] = {}
        self._last_cache_update: datetime | None = None

    @circuit_breaker("record_ai_interaction", CircuitBreakerConfig(failure_threshold=3))
    async def record_ai_interaction(
        self,
        input_text: str,
        language: str,
        raw_ai_response: str,
        parsed_ai_data: dict[str, Any],
        ai_confidence: float,
        processing_time_ms: int,
        model_version: str = "llama3.2:3b",
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> AITrainingData:
        """Record an AI interaction for learning."""

        training_data = AITrainingData(
            input_text=input_text,
            language=language,
            raw_ai_response=raw_ai_response,
            parsed_ai_data=parsed_ai_data,
            ai_confidence=ConfidenceScore(ai_confidence),
            processing_time_ms=processing_time_ms,
            model_version=model_version,
            user_id=user_id,
            session_id=session_id,
            status=ProcessingStatus.SUCCESS,
        )

        await self._training_repository.save(training_data)
        logger.info(f"Recorded AI interaction: {training_data.id.value}")

        # Publish event for real-time processing
        if self._event_publisher:
            try:
                await self._event_publisher.publish_ai_interaction(
                    interaction_id=training_data.id.value,
                    input_text=input_text,
                    language=language,
                    ai_response=parsed_ai_data,
                    processing_time_ms=processing_time_ms,
                    confidence=ai_confidence,
                    model_version=model_version,
                )
            except Exception as e:
                logger.warning(f"Failed to publish AI interaction event: {e}")

        return training_data

    async def record_processing_failure(
        self,
        input_text: str,
        language: str,
        error_message: str,
        validation_errors: list[str] | None = None,
        raw_ai_response: str = "",
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> AITrainingData:
        """Record a processing failure for analysis."""

        training_data = AITrainingData(
            input_text=input_text,
            language=language,
            raw_ai_response=raw_ai_response,
            user_id=user_id,
            session_id=session_id,
            status=ProcessingStatus.FAILED_VALIDATION,
        )

        training_data.mark_as_failed(error_message, validation_errors)
        await self._training_repository.save(training_data)

        logger.warning(f"Recorded processing failure: {training_data.id.value}")
        return training_data

    async def add_user_feedback(
        self,
        training_data_id: str,
        corrected_data: dict[str, Any],
        feedback_type: FeedbackType = FeedbackType.USER_CORRECTION,
        admin_notes: str | None = None,
    ) -> bool:
        """Add user feedback and corrections."""

        from ...domain.entities.ai_training_data import AITrainingDataId

        training_data = await self._training_repository.find_by_id(
            AITrainingDataId.from_string(training_data_id)
        )

        if not training_data:
            logger.error(f"Training data not found: {training_data_id}")
            return False

        training_data.add_feedback(feedback_type, corrected_data, admin_notes)
        await self._training_repository.save(training_data)

        # Update category mappings cache
        await self._update_category_mappings_cache()

        logger.info(f"Added feedback to training data: {training_data_id}")
        return True

    @circuit_breaker("get_category_mappings", CircuitBreakerConfig(failure_threshold=2))
    async def get_dynamic_category_mapping(self) -> dict[str, str]:
        """Get dynamically learned category mappings."""

        # Try cache first
        if self._cache:
            try:
                cached_mappings = await self._cache.get_category_mappings()
                if cached_mappings:
                    return cached_mappings
            except Exception as e:
                logger.warning(f"Failed to get cached category mappings: {e}")

        # Update cache if needed (every hour)
        now = datetime.utcnow()
        if (
            not self._last_cache_update
            or (now - self._last_cache_update).total_seconds() > 3600
        ):
            await self._update_category_mappings_cache()

        return self._category_mappings_cache

    async def _update_category_mappings_cache(self) -> None:
        """Update the category mappings cache from learned data."""

        try:
            mappings = await self._training_repository.get_category_mapping_insights()
            self._category_mappings_cache = mappings
            self._last_cache_update = datetime.utcnow()

            # Update Redis cache
            if self._cache:
                try:
                    await self._cache.set_category_mappings(mappings)
                except Exception as e:
                    logger.warning(f"Failed to cache category mappings: {e}")

            logger.info(
                f"Updated category mappings cache with {len(mappings)} mappings"
            )

        except Exception as e:
            logger.error(f"Failed to update category mappings cache: {e}")

    async def get_processing_insights(self) -> dict[str, Any]:
        """Get insights about AI processing performance."""

        try:
            # Get overall stats
            stats = await self._training_repository.get_accuracy_stats()

            # Get status counts
            status_counts = await self._training_repository.count_by_status()

            # Get common errors
            error_patterns = await self._training_repository.get_common_error_patterns()

            # Get category mappings
            category_mappings = (
                await self._training_repository.get_category_mapping_insights()
            )

            return {
                "overall_stats": stats,
                "status_distribution": status_counts,
                "common_errors": error_patterns[:10],  # Top 10 errors
                "learned_category_mappings": category_mappings,
                "total_mappings_learned": len(category_mappings),
            }

        except Exception as e:
            logger.error(f"Failed to get processing insights: {e}")
            return {}

    async def get_improvement_suggestions(self) -> list[dict[str, Any]]:
        """Get suggestions for improving AI accuracy."""

        suggestions = []

        try:
            # Find low accuracy cases
            low_accuracy_cases = (
                await self._training_repository.find_low_accuracy_cases(
                    accuracy_threshold=0.7, limit=50
                )
            )

            if low_accuracy_cases:
                suggestions.append(
                    {
                        "type": "accuracy_improvement",
                        "priority": "high",
                        "description": f"Found {len(low_accuracy_cases)} cases with accuracy < 70%",
                        "action": "Review and add feedback to improve model training",
                        "cases_count": len(low_accuracy_cases),
                    }
                )

            # Find failed cases
            failed_cases = await self._training_repository.find_failed_cases(limit=50)

            if failed_cases:
                suggestions.append(
                    {
                        "type": "error_reduction",
                        "priority": "high",
                        "description": f"Found {len(failed_cases)} failed processing cases",
                        "action": "Analyze error patterns and improve validation logic",
                        "cases_count": len(failed_cases),
                    }
                )

            # Check language-specific performance
            for language in ["th", "en"]:
                lang_cases = await self._training_repository.find_by_language(
                    language, limit=100
                )

                if lang_cases:
                    failed_count = sum(
                        1
                        for case in lang_cases
                        if case.status != ProcessingStatus.SUCCESS
                    )
                    failure_rate = failed_count / len(lang_cases)

                    if failure_rate > 0.2:  # More than 20% failure rate
                        suggestions.append(
                            {
                                "type": "language_improvement",
                                "priority": "medium",
                                "description": f"High failure rate for {language}: {failure_rate:.1%}",
                                "action": f"Focus on improving {language} language processing",
                                "language": language,
                                "failure_rate": failure_rate,
                            }
                        )

            return suggestions

        except Exception as e:
            logger.error(f"Failed to get improvement suggestions: {e}")
            return []

    async def find_similar_successful_cases(
        self, input_text: str, language: str
    ) -> list[AITrainingData]:
        """Find similar successful cases for learning."""

        try:
            similar_cases = await self._training_repository.find_similar_inputs(
                input_text, language, limit=5
            )

            # Filter for successful cases only
            successful_cases = [
                case
                for case in similar_cases
                if case.status == ProcessingStatus.SUCCESS
            ]

            return successful_cases

        except Exception as e:
            logger.error(f"Failed to find similar cases: {e}")
            return []

    async def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """Clean up old training data."""

        try:
            deleted_count = await self._training_repository.delete_old_data(
                days_to_keep
            )
            logger.info(f"Cleaned up {deleted_count} old training records")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0

    async def get_confidence_calibration_report(self) -> dict[str, Any]:
        """Get report on how well AI confidence correlates with actual accuracy."""

        try:
            stats = await self._training_repository.get_accuracy_stats()

            # Get cases with both confidence and accuracy scores

            # This would need to be implemented in the repository
            # For now, return basic stats
            return {
                "avg_confidence": stats.get("avg_confidence", 0.0),
                "avg_accuracy": stats.get("avg_accuracy", 0.0),
                "confidence_accuracy_gap": abs(
                    stats.get("avg_confidence", 0.0) - stats.get("avg_accuracy", 0.0)
                ),
                "recommendation": "Monitor confidence vs accuracy alignment",
            }

        except Exception as e:
            logger.error(f"Failed to get confidence calibration report: {e}")
            return {}
