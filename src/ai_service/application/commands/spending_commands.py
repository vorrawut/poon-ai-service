"""Spending-related commands and handlers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ...domain.entities.spending_entry import SpendingEntry, SpendingEntryId
from ...domain.value_objects.confidence import ConfidenceScore
from ...domain.value_objects.money import Currency, Money
from ...domain.value_objects.processing_method import (
    ProcessingMethod,
)
from ...domain.value_objects.spending_category import PaymentMethod, SpendingCategory
from ...domain.value_objects.text_content import TextContent
from .base import Command, CommandHandler, CommandResult

if TYPE_CHECKING:
    from ...domain.repositories.spending_repository import SpendingRepository


@dataclass(frozen=True)
class CreateSpendingEntryCommand(Command):
    """Command to create a new spending entry."""

    amount: float
    currency: str
    merchant: str
    description: str
    transaction_date: datetime
    category: str
    subcategory: str | None = None
    payment_method: str = PaymentMethod.CASH.value
    location: str | None = None
    tags: list[str] | None = None
    confidence: float = 0.8
    processing_method: str = ProcessingMethod.MANUAL_ENTRY.value
    raw_text: str | None = None

    def validate(self) -> None:
        """Validate command data."""
        if self.amount <= 0:
            msg = "Amount must be positive"
            raise ValueError(msg)

        if not self.merchant.strip():
            msg = "Merchant cannot be empty"
            raise ValueError(msg)

        if not self.description.strip():
            msg = "Description cannot be empty"
            raise ValueError(msg)

        if self.transaction_date > datetime.utcnow():
            msg = "Transaction date cannot be in the future"
            raise ValueError(msg)


class CreateSpendingEntryCommandHandler(
    CommandHandler[CreateSpendingEntryCommand, CommandResult]
):
    """Handler for creating spending entries."""

    def __init__(self, repository: SpendingRepository) -> None:
        """Initialize handler with repository."""
        self._repository = repository

    async def handle(self, command: CreateSpendingEntryCommand) -> CommandResult:
        """Handle the create spending entry command."""
        try:
            command.validate()

            # Create value objects
            money = Money.from_float(command.amount, Currency(command.currency))
            category = SpendingCategory(command.category)
            payment_method = PaymentMethod(command.payment_method)
            confidence = ConfidenceScore(command.confidence)
            processing_method = ProcessingMethod(command.processing_method)

            # Create spending entry entity
            entry = SpendingEntry(
                amount=money,
                merchant=command.merchant.strip(),
                description=command.description.strip(),
                transaction_date=command.transaction_date,
                category=category,
                subcategory=command.subcategory,
                payment_method=payment_method,
                location=command.location,
                tags=command.tags or [],
                confidence=confidence,
                processing_method=processing_method,
                raw_text=command.raw_text,
            )

            # Save to repository
            await self._repository.save(entry)

            return CommandResult.success_result(
                message="Spending entry created successfully",
                data={"entry_id": entry.id.value},
            )

        except Exception as e:
            return CommandResult.failure_result(
                message="Failed to create spending entry", errors=[str(e)]
            )


@dataclass(frozen=True)
class UpdateSpendingEntryCommand(Command):
    """Command to update an existing spending entry."""

    entry_id: str
    amount: float | None = None
    merchant: str | None = None
    category: str | None = None
    subcategory: str | None = None
    payment_method: str | None = None
    location: str | None = None
    tags: list[str] | None = None

    def validate(self) -> None:
        """Validate command data."""
        if not self.entry_id.strip():
            msg = "Entry ID cannot be empty"
            raise ValueError(msg)

        # Validate UUID format
        try:
            import uuid

            uuid.UUID(self.entry_id)
        except ValueError as e:
            msg = "Invalid entry ID format"
            raise ValueError(msg) from e

        if self.amount is not None and self.amount <= 0:
            msg = "Amount must be positive"
            raise ValueError(msg)

        if self.merchant is not None and not self.merchant.strip():
            msg = "Merchant cannot be empty"
            raise ValueError(msg)


class UpdateSpendingEntryCommandHandler(
    CommandHandler[UpdateSpendingEntryCommand, CommandResult]
):
    """Handler for updating spending entries."""

    def __init__(self, repository: SpendingRepository) -> None:
        """Initialize handler with repository."""
        self._repository = repository

    async def handle(self, command: UpdateSpendingEntryCommand) -> CommandResult:
        """Handle the update spending entry command."""
        try:
            command.validate()

            # Find existing entry
            entry_id = SpendingEntryId(command.entry_id)
            entry = await self._repository.find_by_id(entry_id)

            if entry is None:
                return CommandResult.failure_result(
                    message="Spending entry not found",
                    errors=[f"No entry found with ID: {command.entry_id}"],
                )

            # Update fields
            if command.amount is not None:
                new_amount = Money.from_float(command.amount, entry.amount.currency)
                entry.update_amount(new_amount)

            if command.merchant is not None:
                entry.update_merchant(command.merchant)

            if command.category is not None:
                new_category = SpendingCategory(command.category)
                entry = entry.update_category(new_category)

            # Save updated entry
            await self._repository.save(entry)

            return CommandResult.success_result(
                message="Spending entry updated successfully",
                data={"entry_id": entry.id.value},
            )

        except Exception as e:
            return CommandResult.failure_result(
                message="Failed to update spending entry", errors=[str(e)]
            )


@dataclass(frozen=True)
class DeleteSpendingEntryCommand(Command):
    """Command to delete a spending entry."""

    entry_id: str
    reason: str | None = None

    def validate(self) -> None:
        """Validate command data."""
        if not self.entry_id.strip():
            msg = "Entry ID cannot be empty"
            raise ValueError(msg)


class DeleteSpendingEntryCommandHandler(
    CommandHandler[DeleteSpendingEntryCommand, CommandResult]
):
    """Handler for deleting spending entries."""

    def __init__(self, repository: SpendingRepository) -> None:
        """Initialize handler with repository."""
        self._repository = repository

    async def handle(self, command: DeleteSpendingEntryCommand) -> CommandResult:
        """Handle the delete spending entry command."""
        try:
            command.validate()

            entry_id = SpendingEntryId(command.entry_id)
            deleted = await self._repository.delete(entry_id)

            if not deleted:
                return CommandResult.failure_result(
                    message="Spending entry not found",
                    errors=[f"No entry found with ID: {command.entry_id}"],
                )

            return CommandResult.success_result(
                message="Spending entry deleted successfully",
                data={"entry_id": command.entry_id},
            )

        except Exception as e:
            return CommandResult.failure_result(
                message="Failed to delete spending entry", errors=[str(e)]
            )


@dataclass(frozen=True)
class ProcessTextCommand(Command):
    """Command to process text input into a spending entry."""

    text: str
    language: str | None = None
    user_context: dict[str, Any] | None = None

    def validate(self) -> None:
        """Validate command data."""
        if not self.text.strip():
            msg = "Text cannot be empty"
            raise ValueError(msg)

        if len(self.text) > 2000:
            msg = f"Text too long: {len(self.text)} characters (max 2000)"
            raise ValueError(msg)


class ProcessTextCommandHandler(CommandHandler[ProcessTextCommand, CommandResult]):
    """Handler for processing text into spending entries."""

    def __init__(
        self,
        repository: SpendingRepository,
        text_processing_service: Any,  # Will be defined in domain services
    ) -> None:
        """Initialize handler with dependencies."""
        self._repository = repository
        self._text_processing_service = text_processing_service

    async def handle(self, command: ProcessTextCommand) -> CommandResult:
        """Handle the process text command."""
        try:
            command.validate()

            # Create text content value object
            text_content = TextContent.from_raw_input(command.text)

            # Process text to extract spending data
            processing_result = await self._text_processing_service.process_text(
                text_content, context=command.user_context
            )

            if not processing_result.success:
                return CommandResult.failure_result(
                    message="Failed to process text", errors=processing_result.errors
                )

            # Create spending entry from processing result
            entry = processing_result.spending_entry

            # Save to repository
            await self._repository.save(entry)

            return CommandResult.success_result(
                message="Text processed and spending entry created",
                data={
                    "entry_id": entry.id.value,
                    "confidence": entry.confidence.value,
                    "processing_method": entry.processing_method.value,
                },
            )

        except Exception as e:
            return CommandResult.failure_result(
                message="Failed to process text", errors=[str(e)]
            )


@dataclass(frozen=True)
class ProcessImageCommand(Command):
    """Command to process image (receipt) into a spending entry."""

    image_data: bytes
    image_format: str
    filename: str | None = None
    language: str = "eng+tha"  # OCR language

    def validate(self) -> None:
        """Validate command data."""
        if not self.image_data:
            msg = "Image data cannot be empty"
            raise ValueError(msg)

        if len(self.image_data) > 10 * 1024 * 1024:  # 10MB limit
            msg = f"Image too large: {len(self.image_data)} bytes (max 10MB)"
            raise ValueError(msg)


class ProcessImageCommandHandler(CommandHandler[ProcessImageCommand, CommandResult]):
    """Handler for processing images into spending entries."""

    def __init__(
        self,
        repository: SpendingRepository,
        image_processing_service: Any,  # Will be defined in domain services
    ) -> None:
        """Initialize handler with dependencies."""
        self._repository = repository
        self._image_processing_service = image_processing_service

    async def handle(self, command: ProcessImageCommand) -> CommandResult:
        """Handle the process image command."""
        try:
            command.validate()

            # Create image data value object
            from ...domain.value_objects.image_data import ImageData, ImageFormat

            image_format = ImageFormat(command.image_format)
            image_data = ImageData(
                data=command.image_data, format=image_format, filename=command.filename
            )

            # Process image to extract spending data
            processing_result = await self._image_processing_service.process_image(
                image_data, ocr_language=command.language
            )

            if not processing_result.success:
                return CommandResult.failure_result(
                    message="Failed to process image", errors=processing_result.errors
                )

            # Create spending entry from processing result
            entry = processing_result.spending_entry

            # Save to repository
            await self._repository.save(entry)

            return CommandResult.success_result(
                message="Image processed and spending entry created",
                data={
                    "entry_id": entry.id.value,
                    "confidence": entry.confidence.value,
                    "processing_method": entry.processing_method.value,
                    "ocr_text": processing_result.extracted_text,
                },
            )

        except Exception as e:
            return CommandResult.failure_result(
                message="Failed to process image", errors=[str(e)]
            )


@dataclass(frozen=True)
class EnhanceWithAICommand(Command):
    """Command to enhance an existing spending entry with AI."""

    entry_id: str
    ai_model: str | None = None
    force_enhancement: bool = False

    def validate(self) -> None:
        """Validate command data."""
        if not self.entry_id.strip():
            msg = "Entry ID cannot be empty"
            raise ValueError(msg)


class EnhanceWithAICommandHandler(CommandHandler[EnhanceWithAICommand, CommandResult]):
    """Handler for AI enhancement of spending entries."""

    def __init__(
        self,
        repository: SpendingRepository,
        ai_enhancement_service: Any,  # Will be defined in domain services
    ) -> None:
        """Initialize handler with dependencies."""
        self._repository = repository
        self._ai_enhancement_service = ai_enhancement_service

    async def handle(self, command: EnhanceWithAICommand) -> CommandResult:
        """Handle the AI enhancement command."""
        try:
            command.validate()

            # Find existing entry
            entry_id = SpendingEntryId(command.entry_id)
            entry = await self._repository.find_by_id(entry_id)

            if entry is None:
                return CommandResult.failure_result(
                    message="Spending entry not found",
                    errors=[f"No entry found with ID: {command.entry_id}"],
                )

            # Check if enhancement is needed
            if entry.is_high_confidence() and not command.force_enhancement:
                return CommandResult.success_result(
                    message="Entry already has high confidence, skipping enhancement",
                    data={
                        "entry_id": entry.id.value,
                        "confidence": entry.confidence.value,
                    },
                )

            # Enhance with AI
            enhancement_result = await self._ai_enhancement_service.enhance_entry(
                entry, model_preference=command.ai_model
            )

            if not enhancement_result.success:
                return CommandResult.failure_result(
                    message="Failed to enhance with AI",
                    errors=enhancement_result.errors,
                )

            # Update entry with AI enhancements
            enhanced_entry = enhancement_result.enhanced_entry

            # Save enhanced entry
            await self._repository.save(enhanced_entry)

            return CommandResult.success_result(
                message="Spending entry enhanced with AI",
                data={
                    "entry_id": enhanced_entry.id.value,
                    "confidence_before": entry.confidence.value,
                    "confidence_after": enhanced_entry.confidence.value,
                    "ai_model": enhancement_result.model_used,
                },
            )

        except Exception as e:
            return CommandResult.failure_result(
                message="Failed to enhance with AI", errors=[str(e)]
            )
