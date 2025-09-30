"""Unit tests for base domain events."""

from datetime import datetime
from uuid import uuid4

import pytest

from ai_service.domain.events.base import SpendingDomainEvent


class TestSpendingDomainEvent:
    """Test SpendingDomainEvent base class."""

    def test_event_creation(self):
        """Test creating a base spending domain event."""
        entry_id = str(uuid4())
        event = SpendingDomainEvent(entry_id=entry_id)

        assert event.entry_id == entry_id
        assert isinstance(event.event_id, str)
        assert isinstance(event.occurred_at, datetime)
        assert event.event_version == 1
        assert event.event_type == "base_spending_event"

    def test_event_with_custom_values(self):
        """Test creating event with custom values."""
        entry_id = str(uuid4())
        custom_event_id = str(uuid4())
        custom_time = datetime.utcnow()

        event = SpendingDomainEvent(
            entry_id=entry_id,
            event_id=custom_event_id,
            occurred_at=custom_time,
            event_version=2,
        )

        assert event.entry_id == entry_id
        assert event.event_id == custom_event_id
        assert event.occurred_at == custom_time
        assert event.event_version == 2

    def test_get_event_data(self):
        """Test getting event data payload."""
        entry_id = str(uuid4())
        event = SpendingDomainEvent(entry_id=entry_id)

        data = event.get_event_data()
        assert data == {"entry_id": entry_id}

    def test_get_aggregate_id(self):
        """Test getting aggregate ID."""
        entry_id = str(uuid4())
        event = SpendingDomainEvent(entry_id=entry_id)

        assert event.get_aggregate_id() == entry_id

    def test_to_dict(self):
        """Test converting event to dictionary."""
        entry_id = str(uuid4())
        event = SpendingDomainEvent(entry_id=entry_id)

        event_dict = event.to_dict()

        assert event_dict["event_id"] == event.event_id
        assert event_dict["event_type"] == "base_spending_event"
        assert isinstance(event_dict["occurred_at"], str)
        assert event_dict["event_version"] == 1
        assert event_dict["event_data"] == {"entry_id": entry_id}

    def test_event_immutability(self):
        """Test that events are immutable."""
        entry_id = str(uuid4())
        event = SpendingDomainEvent(entry_id=entry_id)

        # Should not be able to modify frozen dataclass
        with pytest.raises(AttributeError):
            event.entry_id = "new-id"

        with pytest.raises(AttributeError):
            event.event_version = 2

    def test_event_id_uniqueness(self):
        """Test that each event gets a unique ID."""
        entry_id = str(uuid4())
        event1 = SpendingDomainEvent(entry_id=entry_id)
        event2 = SpendingDomainEvent(entry_id=entry_id)

        assert event1.event_id != event2.event_id

    def test_occurred_at_auto_generation(self):
        """Test that occurred_at is automatically set."""
        entry_id = str(uuid4())
        before_creation = datetime.utcnow()
        event = SpendingDomainEvent(entry_id=entry_id)
        after_creation = datetime.utcnow()

        assert before_creation <= event.occurred_at <= after_creation

    def test_event_equality(self):
        """Test event equality comparison."""
        entry_id = str(uuid4())
        event_id = str(uuid4())
        occurred_at = datetime.utcnow()

        event1 = SpendingDomainEvent(
            entry_id=entry_id,
            event_id=event_id,
            occurred_at=occurred_at,
        )
        event2 = SpendingDomainEvent(
            entry_id=entry_id,
            event_id=event_id,
            occurred_at=occurred_at,
        )

        assert event1 == event2

    def test_event_inequality(self):
        """Test event inequality comparison."""
        entry_id = str(uuid4())
        event1 = SpendingDomainEvent(entry_id=entry_id)
        event2 = SpendingDomainEvent(entry_id=entry_id)

        # Different event IDs should make them unequal
        assert event1 != event2
