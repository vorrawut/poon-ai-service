"""Unit tests for domain events."""

from datetime import datetime
from uuid import uuid4

import pytest

from ai_service.domain.events.spending_events import (
    SpendingBatchProcessed,
    SpendingEntryAIEnhanced,
    SpendingEntryCreated,
    SpendingEntryUpdated,
)


class TestSpendingEntryCreated:
    """Test SpendingEntryCreated domain event."""

    def test_event_creation(self):
        """Test creating a spending entry created event."""
        entry_id = str(uuid4())
        event = SpendingEntryCreated(
            entry_id=entry_id,
            amount=100.50,
            merchant="Test Merchant",
            category="Food & Dining",
        )

        assert event.entry_id == entry_id
        assert event.amount == 100.50
        assert event.merchant == "Test Merchant"
        assert event.category == "Food & Dining"
        assert event.event_type == "spending_entry.created"
        assert isinstance(event.event_id, str)
        assert isinstance(event.occurred_at, datetime)
        assert event.event_version == 1

    def test_event_creation_with_defaults(self):
        """Test creating event with default values."""
        entry_id = str(uuid4())
        event = SpendingEntryCreated(entry_id=entry_id)

        assert event.entry_id == entry_id
        assert event.amount == 0.0
        assert event.merchant == ""
        assert event.category == ""
        assert event.event_type == "spending_entry.created"

    def test_get_event_data(self):
        """Test getting event data payload."""
        entry_id = str(uuid4())
        event = SpendingEntryCreated(
            entry_id=entry_id,
            amount=75.25,
            merchant="Coffee Shop",
            category="Food",
        )

        data = event.get_event_data()
        assert data["entry_id"] == entry_id
        assert data["amount"] == 75.25
        assert data["merchant"] == "Coffee Shop"
        assert data["category"] == "Food"

    def test_to_dict(self):
        """Test converting event to dictionary."""
        entry_id = str(uuid4())
        event = SpendingEntryCreated(
            entry_id=entry_id,
            amount=50.0,
            merchant="Gas Station",
            category="Transportation",
        )

        event_dict = event.to_dict()
        assert event_dict["event_id"] == event.event_id
        assert event_dict["event_type"] == "spending_entry.created"
        assert isinstance(event_dict["occurred_at"], str)
        assert event_dict["event_version"] == 1
        assert "event_data" in event_dict
        assert event_dict["event_data"]["entry_id"] == entry_id

    def test_get_aggregate_id(self):
        """Test getting aggregate ID."""
        entry_id = str(uuid4())
        event = SpendingEntryCreated(entry_id=entry_id)
        assert event.get_aggregate_id() == entry_id


class TestSpendingEntryUpdated:
    """Test SpendingEntryUpdated domain event."""

    def test_event_creation(self):
        """Test creating a spending entry updated event."""
        entry_id = str(uuid4())
        event = SpendingEntryUpdated(
            entry_id=entry_id,
            field_updated="amount",
            old_value=100.0,
            new_value=150.0,
        )

        assert event.entry_id == entry_id
        assert event.field_updated == "amount"
        assert event.old_value == 100.0
        assert event.new_value == 150.0
        assert event.event_type == "spending_entry.updated"

    def test_event_creation_with_defaults(self):
        """Test creating event with default values."""
        entry_id = str(uuid4())
        event = SpendingEntryUpdated(entry_id=entry_id)

        assert event.entry_id == entry_id
        assert event.field_updated == ""
        assert event.old_value is None
        assert event.new_value is None

    def test_get_event_data(self):
        """Test getting event data payload."""
        entry_id = str(uuid4())
        event = SpendingEntryUpdated(
            entry_id=entry_id,
            field_updated="merchant",
            old_value="Old Shop",
            new_value="New Shop",
        )

        data = event.get_event_data()
        assert data["entry_id"] == entry_id
        assert data["field_updated"] == "merchant"
        assert data["old_value"] == "Old Shop"
        assert data["new_value"] == "New Shop"


