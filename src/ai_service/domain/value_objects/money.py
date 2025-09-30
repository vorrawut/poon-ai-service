"""Money value object for financial amounts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
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
    JPY = "JPY"  # Japanese Yen

    @classmethod
    def _missing_(cls, value: object) -> None:
        """Handle missing currency values with custom error message."""
        raise ValueError(f"Invalid currency: {value}")

    @classmethod
    def from_string(cls, value: str) -> Currency:
        """Create currency from string."""
        try:
            return cls(value.upper())
        except ValueError as e:
            msg = f"Invalid currency: {value}"
            raise ValueError(msg) from e

    def __str__(self) -> str:
        """String representation."""
        return self.value


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
            msg = (
                f"Cannot add different currencies: {self.currency} and {other.currency}"
            )
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

    def divide(self, divisor: Decimal | float) -> Money:
        """Divide money by a divisor."""
        if isinstance(divisor, float):
            divisor = Decimal(str(divisor))

        if divisor == 0:
            raise InvalidOperation("Cannot divide money by zero")

        if divisor < 0:
            msg = "Cannot divide money by negative divisor"
            raise ValueError(msg)

        return Money(amount=self.amount / divisor, currency=self.currency)

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0

    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > 0

    def abs(self) -> Money:
        """Get absolute value (always positive due to validation)."""
        return Money(amount=abs(self.amount), currency=self.currency)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "amount": float(self.amount),
            "currency": self.currency.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Money:
        """Create money from dictionary."""
        return cls.from_float(data["amount"], Currency(data["currency"]))

    def __str__(self) -> str:
        """String representation of money."""
        # Use standard format: amount + currency code for consistency
        # For JPY, show decimals if they exist, otherwise show as integer
        if self.currency == Currency.JPY and self.amount % 1 == 0:
            return f"{self.amount:,.0f} {self.currency.value}"  # JPY with no decimals
        else:
            return f"{self.amount:,.2f} {self.currency.value}"

    def __repr__(self) -> str:
        """Developer representation of money."""
        return f"Money(amount=Decimal('{self.amount:.2f}'), currency=Currency.{self.currency.name})"

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
