"""Comprehensive unit tests for Money value object."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

import pytest

from ai_service.domain.value_objects.money import Currency, Money


@pytest.mark.unit
class TestCurrency:
    """Test Currency enum."""

    def test_currency_values(self):
        """Test currency enum values."""
        assert Currency.USD.value == "USD"
        assert Currency.THB.value == "THB"
        assert Currency.EUR.value == "EUR"
        assert Currency.GBP.value == "GBP"
        assert Currency.JPY.value == "JPY"

    def test_currency_from_string(self):
        """Test creating currency from string."""
        assert Currency("USD") == Currency.USD
        assert Currency("THB") == Currency.THB

        with pytest.raises(ValueError, match="Invalid currency"):
            Currency("INVALID")

    def test_currency_string_representation(self):
        """Test currency string representation."""
        assert str(Currency.USD) == "USD"
        assert repr(Currency.USD) == "<Currency.USD: 'USD'>"


@pytest.mark.unit
class TestMoney:
    """Comprehensive tests for Money value object."""

    def test_money_creation_from_decimal(self):
        """Test money creation from Decimal."""
        amount = Decimal("25.50")
        money = Money(amount=amount, currency=Currency.USD)

        assert money.amount == amount
        assert money.currency == Currency.USD

    def test_money_creation_from_float(self):
        """Test money creation from float."""
        money = Money.from_float(25.50, Currency.USD)

        assert money.amount == Decimal("25.50")
        assert money.currency == Currency.USD

    def test_money_creation_from_int(self):
        """Test money creation from integer."""
        money = Money.from_float(25, Currency.USD)

        assert money.amount == Decimal("25")
        assert money.currency == Currency.USD

    def test_money_validation_negative(self):
        """Test money validation for negative amounts."""
        with pytest.raises(ValueError, match="Money amount cannot be negative"):
            Money(amount=Decimal("-10.50"), currency=Currency.USD)

        with pytest.raises(ValueError, match="Money amount cannot be negative"):
            Money.from_float(-10.50, Currency.USD)

    def test_money_validation_currency(self):
        """Test money validation for currency."""
        # Valid currency
        money = Money(amount=Decimal("10.50"), currency=Currency.USD)
        assert money.currency == Currency.USD

        # Invalid currency type - this test is no longer valid since we removed runtime type checking
        # The type system now prevents invalid currency types at compile time
        pass

    def test_money_arithmetic_addition(self):
        """Test money addition operations."""
        money1 = Money.from_float(10.50, Currency.USD)
        money2 = Money.from_float(5.25, Currency.USD)

        result = money1.add(money2)

        assert result.amount == Decimal("15.75")
        assert result.currency == Currency.USD

        # Original objects unchanged
        assert money1.amount == Decimal("10.50")
        assert money2.amount == Decimal("5.25")

    def test_money_arithmetic_subtraction(self):
        """Test money subtraction operations."""
        money1 = Money.from_float(10.50, Currency.USD)
        money2 = Money.from_float(5.25, Currency.USD)

        result = money1.subtract(money2)

        assert result.amount == Decimal("5.25")
        assert result.currency == Currency.USD

    def test_money_arithmetic_multiplication(self):
        """Test money multiplication operations."""
        money = Money.from_float(10.50, Currency.USD)

        result = money.multiply(Decimal("2"))

        assert result.amount == Decimal("21.00")
        assert result.currency == Currency.USD

        # Test with float
        result_float = money.multiply(2.5)
        assert result_float.amount == Decimal("26.25")

    def test_money_arithmetic_division(self):
        """Test money division operations."""
        money = Money.from_float(21.00, Currency.USD)

        result = money.divide(Decimal("2"))

        assert result.amount == Decimal("10.50")
        assert result.currency == Currency.USD

        # Test with float
        result_float = money.divide(3.0)
        assert result_float.amount == Decimal("7.00")

    def test_money_arithmetic_different_currencies(self):
        """Test arithmetic operations with different currencies."""
        usd_money = Money.from_float(10.50, Currency.USD)
        thb_money = Money.from_float(100.0, Currency.THB)

        with pytest.raises(ValueError, match="Cannot add different currencies"):
            usd_money.add(thb_money)

        with pytest.raises(ValueError, match="Cannot subtract different currencies"):
            usd_money.subtract(thb_money)

    def test_money_comparison_equal(self):
        """Test money equality comparison."""
        money1 = Money.from_float(10.50, Currency.USD)
        money2 = Money.from_float(10.50, Currency.USD)
        money3 = Money.from_float(10.50, Currency.THB)
        money4 = Money.from_float(15.00, Currency.USD)

        assert money1 == money2
        assert money1 != money3  # Different currency
        assert money1 != money4  # Different amount
        assert money1 != "not money"  # Different type

    def test_money_comparison_ordering(self):
        """Test money ordering comparisons."""
        money1 = Money.from_float(10.50, Currency.USD)
        money2 = Money.from_float(15.00, Currency.USD)
        money3 = Money.from_float(5.25, Currency.USD)

        assert money1 < money2
        assert money2 > money1
        assert money1 > money3
        assert money3 < money1
        assert money1 <= money2
        assert money2 >= money1
        assert money1 >= money3
        assert money3 <= money1

    def test_money_comparison_different_currencies(self):
        """Test comparison with different currencies."""
        usd_money = Money.from_float(10.50, Currency.USD)
        thb_money = Money.from_float(100.0, Currency.THB)

        with pytest.raises(ValueError, match="Cannot compare different currencies"):
            assert usd_money < thb_money

        with pytest.raises(ValueError, match="Cannot compare different currencies"):
            assert usd_money > thb_money

        with pytest.raises(ValueError, match="Cannot compare different currencies"):
            assert usd_money <= thb_money

        with pytest.raises(ValueError, match="Cannot compare different currencies"):
            assert usd_money >= thb_money

    def test_money_hash(self):
        """Test money hashing."""
        money1 = Money.from_float(10.50, Currency.USD)
        money2 = Money.from_float(10.50, Currency.USD)
        money3 = Money.from_float(15.00, Currency.USD)

        assert hash(money1) == hash(money2)
        assert hash(money1) != hash(money3)

        # Can be used in sets and dicts
        money_set = {money1, money2, money3}
        assert len(money_set) == 2  # money1 and money2 are the same

    def test_money_string_representation(self):
        """Test money string representation."""
        money = Money.from_float(10.50, Currency.USD)

        assert str(money) == "10.50 USD"
        assert repr(money) == "Money(amount=Decimal('10.50'), currency=Currency.USD)"

    def test_money_conversion_to_float(self):
        """Test money conversion to float."""
        money = Money.from_float(10.50, Currency.USD)

        assert money.to_float() == 10.50
        assert isinstance(money.to_float(), float)

    def test_money_conversion_to_dict(self):
        """Test money conversion to dictionary."""
        money = Money.from_float(10.50, Currency.USD)

        data = money.to_dict()

        assert data["amount"] == 10.50
        assert data["currency"] == "USD"

    def test_money_from_dict(self):
        """Test money creation from dictionary."""
        data = {"amount": 10.50, "currency": "USD"}
        money = Money.from_dict(data)

        assert money.amount == Decimal("10.50")
        assert money.currency == Currency.USD

    def test_money_from_dict_invalid(self):
        """Test money creation from invalid dictionary."""
        # Missing fields
        with pytest.raises(KeyError):
            Money.from_dict({"amount": 10.50})

        # Invalid currency
        with pytest.raises(ValueError, match="Invalid currency"):
            Money.from_dict({"amount": 10.50, "currency": "INVALID"})

        # Negative amount
        with pytest.raises(ValueError, match="negative"):
            Money.from_dict({"amount": -10.50, "currency": "USD"})

    def test_money_precision(self):
        """Test money precision handling."""
        # High precision
        money = Money.from_float(10.123456789, Currency.USD)
        assert money.amount == Decimal("10.123456789")

        # Rounding behavior
        money_rounded = Money(amount=Decimal("10.50"), currency=Currency.USD)
        assert money_rounded.amount == Decimal("10.50")

    def test_money_zero_amount(self):
        """Test money with zero amount."""
        money = Money.from_float(0.0, Currency.USD)

        assert money.amount == Decimal("0")
        assert money.currency == Currency.USD
        assert money.is_zero()

    def test_money_is_zero(self):
        """Test is_zero method."""
        zero_money = Money.from_float(0.0, Currency.USD)
        non_zero_money = Money.from_float(10.50, Currency.USD)

        assert zero_money.is_zero()
        assert not non_zero_money.is_zero()

    def test_money_is_positive(self):
        """Test is_positive method."""
        zero_money = Money.from_float(0.0, Currency.USD)
        positive_money = Money.from_float(10.50, Currency.USD)

        assert not zero_money.is_positive()
        assert positive_money.is_positive()

    def test_money_absolute_value(self):
        """Test absolute value (should always be positive due to validation)."""
        money = Money.from_float(10.50, Currency.USD)
        abs_money = money.abs()

        assert abs_money.amount == Decimal("10.50")
        assert abs_money.currency == Currency.USD

    def test_money_immutability(self):
        """Test that money objects are immutable."""
        money = Money.from_float(10.50, Currency.USD)
        original_amount = money.amount

        # Operations return new objects
        new_money = money.add(Money.from_float(5.0, Currency.USD))

        # Original unchanged
        assert money.amount == original_amount
        assert new_money.amount == Decimal("15.50")
        assert new_money is not money

    def test_money_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Very small amount
        tiny_money = Money.from_float(0.01, Currency.USD)
        assert tiny_money.amount == Decimal("0.01")

        # Large amount
        large_money = Money.from_float(999999999.99, Currency.USD)
        assert large_money.amount == Decimal("999999999.99")

        # Scientific notation
        sci_money = Money(amount=Decimal("1E+2"), currency=Currency.USD)
        assert sci_money.amount == Decimal("100")

    def test_money_arithmetic_edge_cases(self):
        """Test arithmetic edge cases."""
        money = Money.from_float(10.50, Currency.USD)

        # Multiply by zero
        zero_result = money.multiply(Decimal("0"))
        assert zero_result.is_zero()

        # Multiply by one
        same_result = money.multiply(Decimal("1"))
        assert same_result == money

        # Division by one
        same_div = money.divide(Decimal("1"))
        assert same_div == money

        # Division by zero should raise
        with pytest.raises(InvalidOperation):
            money.divide(Decimal("0"))

    def test_money_currency_consistency(self):
        """Test currency consistency across operations."""
        usd_money = Money.from_float(10.50, Currency.USD)

        # All operations preserve currency
        doubled = usd_money.multiply(2)
        assert doubled.currency == Currency.USD

        halved = usd_money.divide(2)
        assert halved.currency == Currency.USD

        added = usd_money.add(Money.from_float(5.0, Currency.USD))
        assert added.currency == Currency.USD

    def test_money_serialization_roundtrip(self):
        """Test serialization roundtrip."""
        original = Money.from_float(10.50, Currency.USD)

        # To dict and back
        data = original.to_dict()
        recreated = Money.from_dict(data)

        assert original == recreated
        assert original.amount == recreated.amount
        assert original.currency == recreated.currency

    def test_money_with_all_currencies(self):
        """Test money with all supported currencies."""
        amount = Decimal("100.50")

        for currency in Currency:
            money = Money(amount=amount, currency=currency)
            assert money.amount == amount
            assert money.currency == currency

            # Test string representation
            str_repr = str(money)
            assert currency.value in str_repr
            assert "100.50" in str_repr

    def test_money_decimal_precision_preservation(self):
        """Test that decimal precision is preserved."""
        # Create money with specific precision
        precise_amount = Decimal("10.123456789012345")
        money = Money(amount=precise_amount, currency=Currency.USD)

        assert money.amount == precise_amount

        # Arithmetic should preserve precision where possible
        doubled = money.multiply(Decimal("2"))
        expected = precise_amount * 2
        assert doubled.amount == expected
