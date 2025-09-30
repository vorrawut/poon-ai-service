"""Background tasks for AI processing and learning."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import structlog

from ...application.services.ai_learning_service import AILearningService
from ...core.config.settings import Settings
from .celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    bind=True, name="ai_service.infrastructure.tasks.ai_tasks.process_ai_feedback"
)
def process_ai_feedback(
    self, training_data_id: str, feedback_data: dict[str, Any]
) -> dict[str, Any]:
    """Process user feedback in the background."""
    try:
        from ...domain.entities.ai_training_data import FeedbackType
        from ...infrastructure.database.ai_training_repository import (
            MongoDBTrainingRepository,
        )

        # Initialize services
        settings = Settings()
        training_repo = MongoDBTrainingRepository(settings)
        ai_learning_service = AILearningService(training_repo)

        # Process feedback
        success = await ai_learning_service.add_user_feedback(
            training_data_id=training_data_id,
            corrected_data=feedback_data["corrected_data"],
            feedback_type=FeedbackType(
                feedback_data.get("feedback_type", "user_correction")
            ),
            admin_notes=feedback_data.get("admin_notes"),
        )

        if success:
            logger.info(f"Successfully processed feedback for {training_data_id}")
            return {"status": "success", "training_data_id": training_data_id}
        else:
            logger.error(f"Failed to process feedback for {training_data_id}")
            return {"status": "error", "message": "Training data not found"}

    except Exception as e:
        logger.error(f"Error processing AI feedback: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3) from e


@celery_app.task(
    bind=True, name="ai_service.infrastructure.tasks.ai_tasks.update_category_mappings"
)
def update_category_mappings(self) -> dict[str, Any]:
    """Update category mappings based on recent feedback."""
    try:
        from ...infrastructure.database.ai_training_repository import (
            MongoDBTrainingRepository,
        )

        # Initialize services
        settings = Settings()
        training_repo = MongoDBTrainingRepository(settings)
        ai_learning_service = AILearningService(training_repo)

        # Update mappings
        mappings = await ai_learning_service.get_dynamic_category_mapping()

        logger.info(f"Updated category mappings: {len(mappings)} mappings")
        return {
            "status": "success",
            "mappings_count": len(mappings),
            "updated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error updating category mappings: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3) from e


@celery_app.task(
    bind=True, name="ai_service.infrastructure.tasks.ai_tasks.analyze_accuracy_trends"
)
def analyze_accuracy_trends(self, days_back: int = 7) -> dict[str, Any]:
    """Analyze accuracy trends over time."""
    try:
        from ...application.services.ai_learning_service import AILearningService
        from ...infrastructure.database.ai_training_repository import (
            MongoDBTrainingRepository,
        )

        # Initialize services
        settings = Settings()
        training_repo = MongoDBTrainingRepository(settings)
        AILearningService(training_repo)

        # Get accuracy stats for the period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        stats = training_repo.get_accuracy_stats(
            start_date=start_date, end_date=end_date
        )

        # Analyze trends
        trends = {
            "period_days": days_back,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "stats": stats,
        }

        # Check for accuracy alerts
        avg_accuracy = stats.get("avg_accuracy", 0)
        if avg_accuracy and avg_accuracy < 0.8:
            logger.warning(f"Low accuracy detected: {avg_accuracy:.2%}")
            trends["alert"] = {
                "type": "low_accuracy",
                "accuracy": avg_accuracy,
                "threshold": 0.8,
            }

        logger.info(f"Analyzed accuracy trends for {days_back} days")
        return trends

    except Exception as e:
        logger.error(f"Error analyzing accuracy trends: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3) from e


@celery_app.task(
    bind=True,
    name="ai_service.infrastructure.tasks.ai_tasks.batch_process_training_data",
)
def batch_process_training_data(self, batch_size: int = 100) -> dict[str, Any]:
    """Process training data in batches for insights."""
    try:
        from ...application.services.ai_learning_service import AILearningService
        from ...domain.entities.ai_training_data import ProcessingStatus
        from ...infrastructure.database.ai_training_repository import (
            MongoDBTrainingRepository,
        )

        # Initialize services
        settings = Settings()
        training_repo = MongoDBTrainingRepository(settings)
        AILearningService(training_repo)

        # Get unprocessed training data
        unprocessed_data = training_repo.find_by_status(
            ProcessingStatus.SUCCESS, limit=batch_size
        )

        processed_count = 0
        insights_generated = 0

        for training_data in unprocessed_data:
            try:
                # Generate insights for each training data
                insights = training_data.generate_learning_insights()

                if insights:
                    insights_generated += 1
                    logger.debug(f"Generated insights for {training_data.id.value}")

                processed_count += 1

            except Exception as e:
                logger.error(
                    f"Error processing training data {training_data.id.value}: {e}"
                )
                continue

        result = {
            "status": "success",
            "processed_count": processed_count,
            "insights_generated": insights_generated,
            "batch_size": batch_size,
            "processed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Batch processed {processed_count} training data items")
        return result

    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3) from e


@celery_app.task(
    bind=True, name="ai_service.infrastructure.tasks.ai_tasks.detect_anomalies"
)
def detect_anomalies(self) -> dict[str, Any]:
    """Detect anomalies in AI performance."""
    try:
        from ...application.services.ai_learning_service import AILearningService
        from ...infrastructure.database.ai_training_repository import (
            MongoDBTrainingRepository,
        )

        # Initialize services
        settings = Settings()
        training_repo = MongoDBTrainingRepository(settings)
        AILearningService(training_repo)

        # Get recent stats
        recent_stats = training_repo.get_accuracy_stats(
            start_date=datetime.utcnow() - timedelta(hours=24)
        )

        # Get historical stats for comparison
        historical_stats = training_repo.get_accuracy_stats(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow() - timedelta(days=1),
        )

        anomalies = []

        # Check accuracy drop
        recent_accuracy = recent_stats.get("avg_accuracy", 0) or 0
        historical_accuracy = historical_stats.get("avg_accuracy", 0) or 0

        if historical_accuracy > 0 and recent_accuracy < historical_accuracy * 0.9:
            anomalies.append(
                {
                    "type": "accuracy_drop",
                    "recent_accuracy": recent_accuracy,
                    "historical_accuracy": historical_accuracy,
                    "drop_percentage": (historical_accuracy - recent_accuracy)
                    / historical_accuracy,
                }
            )

        # Check processing time increase
        recent_time = recent_stats.get("avg_processing_time", 0) or 0
        historical_time = historical_stats.get("avg_processing_time", 0) or 0

        if historical_time > 0 and recent_time > historical_time * 1.5:
            anomalies.append(
                {
                    "type": "processing_time_increase",
                    "recent_time": recent_time,
                    "historical_time": historical_time,
                    "increase_percentage": (recent_time - historical_time)
                    / historical_time,
                }
            )

        result = {
            "status": "success",
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies,
            "checked_at": datetime.utcnow().isoformat(),
        }

        if anomalies:
            logger.warning(f"Detected {len(anomalies)} anomalies in AI performance")
        else:
            logger.info("No anomalies detected in AI performance")

        return result

    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3) from e