class TestSpendingEntryAIEnhanced:
    """Test SpendingEntryAIEnhanced domain event."""

    def test_event_creation(self):
        """Test creating an AI enhanced event."""
        entry_id = str(uuid4())
        event = SpendingEntryAIEnhanced(
            entry_id=entry_id,
            ai_model="llama2",
            confidence_before=0.6,
            confidence_after=0.9,
            processing_time_ms=1500,
        )

        assert event.entry_id == entry_id
        assert event.ai_model == "llama2"
        assert event.confidence_before == 0.6
        assert event.confidence_after == 0.9
        assert event.processing_time_ms == 1500
        assert event.event_type == "spending_entry.ai_enhanced"

    def test_event_creation_with_defaults(self):
        """Test creating event with default values."""
        entry_id = str(uuid4())
        event = SpendingEntryAIEnhanced(entry_id=entry_id)

        assert event.entry_id == entry_id
        assert event.ai_model == ""
        assert event.confidence_before == 0.0
        assert event.confidence_after == 0.0
        assert event.processing_time_ms == 0

    def test_get_event_data(self):
        """Test getting event data payload."""
        entry_id = str(uuid4())
        event = SpendingEntryAIEnhanced(
            entry_id=entry_id,
            ai_model="gpt-4",
            confidence_before=0.5,
            confidence_after=0.85,
            processing_time_ms=2000,
        )

        data = event.get_event_data()
        assert data["entry_id"] == entry_id
        assert data["ai_model"] == "gpt-4"
        assert data["confidence_before"] == 0.5
        assert data["confidence_after"] == 0.85
        assert data["processing_time_ms"] == 2000


class TestSpendingBatchProcessed:
    """Test SpendingBatchProcessed domain event."""

    def test_event_creation(self):
        """Test creating a batch processed event."""
        entry_id = str(uuid4())
        batch_id = str(uuid4())
        event = SpendingBatchProcessed(
            entry_id=entry_id,
            batch_id=batch_id,
            total_entries=100,
            successful_entries=95,
            failed_entries=5,
            processing_method="ai_enhanced",
        )

        assert event.entry_id == entry_id
        assert event.batch_id == batch_id
        assert event.total_entries == 100
        assert event.successful_entries == 95
        assert event.failed_entries == 5
        assert event.processing_method == "ai_enhanced"
        assert event.event_type == "spending_batch.processed"

    def test_event_creation_with_defaults(self):
        """Test creating event with default values."""
        entry_id = str(uuid4())
        event = SpendingBatchProcessed(entry_id=entry_id)

        assert event.entry_id == entry_id
        assert event.batch_id == ""
        assert event.total_entries == 0
        assert event.successful_entries == 0
        assert event.failed_entries == 0
        assert event.processing_method == ""

    def test_get_event_data(self):
        """Test getting event data payload."""
        entry_id = str(uuid4())
        batch_id = str(uuid4())
        event = SpendingBatchProcessed(
            entry_id=entry_id,
            batch_id=batch_id,
            total_entries=50,
            successful_entries=48,
            failed_entries=2,
            processing_method="manual",
        )

        data = event.get_event_data()
        assert data["entry_id"] == entry_id
        assert data["batch_id"] == batch_id
        assert data["total_entries"] == 50
        assert data["successful_entries"] == 48
        assert data["failed_entries"] == 2
        assert data["processing_method"] == "manual"

    def test_event_immutability(self):
        """Test that events are immutable."""
        entry_id = str(uuid4())
        event = SpendingBatchProcessed(
            entry_id=entry_id,
            batch_id="test-batch",
            total_entries=10,
        )

        # Should not be able to modify frozen dataclass
        with pytest.raises(AttributeError):
            event.total_entries = 20

    def test_event_string_representation(self):
        """Test event string representation."""
        entry_id = str(uuid4())
        event = SpendingEntryCreated(
            entry_id=entry_id,
            amount=100.0,
            merchant="Test",
        )

        # Should include class name and entry ID
        str_repr = str(event)
        assert "SpendingEntryCreated" in str_repr
        assert entry_id in str_repr
