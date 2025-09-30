"""Comprehensive unit tests for domain entities."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from ai_service.domain.entities.spending_entry import SpendingEntry, SpendingEntryId
from ai_service.domain.value_objects.money import Currency, Money
from ai_service.domain.value_objects.processing_method import ProcessingMethod
from ai_service.domain.value_objects.spending_category import SpendingCategory


@pytest.mark.unit
class TestSpendingEntryId:
    """Comprehensive tests for SpendingEntryId."""

    def test_id_generation(self):
        """Test ID generation."""
        id1 = SpendingEntryId.generate()
        id2 = SpendingEntryId.generate()

        assert id1 != id2
        assert isinstance(id1.value, str)
        assert len(id1.value) == 36  # UUID4 format

    def test_id_from_string(self):
        """Test creating ID from string."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        entry_id = SpendingEntryId.from_string(uuid_str)

        assert entry_id.value == uuid_str

    def test_id_validation(self):
        """Test ID validation."""
        # Valid UUID
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        entry_id = SpendingEntryId.from_string(valid_uuid)
        assert entry_id.value == valid_uuid

        # Invalid UUID format
        with pytest.raises(ValueError, match="Invalid UUID format"):
            SpendingEntryId.from_string("invalid-uuid")

        with pytest.raises(ValueError, match="Invalid UUID format"):
            SpendingEntryId.from_string("")

    def test_id_equality(self):
        """Test ID equality comparison."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        id1 = SpendingEntryId.from_string(uuid_str)
        id2 = SpendingEntryId.from_string(uuid_str)
        id3 = SpendingEntryId.generate()

        assert id1 == id2
        assert id1 != id3
        assert hash(id1) == hash(id2)
        assert hash(id1) != hash(id3)

    def test_id_string_representation(self):
        """Test string representation."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        entry_id = SpendingEntryId.from_string(uuid_str)

        assert str(entry_id) == uuid_str
        assert repr(entry_id) == f"SpendingEntryId({uuid_str})"


