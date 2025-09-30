"""Event streaming system using Redis Streams for real-time AI event processing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import redis.asyncio as redis
import structlog
from redis.asyncio import Redis

logger = structlog.get_logger(__name__)


class EventType(str, Enum):
    """Types of AI events that can be streamed."""

    AI_INTERACTION = "ai_interaction"
    AI_FAILURE = "ai_failure"
    USER_FEEDBACK = "user_feedback"
    MODEL_UPDATE = "model_update"
    ACCURACY_ALERT = "accuracy_alert"
    PERFORMANCE_ALERT = "performance_alert"
    CATEGORY_LEARNED = "category_learned"
    BATCH_PROCESSED = "batch_processed"


@dataclass
class AIEvent:
    """Base class for AI events."""

    event_id: str
    event_type: EventType
    timestamp: datetime
    data: dict[str, Any]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for streaming."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AIEvent:
        """Create event from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data["data"],
            metadata=data["metadata"],
        )


class EventStream:
    """Redis Streams-based event streaming system."""

    def __init__(self, redis_client: Redis, stream_prefix: str = "ai_events") -> None:
        """Initialize event stream."""
        self.redis = redis_client
        self.stream_prefix = stream_prefix
        self._consumers: dict[str, str] = {}  # consumer_name -> group_name

    def _get_stream_name(self, event_type: EventType) -> str:
        """Get stream name for event type."""
        return f"{self.stream_prefix}:{event_type.value}"

    async def publish_event(self, event: AIEvent) -> str:
        """Publish an event to the appropriate stream."""
        try:
            stream_name = self._get_stream_name(event.event_type)
            event_data = event.to_dict()

            # Convert to Redis-compatible format
            redis_data = {"payload": json.dumps(event_data)}

            # Add to stream
            message_id = await self.redis.xadd(stream_name, redis_data)

            logger.info(
                "Published AI event",
                event_type=event.event_type.value,
                event_id=event.event_id,
                stream=stream_name,
                message_id=message_id,
            )

            return message_id

        except Exception as e:
            logger.error(f"Failed to publish event: {e}", event_id=event.event_id)
            raise

    async def create_consumer_group(
        self, event_type: EventType, group_name: str, start_id: str = "0"
    ) -> None:
        """Create a consumer group for an event type."""
        try:
            stream_name = self._get_stream_name(event_type)
            await self.redis.xgroup_create(
                stream_name, group_name, id=start_id, mkstream=True
            )
            logger.info(f"Created consumer group {group_name} for {stream_name}")

        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group {group_name} already exists")
            else:
                logger.error(f"Failed to create consumer group: {e}")
                raise

    async def consume_events(
        self,
        event_type: EventType,
        group_name: str,
        consumer_name: str,
        count: int = 10,
        block: int = 1000,
    ) -> list[AIEvent]:
        """Consume events from a stream."""
        try:
            stream_name = self._get_stream_name(event_type)

            # Read from stream
            messages = await self.redis.xreadgroup(
                group_name,
                consumer_name,
                {stream_name: ">"},
                count=count,
                block=block,
            )

            events = []
            for _stream, msgs in messages:
                for msg_id, fields in msgs:
                    try:
                        payload = json.loads(fields[b"payload"])
                        event = AIEvent.from_dict(payload)
                        events.append(event)

                        # Acknowledge message
                        await self.redis.xack(stream_name, group_name, msg_id)

                    except Exception as e:
                        logger.error(f"Failed to process message {msg_id}: {e}")
                        continue

            if events:
                logger.debug(f"Consumed {len(events)} events from {stream_name}")

            return events

        except Exception as e:
            logger.error(f"Failed to consume events: {e}")
            return []

    async def get_stream_info(self, event_type: EventType) -> dict[str, Any]:
        """Get information about a stream."""
        try:
            stream_name = self._get_stream_name(event_type)
            info = await self.redis.xinfo_stream(stream_name)
            return {
                "stream_name": stream_name,
                "length": info.get("length", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry"),
                "groups": info.get("groups", 0),
            }
        except redis.ResponseError:
            return {"stream_name": stream_name, "length": 0, "exists": False}

    async def get_pending_messages(
        self, event_type: EventType, group_name: str
    ) -> list[dict[str, Any]]:
        """Get pending messages for a consumer group."""
        try:
            stream_name = self._get_stream_name(event_type)
            pending = await self.redis.xpending(stream_name, group_name)
            return {
                "stream_name": stream_name,
                "group_name": group_name,
                "pending_count": pending.get("pending", 0),
                "min_idle_time": pending.get("min-idle-time", 0),
                "max_idle_time": pending.get("max-idle-time", 0),
            }
        except redis.ResponseError as e:
            logger.error(f"Failed to get pending messages: {e}")
            return {}

    async def cleanup_old_events(
        self, event_type: EventType, max_length: int = 10000
    ) -> int:
        """Cleanup old events from stream to prevent memory issues."""
        try:
            stream_name = self._get_stream_name(event_type)
            result = await self.redis.xtrim(
                stream_name, maxlen=max_length, approximate=True
            )

            if result > 0:
                logger.info(f"Trimmed {result} old events from {stream_name}")

            return result

        except Exception as e:
            logger.error(f"Failed to cleanup old events: {e}")
            return 0


class AIEventPublisher:
    """High-level interface for publishing AI events."""

    def __init__(self, event_stream: EventStream) -> None:
        """Initialize AI event publisher."""
        self.event_stream = event_stream

    async def publish_ai_interaction(
        self,
        interaction_id: str,
        input_text: str,
        language: str,
        ai_response: dict[str, Any],
        processing_time_ms: int,
        confidence: float,
        model_version: str,
    ) -> None:
        """Publish an AI interaction event."""
        import uuid

        event = AIEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.AI_INTERACTION,
            timestamp=datetime.utcnow(),
            data={
                "interaction_id": interaction_id,
                "input_text": input_text,
                "language": language,
                "ai_response": ai_response,
                "processing_time_ms": processing_time_ms,
                "confidence": confidence,
                "model_version": model_version,
            },
            metadata={
                "source": "ai_service",
                "version": "1.0.0",
            },
        )

        await self.event_stream.publish_event(event)

    async def publish_ai_failure(
        self,
        interaction_id: str,
        input_text: str,
        language: str,
        error_message: str,
        error_type: str,
    ) -> None:
        """Publish an AI failure event."""
        import uuid

        event = AIEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.AI_FAILURE,
            timestamp=datetime.utcnow(),
            data={
                "interaction_id": interaction_id,
                "input_text": input_text,
                "language": language,
                "error_message": error_message,
                "error_type": error_type,
            },
            metadata={
                "source": "ai_service",
                "severity": "high",
            },
        )

        await self.event_stream.publish_event(event)

    async def publish_user_feedback(
        self,
        training_data_id: str,
        original_data: dict[str, Any],
        corrected_data: dict[str, Any],
        feedback_type: str,
    ) -> None:
        """Publish a user feedback event."""
        import uuid

        event = AIEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.USER_FEEDBACK,
            timestamp=datetime.utcnow(),
            data={
                "training_data_id": training_data_id,
                "original_data": original_data,
                "corrected_data": corrected_data,
                "feedback_type": feedback_type,
            },
            metadata={
                "source": "ai_service",
                "priority": "high",
            },
        )

        await self.event_stream.publish_event(event)

    async def publish_accuracy_alert(
        self,
        accuracy_score: float,
        threshold: float,
        language: str,
        sample_size: int,
    ) -> None:
        """Publish an accuracy alert event."""
        import uuid

        event = AIEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ACCURACY_ALERT,
            timestamp=datetime.utcnow(),
            data={
                "accuracy_score": accuracy_score,
                "threshold": threshold,
                "language": language,
                "sample_size": sample_size,
            },
            metadata={
                "source": "ai_service",
                "alert_type": "accuracy_degradation",
                "severity": "medium" if accuracy_score > 0.7 else "high",
            },
        )

        await self.event_stream.publish_event(event)

    async def publish_category_learned(
        self,
        ai_category: str,
        correct_category: str,
        confidence: float,
        frequency: int,
    ) -> None:
        """Publish a category learning event."""
        import uuid

        event = AIEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.CATEGORY_LEARNED,
            timestamp=datetime.utcnow(),
            data={
                "ai_category": ai_category,
                "correct_category": correct_category,
                "confidence": confidence,
                "frequency": frequency,
            },
            metadata={
                "source": "ai_service",
                "learning_type": "category_mapping",
            },
        )

        await self.event_stream.publish_event(event)
