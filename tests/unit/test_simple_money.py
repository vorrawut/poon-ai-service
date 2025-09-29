"""Simple unit tests for Money value object."""

from decimal import Decimal

import pytest

from ai_service.domain.value_objects.money import Currency, Money


@pytest.mark.unit
class TestMoney:
    """Test Money value object."""

    def test_money_creation_from_float(self):
        """Test creating Money from float."""
        money = Money.from_float(120.50, Currency.THB)
        assert money.amount == Decimal("120.50")
        assert money.currency == Currency.THB
        assert str(money) == "฿120.50"

    def test_money_creation_from_decimal(self):
        """Test creating Money from Decimal."""
        money = Money(Decimal("99.99"), Currency.USD)
        assert money.amount == Decimal("99.99")
        assert money.currency == Currency.USD
        assert str(money) == "$99.99"

    def test_money_validation(self):
        """Test Money validation."""
        # Negative amounts should raise ValueError
        with pytest.raises(ValueError, match="Money amount cannot be negative"):
            Money(Decimal("-10.00"), Currency.THB)

        # Zero should be allowed
        money = Money(Decimal("0.00"), Currency.THB)
        assert money.amount == Decimal("0.00")

    def test_money_arithmetic(self):
        """Test Money arithmetic operations."""
        money1 = Money.from_float(100.00, Currency.THB)
        money2 = Money.from_float(50.00, Currency.THB)

        # Addition
        result = money1.add(money2)
        assert result.amount == Decimal("150.00")
        assert result.currency == Currency.THB

        # Subtraction
        result = money1.subtract(money2)
        assert result.amount == Decimal("50.00")

        # Cannot add different currencies
        usd_money = Money.from_float(50.00, Currency.USD)
        with pytest.raises(ValueError, match="Cannot add different currencies"):
            money1.add(usd_money)

    def test_money_comparison(self):
        """Test Money comparison operations."""
        money1 = Money.from_float(100.00, Currency.THB)
        money2 = Money.from_float(50.00, Currency.THB)
        money3 = Money.from_float(100.00, Currency.THB)

        assert money1 > money2
        assert money2 < money1
        assert money1 == money3
        assert money1 != money2

    def test_money_conversion(self):
        """Test Money conversion methods."""
        money = Money.from_float(120.50, Currency.THB)

        assert money.to_float() == 120.50
