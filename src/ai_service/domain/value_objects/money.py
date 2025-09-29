"""Money value object for financial amounts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any


class Currency(str, Enum):
    """Supported currencies."""

    THB = "THB"  # Thai Baht
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    SGD = "SGD"  # Singapore Dollar
    MYR = "MYR"  # Malaysian Ringgit
    PHP = "PHP"  # Philippine Peso


@dataclass(frozen=True)
class Money:
    """Immutable money value object representing an amount with currency."""

    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        """Validate money constraints."""
        if self.amount < 0:
            msg = "Money amount cannot be negative"
            raise ValueError(msg)

        if not isinstance(self.currency, Currency):
            msg = f"Invalid currency: {self.currency}"
            raise ValueError(msg)

    @classmethod
    def from_float(cls, amount: float, currency: Currency) -> Money:
        """Create money from float amount."""
        return cls(amount=Decimal(str(amount)), currency=currency)

    @classmethod
    def zero(cls, currency: Currency) -> Money:
        """Create zero money amount."""
        return cls(amount=Decimal("0"), currency=currency)

    def to_float(self) -> float:
        """Convert to float for external APIs."""
        return float(self.amount)

    def add(self, other: Money) -> Money:
        """Add two money amounts (must be same currency)."""
        if self.currency != other.currency:
            msg = f"Cannot add different currencies: {self.currency} and {other.currency}"
            raise ValueError(msg)

        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: Money) -> Money:
        """Subtract two money amounts (must be same currency)."""
        if self.currency != other.currency:
            msg = f"Cannot subtract different currencies: {self.currency} and {other.currency}"
            raise ValueError(msg)

        result_amount = self.amount - other.amount
        if result_amount < 0:
            msg = "Subtraction would result in negative amount"
            raise ValueError(msg)

        return Money(amount=result_amount, currency=self.currency)

    def multiply(self, factor: Decimal | float) -> Money:
        """Multiply money by a factor."""
        if isinstance(factor, float):
            factor = Decimal(str(factor))

        if factor < 0:
            msg = "Cannot multiply money by negative factor"
            raise ValueError(msg)

        return Money(amount=self.amount * factor, currency=self.currency)

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0

    def __str__(self) -> str:
        """String representation of money."""
        if self.currency == Currency.THB:
            return f"฿{self.amount:,.2f}"
        elif self.currency == Currency.USD:
            return f"${self.amount:,.2f}"
        else:
            return f"{self.amount:,.2f} {self.currency.value}"

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: Money) -> bool:
        """Less than comparison (same currency only)."""
        if self.currency != other.currency:
            msg = f"Cannot compare different currencies: {self.currency} and {other.currency}"
            raise ValueError(msg)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        """Less than or equal comparison (same currency only)."""
        if self.currency != other.currency:
            msg = f"Cannot compare different currencies: {self.currency} and {other.currency}"
            raise ValueError(msg)
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        """Greater than comparison (same currency only)."""
        if self.currency != other.currency:
            msg = f"Cannot compare different currencies: {self.currency} and {other.currency}"
            raise ValueError(msg)
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        """Greater than or equal comparison (same currency only)."""
        if self.currency != other.currency:
            msg = f"Cannot compare different currencies: {self.currency} and {other.currency}"
            raise ValueError(msg)
        return self.amount >= other.amount
