"""Comprehensive tests for Money value object."""

from decimal import Decimal

import pytest

from src.ai_service.domain.value_objects.money import Currency, Money


class TestMoney:
    """Test Money value object."""

    def test_money_creation_success(self):
        """Test successful money creation."""
        money = Money(amount=Decimal("100.50"), currency=Currency.USD)
        assert money.amount == Decimal("100.50")
        assert money.currency == Currency.USD

    def test_money_from_float(self):
        """Test creating money from float."""
        money = Money.from_float(150.75, Currency.THB)
        assert money.amount == Decimal("150.75")
        assert money.currency == Currency.THB

    def test_money_zero_class_method(self):
        """Test creating zero money."""
        money = Money.zero(Currency.EUR)
        assert money.amount == Decimal("0")
        assert money.currency == Currency.EUR

    def test_negative_amount_validation(self):
        """Test negative amount validation."""
        with pytest.raises(ValueError, match="Money amount cannot be negative"):
            Money(amount=Decimal("-10"), currency=Currency.USD)

    def test_money_addition_same_currency(self):
        """Test adding money with same currency."""
        money1 = Money.from_float(100.0, Currency.USD)
        money2 = Money.from_float(50.0, Currency.USD)

        result = money1.add(money2)
        assert result.amount == Decimal("150.0")
        assert result.currency == Currency.USD

    def test_money_addition_different_currency_raises_error(self):
        """Test adding money with different currencies raises error."""
        usd_money = Money.from_float(100, Currency.USD)
        thb_money = Money.from_float(100, Currency.THB)

        with pytest.raises(ValueError, match="Cannot add different currencies"):
            usd_money.add(thb_money)

    def test_money_subtraction_same_currency(self):
        """Test subtracting money with same currency."""
        money1 = Money.from_float(100.0, Currency.USD)
        money2 = Money.from_float(30.0, Currency.USD)

        result = money1.subtract(money2)
        assert result.amount == Decimal("70.0")
        assert result.currency == Currency.USD

    def test_money_subtraction_different_currency_raises_error(self):
        """Test subtracting money with different currencies raises error."""
        usd_money = Money.from_float(100, Currency.USD)
        thb_money = Money.from_float(50, Currency.THB)

        with pytest.raises(ValueError, match="Cannot subtract different currencies"):
            usd_money.subtract(thb_money)

    def test_money_subtraction_negative_result_raises_error(self):
        """Test subtraction resulting in negative amount raises error."""
        money1 = Money.from_float(30.0, Currency.USD)
        money2 = Money.from_float(50.0, Currency.USD)

        with pytest.raises(
            ValueError, match="Subtraction would result in negative amount"
        ):
            money1.subtract(money2)

    def test_money_multiplication(self):
        """Test money multiplication by scalar."""
        money = Money.from_float(25.0, Currency.USD)
        result = money.multiply(Decimal("3"))

        assert result.amount == Decimal("75.0")
        assert result.currency == Currency.USD

    def test_money_to_float(self):
        """Test converting money to float."""
        money = Money.from_float(123.45, Currency.USD)
        assert money.to_float() == 123.45

    def test_money_is_positive(self):
        """Test checking if money is positive."""
        positive_money = Money.from_float(10.0, Currency.USD)
        zero_money = Money.zero(Currency.USD)

        assert positive_money.is_positive()
        assert not zero_money.is_positive()

    def test_money_comparison(self):
        """Test money comparison operations."""
        money1 = Money.from_float(100.0, Currency.USD)
        money2 = Money.from_float(150.0, Currency.USD)
        money3 = Money.from_float(100.0, Currency.USD)

        assert money1 < money2
        assert money2 > money1
        assert money1 == money3
        assert money1 <= money3
        assert money1 >= money3

    def test_money_comparison_different_currency_raises_error(self):
        """Test comparing money with different currencies raises error."""
        usd_money = Money.from_float(100, Currency.USD)
        thb_money = Money.from_float(100, Currency.THB)

        with pytest.raises(ValueError, match="Cannot compare different currencies"):
            _ = usd_money < thb_money

    def test_money_string_representation(self):
        """Test money string representation."""
        money = Money.from_float(123.45, Currency.USD)
        assert str(money) == "123.45 USD"

    def test_money_repr(self):
        """Test money repr."""
        money = Money.from_float(123.45, Currency.USD)
        assert repr(money) == "Money(amount=Decimal('123.45'), currency=Currency.USD)"

    def test_money_hash(self):
        """Test money hashing."""
        money1 = Money.from_float(100.0, Currency.USD)
        money2 = Money.from_float(100.0, Currency.USD)
        money3 = Money.from_float(150.0, Currency.USD)

        assert hash(money1) == hash(money2)
        assert hash(money1) != hash(money3)

    def test_money_to_dict(self):
        """Test money serialization to dict."""
        money = Money.from_float(123.45, Currency.USD)
        data = money.to_dict()

        expected = {"amount": 123.45, "currency": "USD"}
        assert data == expected

    def test_money_from_dict(self):
        """Test money deserialization from dict."""
        data = {"amount": "123.45", "currency": "USD"}
        money = Money.from_dict(data)

        assert money.amount == Decimal("123.45")
        assert money.currency == Currency.USD

    def test_money_roundtrip_serialization(self):
        """Test money roundtrip serialization."""
        original = Money.from_float(123.45, Currency.EUR)
        data = original.to_dict()
        restored = Money.from_dict(data)

        assert original == restored

    def test_money_precision(self):
        """Test money precision handling."""
        # Test with high precision decimal
        precise_amount = Decimal("123.456789")
        money = Money(amount=precise_amount, currency=Currency.USD)

        assert money.amount == precise_amount

    def test_money_zero_amount(self):
        """Test money with zero amount."""
        zero_money = Money.from_float(0.0, Currency.USD)
        assert zero_money.amount == Decimal("0.0")
        assert zero_money.currency == Currency.USD

    def test_money_is_zero(self):
        """Test checking if money is zero."""
        zero_money = Money.from_float(0.0, Currency.USD)
        non_zero_money = Money.from_float(10.0, Currency.USD)

        assert zero_money.is_zero()
        assert not non_zero_money.is_zero()

    def test_money_absolute_value(self):
        """Test money absolute value (should always be positive)."""
        money = Money.from_float(123.45, Currency.USD)
        abs_money = money.abs()

        assert abs_money.amount == Decimal("123.45")
        assert abs_money.currency == Currency.USD


class TestCurrency:
    """Test Currency enum."""

    def test_currency_values(self):
        """Test currency enum values."""
        assert Currency.USD.value == "USD"
        assert Currency.EUR.value == "EUR"
        assert Currency.THB.value == "THB"
        assert Currency.GBP.value == "GBP"
        assert Currency.JPY.value == "JPY"

    def test_currency_from_string(self):
        """Test creating currency from string."""
        assert Currency.from_string("USD") == Currency.USD
        assert Currency.from_string("EUR") == Currency.EUR
        assert Currency.from_string("THB") == Currency.THB

    def test_currency_from_string_case_insensitive(self):
        """Test creating currency from string (case insensitive)."""
        assert Currency.from_string("usd") == Currency.USD
        assert Currency.from_string("Eur") == Currency.EUR
        assert Currency.from_string("thb") == Currency.THB

    def test_currency_from_string_invalid(self):
        """Test creating currency from invalid string."""
        with pytest.raises(ValueError, match="Invalid currency: XYZ"):
            Currency.from_string("XYZ")

    def test_currency_string_representation(self):
        """Test currency string representation."""
        assert str(Currency.USD) == "USD"
        assert str(Currency.EUR) == "EUR"
        assert str(Currency.THB) == "THB"
