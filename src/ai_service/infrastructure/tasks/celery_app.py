"""Celery application for background AI tasks."""

from __future__ import annotations

from typing import Any

import structlog
from celery import Celery

from ...core.config.settings import Settings

logger = structlog.get_logger(__name__)

# Initialize settings
settings = Settings()

# Create Celery app
celery_app = Celery(
    "ai_service",
    broker=f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
    backend=f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
    include=[
        "ai_service.infrastructure.tasks.ai_tasks",
        "ai_service.infrastructure.tasks.model_tasks",
        "ai_service.infrastructure.tasks.monitoring_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "ai_service.infrastructure.tasks.ai_tasks.*": {"queue": "ai_processing"},
        "ai_service.infrastructure.tasks.model_tasks.*": {"queue": "model_training"},
        "ai_service.infrastructure.tasks.monitoring_tasks.*": {"queue": "monitoring"},
    },
    # Task execution
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Result backend configuration
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    # Beat schedule for periodic tasks
    beat_schedule={
        "analyze-ai-performance": {
            "task": "ai_service.infrastructure.tasks.monitoring_tasks.analyze_ai_performance",
            "schedule": 300.0,  # Every 5 minutes
        },
        "update-category-mappings": {
            "task": "ai_service.infrastructure.tasks.ai_tasks.update_category_mappings",
            "schedule": 900.0,  # Every 15 minutes
        },
        "cleanup-old-events": {
            "task": "ai_service.infrastructure.tasks.monitoring_tasks.cleanup_old_events",
            "schedule": 3600.0,  # Every hour
        },
        "retrain-models": {
            "task": "ai_service.infrastructure.tasks.model_tasks.retrain_models",
            "schedule": 86400.0,  # Every 24 hours
        },
        "generate-performance-report": {
            "task": "ai_service.infrastructure.tasks.monitoring_tasks.generate_performance_report",
            "schedule": 21600.0,  # Every 6 hours
        },
    },
)


# Task base class with enhanced error handling
class BaseTask(celery_app.Task):
    """Base task class with enhanced error handling and logging."""

    def on_success(
        self, retval: Any, task_id: str, _args: tuple, _kwargs: dict
    ) -> None:
        """Called when task succeeds."""
        logger.info(
            "Task completed successfully",
            task_id=task_id,
            task_name=self.name,
            result=retval,
        )

    def on_failure(
        self, exc: Exception, task_id: str, _args: tuple, _kwargs: dict, _einfo: Any
    ) -> None:
        """Called when task fails."""
        logger.error(
            "Task failed",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
            args=_args,
            kwargs=_kwargs,
        )

    def on_retry(
        self, exc: Exception, task_id: str, _args: tuple, _kwargs: dict, _einfo: Any
    ) -> None:
        """Called when task is retried."""
        logger.warning(
            "Task retrying",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
            retry_count=self.request.retries,
        )


# Set base task class
celery_app.Task = BaseTask

if __name__ == "__main__":
    celery_app.start()
