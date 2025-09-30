"""Simple tests to boost coverage for low-coverage files."""

from decimal import Decimal

import pytest

from src.ai_service.domain.entities.spending_entry import SpendingEntry, SpendingEntryId
from src.ai_service.domain.value_objects.money import Currency, Money
from src.ai_service.domain.value_objects.processing_method import ProcessingMethod
from src.ai_service.domain.value_objects.spending_category import SpendingCategory


class TestSimpleCoverageBoost:
    """Simple tests to boost coverage."""

    def test_processing_method_enum_values(self):
        """Test ProcessingMethod enum values exist."""
        # Test that we can access enum values
        assert ProcessingMethod.MANUAL_ENTRY
        assert ProcessingMethod.OCR_PROCESSING
        assert ProcessingMethod.AI_ENHANCED
        assert ProcessingMethod.BATCH_IMPORT

        # Test string values
        assert isinstance(ProcessingMethod.MANUAL_ENTRY.value, str)
        assert isinstance(ProcessingMethod.OCR_PROCESSING.value, str)

    def test_spending_category_enum_values(self):
        """Test SpendingCategory enum values exist."""
        # Test that we can access enum values
        assert SpendingCategory.FOOD_DINING
        assert SpendingCategory.TRANSPORTATION
        assert SpendingCategory.GROCERIES

        # Test string values
        assert isinstance(SpendingCategory.FOOD_DINING.value, str)
        assert isinstance(SpendingCategory.TRANSPORTATION.value, str)

    def test_money_edge_cases(self):
        """Test Money edge cases for coverage."""
        # Test zero money
        zero_money = Money(amount=Decimal("0"), currency=Currency.USD)
        assert zero_money.is_zero()

        # Test positive check
        positive_money = Money.from_float(10.0, Currency.USD)
        assert positive_money.is_positive()

        # Test absolute value
        abs_money = positive_money.abs()
        assert abs_money.amount == positive_money.amount

    def test_spending_entry_id_methods(self):
        """Test SpendingEntryId methods for coverage."""
        # Test generate
        entry_id = SpendingEntryId.generate()
        assert isinstance(entry_id.value, str)

        # Test from_string
        entry_id2 = SpendingEntryId.from_string(entry_id.value)
        assert entry_id2.value == entry_id.value

        # Test repr
        repr_str = repr(entry_id)
        assert "SpendingEntryId" in repr_str

    def test_spending_entry_basic_methods(self):
        """Test SpendingEntry basic methods for coverage."""
        entry = SpendingEntry.create(
            merchant="Test Merchant",
            amount=Money.from_float(100.0, Currency.USD),
            category=SpendingCategory.FOOD_DINING,
            description="Test transaction",
        )

        # Test validate method
        entry.validate()  # Should not raise

        # Test to_dict
        entry_dict = entry.to_dict()
        assert isinstance(entry_dict, dict)
        assert entry_dict["merchant"] == "Test Merchant"

        # Test string representation
        str_repr = str(entry)
        assert isinstance(str_repr, str)

    def test_spending_entry_update_methods(self):
        """Test SpendingEntry update methods for coverage."""
        entry = SpendingEntry.create(
            merchant="Old Merchant",
            amount=Money.from_float(100.0, Currency.USD),
            category=SpendingCategory.FOOD_DINING,
            description="Old description",
        )

        # Test update_merchant
        updated_entry = entry.update_merchant("New Merchant")
        assert updated_entry.merchant == "New Merchant"
        assert entry.merchant == "Old Merchant"  # Original unchanged

        # Test update_description
        updated_entry2 = entry.update_description("New description")
        assert updated_entry2.description == "New description"
        assert entry.description == "Old description"  # Original unchanged

    def test_spending_entry_from_dict(self):
        """Test SpendingEntry from_dict for coverage."""
        data = {
            "merchant": "Test Merchant",
            "amount": 100.0,
            "currency": "USD",
            "category": "Food & Dining",
            "description": "Test description",
            "payment_method": "Credit Card",
            "confidence": 0.9,
            "processing_method": "manual_entry",
            "transaction_date": "2023-01-01T12:00:00",
        }

        entry = SpendingEntry.from_dict(data)
        assert entry.merchant == "Test Merchant"
        assert entry.amount.amount == Decimal("100.0")
        assert entry.category == SpendingCategory.FOOD_DINING

    def test_money_division(self):
        """Test Money division for coverage."""
        money = Money.from_float(100.0, Currency.USD)

        # Test division
        half = money.divide(2)
        assert half.amount == Decimal("50.0")

        # Test division by zero should raise
        from decimal import InvalidOperation

        with pytest.raises(InvalidOperation):
            money.divide(0)

    def test_money_from_dict(self):
        """Test Money from_dict for coverage."""
        data = {"amount": 123.45, "currency": "USD"}
        money = Money.from_dict(data)

        assert money.amount == Decimal("123.45")
        assert money.currency == Currency.USD

    def test_processing_method_iteration(self):
        """Test ProcessingMethod iteration for coverage."""
        # Test that we can iterate over all processing methods
        methods = list(ProcessingMethod)
        assert len(methods) > 0

        # Test that each method has a string value
        for method in methods:
            assert isinstance(method.value, str)
            assert len(method.value) > 0

    def test_spending_category_iteration(self):
        """Test SpendingCategory iteration for coverage."""
        # Test that we can iterate over all categories
        categories = list(SpendingCategory)
        assert len(categories) > 0

        # Test that each category has a string value
        for category in categories:
            assert isinstance(category.value, str)
            assert len(category.value) > 0

    def test_currency_iteration(self):
        """Test Currency iteration for coverage."""
        # Test that we can iterate over all currencies
        currencies = list(Currency)
        assert len(currencies) > 0

        # Test that each currency has a string value
        for currency in currencies:
            assert isinstance(currency.value, str)
            assert len(currency.value) > 0