@pytest.mark.unit
class TestSpendingEntry:
    """Comprehensive tests for SpendingEntry."""

    @pytest.fixture
    def sample_money(self):
        """Create sample money."""
        return Money.from_float(25.50, Currency.USD)

    @pytest.fixture
    def sample_entry(self, sample_money):
        """Create sample spending entry."""
        return SpendingEntry.create(
            merchant="Test Cafe",
            amount=sample_money,
            category=SpendingCategory.FOOD_DINING,
            description="Coffee and pastry",
        )

    def test_entry_creation(self, sample_money):
        """Test entry creation."""
        entry = SpendingEntry.create(
            merchant="Test Merchant",
            amount=sample_money,
            category=SpendingCategory.FOOD_DINING,
            description="Test description",
        )

        assert entry.merchant == "Test Merchant"
        assert entry.amount == sample_money
        assert entry.category == SpendingCategory.FOOD_DINING
        assert entry.description == "Test description"
        assert isinstance(entry.id, SpendingEntryId)
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.updated_at, datetime)
        assert entry.processing_method == ProcessingMethod.MANUAL_ENTRY

    def test_entry_creation_with_optional_fields(self, sample_money):
        """Test entry creation with all optional fields."""
        entry = SpendingEntry.create(
            merchant="Test Merchant",
            amount=sample_money,
            category=SpendingCategory.FOOD_DINING,
            description="Test description",
            processing_method=ProcessingMethod.OCR_PROCESSING,
        )

        assert entry.processing_method == ProcessingMethod.OCR_PROCESSING

    def test_entry_creation_minimal(self, sample_money):
        """Test entry creation with minimal fields."""
        entry = SpendingEntry.create(
            merchant="Test Merchant",
            amount=sample_money,
            category=SpendingCategory.FOOD_DINING,
        )

        assert entry.merchant == "Test Merchant"
        assert entry.amount == sample_money
        assert entry.category == SpendingCategory.FOOD_DINING
        assert entry.description is None

    def test_entry_validation(self, sample_money):
        """Test entry validation."""
        # Valid entry
        entry = SpendingEntry.create(
            merchant="Valid Merchant",
            amount=sample_money,
            category=SpendingCategory.FOOD_DINING,
        )
        entry.validate()  # Should not raise

        # Test individual validations
        with pytest.raises(ValueError, match="Merchant cannot be empty"):
            SpendingEntry.create(
                merchant="",
                amount=sample_money,
                category=SpendingCategory.FOOD_DINING,
            )

        with pytest.raises(ValueError, match="Merchant cannot be empty"):
            SpendingEntry.create(
                merchant="   ",
                amount=sample_money,
                category=SpendingCategory.FOOD_DINING,
            )

        # Test long merchant name
        long_merchant = "A" * 256
        with pytest.raises(ValueError, match="Merchant name too long"):
            SpendingEntry.create(
                merchant=long_merchant,
                amount=sample_money,
                category=SpendingCategory.FOOD_DINING,
            )

    def test_amount_updates(self, sample_entry):
        """Test amount update operations."""
        new_amount = Money.from_float(50.00, Currency.USD)
        updated_entry = sample_entry.update_amount(new_amount)

        # Original entry unchanged
        assert sample_entry.amount.amount == Decimal("25.50")

        # New entry has updated amount
        assert updated_entry.amount.amount == Decimal("50.00")
        assert updated_entry.id == sample_entry.id  # Same ID
        assert updated_entry.updated_at > sample_entry.updated_at

    def test_description_updates(self, sample_entry):
        """Test description update operations."""
        new_description = "Updated description"
        updated_entry = sample_entry.update_description(new_description)

        # Original entry unchanged
        assert sample_entry.description == "Coffee and pastry"

        # New entry has updated description
        assert updated_entry.description == new_description
        assert updated_entry.id == sample_entry.id
        assert updated_entry.updated_at > sample_entry.updated_at

    def test_category_updates(self, sample_entry):
        """Test category update operations."""
        new_category = SpendingCategory.TRANSPORTATION
        updated_entry = sample_entry.update_category(new_category)

        # Original entry unchanged
        assert sample_entry.category == SpendingCategory.FOOD_DINING

        # New entry has updated category
        assert updated_entry.category == new_category
        assert updated_entry.id == sample_entry.id
        assert updated_entry.updated_at > sample_entry.updated_at

    def test_processing_method_updates(self, sample_entry):
        """Test processing method updates."""
        new_method = ProcessingMethod.AI_ENHANCED
        updated_entry = sample_entry.update_processing_method(new_method)

        # Original entry unchanged
        assert sample_entry.processing_method == ProcessingMethod.MANUAL_ENTRY

        # New entry has updated method
        assert updated_entry.processing_method == new_method
        assert updated_entry.id == sample_entry.id

    def test_entry_serialization(self, sample_entry):
        """Test entry serialization to dictionary."""
        data = sample_entry.to_dict()

        assert data["id"] == str(sample_entry.id.value)
        assert data["merchant"] == sample_entry.merchant
        assert data["amount"] == float(sample_entry.amount.amount)
        assert data["currency"] == sample_entry.amount.currency.value
        assert data["category"] == sample_entry.category.value
        assert data["description"] == sample_entry.description
        assert "created_at" in data
        assert "updated_at" in data
        assert data["processing_method"] == sample_entry.processing_method.value

    def test_entry_from_dict(self, sample_entry):
        """Test entry creation from dictionary."""
        data = sample_entry.to_dict()

        # Create entry from dict
        recreated_entry = SpendingEntry.from_dict(data)

        assert recreated_entry.id.value == sample_entry.id.value
        assert recreated_entry.merchant == sample_entry.merchant
        assert recreated_entry.amount.amount == sample_entry.amount.amount
        assert recreated_entry.amount.currency == sample_entry.amount.currency
        assert recreated_entry.category == sample_entry.category
        assert recreated_entry.description == sample_entry.description
        assert recreated_entry.processing_method == sample_entry.processing_method

    def test_entry_equality(self, sample_money):
        """Test entry equality comparison."""
        entry1 = SpendingEntry.create(
            merchant="Test Merchant",
            amount=sample_money,
            category=SpendingCategory.FOOD_DINING,
        )

        # Same entry
        entry2 = SpendingEntry.from_dict(entry1.to_dict())
        assert entry1 == entry2

        # Different entry
        entry3 = SpendingEntry.create(
            merchant="Different Merchant",
            amount=sample_money,
            category=SpendingCategory.FOOD_DINING,
        )
        assert entry1 != entry3

    def test_entry_string_representation(self, sample_entry):
        """Test string representation."""
        str_repr = str(sample_entry)
        assert "Test Cafe" in str_repr
        assert "25.50" in str_repr
        assert "USD" in str_repr

        repr_str = repr(sample_entry)
        assert "SpendingEntry" in repr_str
        assert str(sample_entry.id.value) in repr_str

    def test_entry_immutability(self, sample_entry):
        """Test that entries are immutable."""
        original_merchant = sample_entry.merchant
        original_amount = sample_entry.amount

        # Updates should return new instances
        updated_entry = sample_entry.update_amount(
            Money.from_float(100.0, Currency.USD)
        )

        # Original should be unchanged
        assert sample_entry.merchant == original_merchant
        assert sample_entry.amount == original_amount

        # New entry should be different
        assert updated_entry.amount.amount == Decimal("100.0")
        assert updated_entry is not sample_entry

    def test_entry_timestamps(self, sample_money):
        """Test timestamp handling."""
        before_creation = datetime.utcnow()
        entry = SpendingEntry.create(
            merchant="Test Merchant",
            amount=sample_money,
            category=SpendingCategory.FOOD_DINING,
        )
        after_creation = datetime.utcnow()

        # Creation timestamps
        assert before_creation <= entry.created_at <= after_creation
        assert before_creation <= entry.updated_at <= after_creation
        # Allow for small timing differences (microseconds)
        assert abs((entry.created_at - entry.updated_at).total_seconds()) < 0.001

        # Update timestamps
        import time

        time.sleep(0.01)  # Ensure time difference

        updated_entry = entry.update_amount(Money.from_float(50.0, Currency.USD))

        assert updated_entry.created_at == entry.created_at  # Unchanged
        assert updated_entry.updated_at > entry.updated_at  # Updated

    def test_currency_consistency(self, sample_entry):
        """Test currency consistency in updates."""
        # Update with same currency
        new_amount_usd = Money.from_float(50.0, Currency.USD)
        updated_entry = sample_entry.update_amount(new_amount_usd)
        assert updated_entry.amount.currency == Currency.USD

        # Update with different currency
        new_amount_thb = Money.from_float(1000.0, Currency.THB)
        updated_entry_thb = sample_entry.update_amount(new_amount_thb)
        assert updated_entry_thb.amount.currency == Currency.THB

    def test_edge_cases(self, sample_money):
        """Test edge cases and boundary conditions."""
        # Very long description
        long_description = "A" * 1000
        entry = SpendingEntry.create(
            merchant="Test Merchant",
            amount=sample_money,
            category=SpendingCategory.FOOD_DINING,
            description=long_description,
        )
        assert entry.description == long_description

        # Unicode characters
        unicode_merchant = "Café München 🍕"
        unicode_entry = SpendingEntry.create(
            merchant=unicode_merchant,
            amount=sample_money,
            category=SpendingCategory.FOOD_DINING,
        )
        assert unicode_entry.merchant == unicode_merchant

        # Minimum amount
        min_amount = Money.from_float(0.01, Currency.USD)
        min_entry = SpendingEntry.create(
            merchant="Test Merchant",
            amount=min_amount,
            category=SpendingCategory.FOOD_DINING,
        )
        assert min_entry.amount.amount == Decimal("0.01")

    def test_invalid_from_dict(self):
        """Test invalid dictionary data."""
        # Missing required fields
        with pytest.raises(KeyError):
            SpendingEntry.from_dict({})

        # Invalid UUID
        with pytest.raises(ValueError, match="Invalid UUID"):
            SpendingEntry.from_dict(
                {
                    "id": "invalid-uuid",
                    "merchant": "Test",
                    "amount": 10.0,
                    "currency": "USD",
                    "category": "Food & Dining",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )

        # Invalid currency
        with pytest.raises(ValueError, match="Invalid currency"):
            SpendingEntry.from_dict(
                {
                    "id": str(SpendingEntryId.generate().value),
                    "merchant": "Test",
                    "amount": 10.0,
                    "currency": "INVALID",
                    "category": "Food & Dining",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )

    def test_business_rules(self, sample_money):
        """Test business rules and constraints."""
        # Test that created_at is always <= updated_at
        entry = SpendingEntry.create(
            merchant="Test Merchant",
            amount=sample_money,
            category=SpendingCategory.FOOD_DINING,
        )

        assert entry.created_at <= entry.updated_at

        updated_entry = entry.update_amount(Money.from_float(100.0, Currency.USD))
        assert updated_entry.created_at <= updated_entry.updated_at
        assert updated_entry.created_at == entry.created_at  # Should not change

    def test_category_validation_comprehensive(self, sample_money):
        """Test comprehensive category validation."""
        # Test all valid categories
        for category in SpendingCategory:
            entry = SpendingEntry.create(
                merchant="Test Merchant",
                amount=sample_money,
                category=category,
            )
            assert entry.category == category

    def test_processing_method_validation(self, sample_money):
        """Test processing method validation."""
        # Test all valid processing methods
        for method in ProcessingMethod:
            entry = SpendingEntry.create(
                merchant="Test Merchant",
                amount=sample_money,
                category=SpendingCategory.FOOD_DINING,
                processing_method=method,
            )
            assert entry.processing_method == method
