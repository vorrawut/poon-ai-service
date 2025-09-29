"""Simple unit tests for SpendingEntry domain entity."""

from datetime import datetime

import pytest

from ai_service.domain.entities.spending_entry import SpendingEntry, SpendingEntryId
from ai_service.domain.value_objects.confidence import ConfidenceScore
from ai_service.domain.value_objects.money import Currency, Money
from ai_service.domain.value_objects.processing_method import ProcessingMethod
from ai_service.domain.value_objects.spending_category import (
    PaymentMethod,
    SpendingCategory,
)


@pytest.mark.unit
class TestSpendingEntryId:
    """Test SpendingEntryId value object."""

    def test_spending_entry_id_creation(self):
        """Test creating SpendingEntryId."""
        # Auto-generate UUID
        entry_id = SpendingEntryId()
        assert len(entry_id.value) == 36  # UUID format
        assert str(entry_id) == entry_id.value

    def test_spending_entry_id_from_string(self):
        """Test creating SpendingEntryId from string."""
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"
        entry_id = SpendingEntryId(uuid_str)
        assert entry_id.value == uuid_str

    def test_spending_entry_id_validation(self):
        """Test SpendingEntryId validation."""
        # Invalid UUID format should raise ValueError
        with pytest.raises(ValueError, match="Invalid UUID format"):
            SpendingEntryId("invalid-uuid")

    def test_spending_entry_id_equality(self):
        """Test SpendingEntryId equality."""
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"
        id1 = SpendingEntryId(uuid_str)
        id2 = SpendingEntryId(uuid_str)
        id3 = SpendingEntryId()

        assert id1 == id2
        assert id1 != id3


@pytest.mark.unit
class TestSpendingEntry:
    """Test SpendingEntry domain entity."""

    def test_spending_entry_creation(self):
        """Test creating a SpendingEntry."""
        entry = SpendingEntry(
            amount=Money.from_float(120.50, Currency.THB),
            merchant="Test Cafe",
            description="Coffee and pastry",
            transaction_date=datetime(2024, 1, 15, 10, 30, 0),
            category=SpendingCategory.FOOD_DINING,
            payment_method=PaymentMethod.CREDIT_CARD,
            confidence=ConfidenceScore.high(),
            processing_method=ProcessingMethod.MANUAL_ENTRY,
        )

        assert entry.amount.to_float() == 120.50
        assert entry.merchant == "Test Cafe"
        assert entry.description == "Coffee and pastry"
        assert entry.category == SpendingCategory.FOOD_DINING
        assert entry.payment_method == PaymentMethod.CREDIT_CARD
        assert entry.confidence.is_high()
        assert entry.processing_method == ProcessingMethod.MANUAL_ENTRY
        assert isinstance(entry.id, SpendingEntryId)
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.updated_at, datetime)

    def test_spending_entry_validation(self):
        """Test SpendingEntry business rule validation."""
        # Empty merchant should raise ValueError
        with pytest.raises(ValueError, match="Merchant cannot be empty"):
            SpendingEntry(
                amount=Money.from_float(100.0, Currency.THB),
                merchant="",
                description="Test",
                transaction_date=datetime.utcnow(),
                category=SpendingCategory.MISCELLANEOUS,
                payment_method=PaymentMethod.CASH,
                confidence=ConfidenceScore.medium(),
                processing_method=ProcessingMethod.MANUAL_ENTRY,
            )

    def test_spending_entry_amount_update(self):
        """Test updating spending entry amount."""
        entry = SpendingEntry(
            amount=Money.from_float(100.0, Currency.THB),
            merchant="Test Merchant",
            description="Test transaction",
            transaction_date=datetime.utcnow(),
            category=SpendingCategory.MISCELLANEOUS,
            payment_method=PaymentMethod.CASH,
            confidence=ConfidenceScore.medium(),
            processing_method=ProcessingMethod.MANUAL_ENTRY,
        )

        original_updated_at = entry.updated_at
        new_amount = Money.from_float(150.0, Currency.THB)

        entry.update_amount(new_amount)

        assert entry.amount.to_float() == 150.0
        assert entry.updated_at > original_updated_at

    def test_spending_entry_serialization(self):
        """Test spending entry serialization."""
        entry = SpendingEntry(
            amount=Money.from_float(120.50, Currency.THB),
            merchant="Test Cafe",
            description="Coffee and pastry",
            transaction_date=datetime(2024, 1, 15, 10, 30, 0),
            category=SpendingCategory.FOOD_DINING,
            payment_method=PaymentMethod.CREDIT_CARD,
            confidence=ConfidenceScore.high(),
            processing_method=ProcessingMethod.MANUAL_ENTRY,
        )

        entry_dict = entry.to_dict()

        # Check required fields
        assert entry_dict["id"] == entry.id.value
        assert entry_dict["amount"] == 120.50
        assert entry_dict["currency"] == "THB"
        assert entry_dict["merchant"] == "Test Cafe"
        assert entry_dict["description"] == "Coffee and pastry"
        assert entry_dict["category"] == "Food & Dining"
        assert entry_dict["payment_method"] == "Credit Card"
        assert entry_dict["confidence"] >= 0.8  # High confidence
        assert entry_dict["processing_method"] == "manual_entry"
        assert "created_at" in entry_dict
        assert "updated_at" in entry_dict
