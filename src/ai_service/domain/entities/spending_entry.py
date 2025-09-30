"""Spending entry domain entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ..value_objects.processing_method import ProcessingMethod

if TYPE_CHECKING:
    from ..value_objects.confidence import ConfidenceScore
    from ..value_objects.money import Money
    from ..value_objects.processing_method import ProcessingMetadata
    from ..value_objects.spending_category import PaymentMethod, SpendingCategory


@dataclass(frozen=True)
class SpendingEntryId:
    """Unique identifier for spending entries."""

    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        """Validate spending entry ID."""

        # Validate UUID format (this will catch empty strings too)
        try:
            uuid.UUID(self.value)
        except ValueError as e:
            msg = f"Invalid UUID format: {self.value}"
            raise ValueError(msg) from e

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Developer representation."""
        return f"SpendingEntryId({self.value})"

    @classmethod
    def generate(cls) -> SpendingEntryId:
        """Generate a new spending entry ID."""
        return cls()

    @classmethod
    def from_string(cls, value: str) -> SpendingEntryId:
        """Create spending entry ID from string."""
        return cls(value=value)


@dataclass
class SpendingEntry:
    """
    Spending entry aggregate root representing a financial transaction.

    This is the core domain entity that encapsulates all spending-related
    business logic and invariants.
    """

    # Core spending data (required fields first)
    amount: Money
    merchant: str
    description: str | None
    transaction_date: datetime
    category: SpendingCategory
    payment_method: PaymentMethod
    confidence: ConfidenceScore
    processing_method: ProcessingMethod

    # Identity (with default)
    id: SpendingEntryId = field(default_factory=SpendingEntryId)

    # Optional fields
    subcategory: str | None = field(default=None)
    location: str | None = field(default=None)
    processing_metadata: ProcessingMetadata | None = field(default=None)
    raw_text: str | None = field(default=None)

    # Lists with defaults
    tags: list[str] = field(default_factory=list)

    # Audit fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Domain events
    _events: list[Any] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        """Validate spending entry invariants."""
        self._validate_business_rules()

        # Domain events are temporarily disabled for migration

    def validate(self) -> None:
        """Public validation method."""
        self._validate_business_rules()

    def update_amount(self, new_amount: Money) -> SpendingEntry:
        """Update the amount and return a new instance."""
        from copy import deepcopy

        try:
            new_entry = deepcopy(self)
            new_entry.amount = new_amount
            new_entry.updated_at = datetime.utcnow()
            return new_entry
        except Exception as e:
            # This should not happen in production, but helps debug
            raise RuntimeError(f"Failed to update amount: {e}") from e

    def update_description(self, new_description: str | None) -> SpendingEntry:
        """Update the description and return a new instance."""
        from copy import deepcopy

        new_entry = deepcopy(self)
        new_entry.description = new_description
        new_entry.updated_at = datetime.utcnow()
        return new_entry

    def update_category(self, new_category: SpendingCategory) -> SpendingEntry:
        """Update the category and return a new instance."""
        from copy import deepcopy

        new_entry = deepcopy(self)
        new_entry.category = new_category
        new_entry.updated_at = datetime.utcnow()
        return new_entry

    def update_processing_method(self, new_method: ProcessingMethod) -> SpendingEntry:
        """Update the processing method and return a new instance."""
        from copy import deepcopy

        new_entry = deepcopy(self)
        new_entry.processing_method = new_method
        new_entry.updated_at = datetime.utcnow()
        return new_entry

    def _validate_business_rules(self) -> None:
        """Validate core business rules."""
        # Merchant validation
        if not self.merchant.strip():
            msg = "Merchant cannot be empty"
            raise ValueError(msg)

        if len(self.merchant) > 200:
            msg = f"Merchant name too long: {len(self.merchant)} characters (max 200)"
            raise ValueError(msg)

        # Description validation (optional field)
        if self.description is not None:
            if not self.description.strip():
                msg = "Description cannot be empty"
                raise ValueError(msg)

            if len(self.description) > 1000:
                msg = f"Description too long: {len(self.description)} characters (max 1000)"
                raise ValueError(msg)

        # Date validation
        if self.transaction_date > datetime.utcnow():
            msg = "Transaction date cannot be in the future"
            raise ValueError(msg)

        # Tags validation
        if len(self.tags) > 10:
            msg = f"Too many tags: {len(self.tags)} (max 10)"
            raise ValueError(msg)

        for tag in self.tags:
            if len(tag) > 50:
                msg = f"Tag too long: '{tag}' ({len(tag)} characters, max 50)"
                raise ValueError(msg)

        # Location validation
        if self.location and len(self.location) > 200:
            msg = f"Location too long: {len(self.location)} characters (max 200)"
            raise ValueError(msg)

        # Raw text validation
        if self.raw_text and len(self.raw_text) > 2000:
            msg = f"Raw text too long: {len(self.raw_text)} characters (max 2000)"
            raise ValueError(msg)

    def update_merchant(self, new_merchant: str) -> SpendingEntry:
        """Update the merchant name and return a new instance."""
        if not new_merchant.strip():
            msg = "Merchant cannot be empty"
            raise ValueError(msg)

        if len(new_merchant) > 200:
            msg = f"Merchant name too long: {len(new_merchant)} characters (max 200)"
            raise ValueError(msg)

        from copy import deepcopy

        try:
            new_entry = deepcopy(self)
            new_entry.merchant = new_merchant.strip()
            new_entry.updated_at = datetime.utcnow()
            return new_entry
        except Exception as e:
            # This should not happen in production, but helps debug
            msg = f"Failed to update merchant: {e}"
            raise RuntimeError(msg) from e

    def add_tag(self, tag: str) -> None:
        """Add a tag to the spending entry."""
        if not tag.strip():
            msg = "Tag cannot be empty"
            raise ValueError(msg)

        if len(tag) > 50:
            msg = f"Tag too long: '{tag}' ({len(tag)} characters, max 50)"
            raise ValueError(msg)

        tag_cleaned = tag.strip().lower()

        if tag_cleaned in [t.lower() for t in self.tags]:
            return  # Tag already exists

        if len(self.tags) >= 10:
            msg = "Cannot add more than 10 tags"
            raise ValueError(msg)

        new_tags = [*self.tags, tag_cleaned]
        object.__setattr__(self, "tags", new_tags)
        object.__setattr__(self, "updated_at", datetime.utcnow())

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the spending entry."""
        tag_cleaned = tag.strip().lower()
        new_tags = [t for t in self.tags if t.lower() != tag_cleaned]

        if len(new_tags) == len(self.tags):
            return  # Tag not found

        object.__setattr__(self, "tags", new_tags)
        object.__setattr__(self, "updated_at", datetime.utcnow())

    def enhance_with_ai(
        self, confidence: ConfidenceScore, processing_metadata: ProcessingMetadata
    ) -> None:
        """Enhance the entry with AI processing results."""
        # Only allow enhancement if current confidence is lower
        if self.confidence.value >= confidence.value:
            return

        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "processing_metadata", processing_metadata)
        object.__setattr__(self, "updated_at", datetime.utcnow())

    def is_high_confidence(self) -> bool:
        """Check if the entry has high confidence."""
        return self.confidence.is_high()

    def is_ai_processed(self) -> bool:
        """Check if the entry was processed with AI."""
        return self.processing_method.is_ai_enhanced()

    def is_manual_entry(self) -> bool:
        """Check if the entry was manually entered."""
        return self.processing_method == ProcessingMethod.MANUAL_ENTRY

    def is_cultural_spending(self) -> bool:
        """Check if this is Thai cultural spending."""
        return self.category.is_cultural()

    def is_essential_spending(self) -> bool:
        """Check if this is essential spending."""
        return self.category.is_essential()

    def get_display_amount(self) -> str:
        """Get formatted display amount."""
        return str(self.amount)

    def get_age_days(self) -> int:
        """Get age of the entry in days."""
        return (datetime.utcnow() - self.created_at).days

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id.value,
            "amount": self.amount.to_float(),
            "currency": self.amount.currency.value,
            "merchant": self.merchant,
            "description": self.description,
            "transaction_date": self.transaction_date.isoformat(),
            "category": self.category.value,
            "subcategory": self.subcategory,
            "payment_method": self.payment_method.value,
            "location": self.location,
            "tags": self.tags,
            "confidence": self.confidence.value,
            "processing_method": self.processing_method.value,
            "raw_text": self.raw_text,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def _add_event(self, event: Any) -> None:
        """Add domain event."""
        self._events.append(event)

    def get_events(self) -> list[Any]:
        """Get all domain events."""
        return self._events.copy()

    def clear_events(self) -> None:
        """Clear domain events."""
        self._events.clear()

    @classmethod
    def create(
        cls,
        merchant: str,
        amount: Money,
        category: SpendingCategory,
        description: str | None = None,
        payment_method: PaymentMethod | None = None,
        confidence: ConfidenceScore | None = None,
        processing_method: ProcessingMethod | None = None,
        transaction_date: datetime | None = None,
        **kwargs: Any,
    ) -> SpendingEntry:
        """Create a new spending entry with defaults."""
        from ..value_objects.confidence import ConfidenceScore
        from ..value_objects.spending_category import PaymentMethod

        return cls(
            merchant=merchant,
            amount=amount,
            category=category,
            description=description,
            payment_method=payment_method or PaymentMethod.OTHER,
            confidence=confidence or ConfidenceScore.medium(),
            processing_method=processing_method or ProcessingMethod.MANUAL_ENTRY,
            transaction_date=transaction_date or datetime.utcnow(),
            **kwargs,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpendingEntry:
        """Create spending entry from dictionary."""
        from ..value_objects.confidence import ConfidenceScore
        from ..value_objects.money import Currency, Money
        from ..value_objects.spending_category import PaymentMethod, SpendingCategory

        return cls(
            id=SpendingEntryId.from_string(data["id"])
            if "id" in data
            else SpendingEntryId.generate(),
            merchant=data["merchant"],
            amount=Money.from_float(data["amount"], Currency(data["currency"])),
            category=SpendingCategory(data["category"]),
            description=data["description"],
            payment_method=PaymentMethod(data["payment_method"]),
            confidence=ConfidenceScore(data["confidence"]),
            processing_method=ProcessingMethod(data["processing_method"]),
            transaction_date=datetime.fromisoformat(data["transaction_date"]),
            subcategory=data.get("subcategory"),
            location=data.get("location"),
            tags=data.get("tags", []),
            raw_text=data.get("raw_text"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.utcnow(),
        )

    def __str__(self) -> str:
        """String representation."""
        return f"SpendingEntry({self.merchant}, {self.amount}, {self.category.value})"
