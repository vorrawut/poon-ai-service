"""Unit tests for UpdateSpendingEntryCommandHandler."""

from unittest.mock import AsyncMock

import pytest

from ai_service.application.commands.spending_commands import (
    UpdateSpendingEntryCommand,
    UpdateSpendingEntryCommandHandler,
)
from ai_service.domain.entities.spending_entry import SpendingEntry
from ai_service.domain.value_objects.money import Currency, Money
from ai_service.domain.value_objects.spending_category import SpendingCategory


class TestUpdateSpendingEntryCommandHandler:
    """Test UpdateSpendingEntryCommandHandler."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_repository):
        """Create command handler."""
        return UpdateSpendingEntryCommandHandler(mock_repository)

    @pytest.fixture
    def sample_entry(self):
        """Create sample spending entry."""
        return SpendingEntry.create(
            merchant="Original Merchant",
            amount=Money.from_float(100.0, Currency.USD),
            category=SpendingCategory.FOOD_DINING,
            description="Original description",
        )

    @pytest.mark.asyncio
    async def test_handle_success_amount_update(
        self, handler, mock_repository, sample_entry
    ):
        """Test successful amount update."""
        entry_id = sample_entry.id.value
        command = UpdateSpendingEntryCommand(
            entry_id=entry_id,
            amount=150.0,
        )

        mock_repository.find_by_id.return_value = sample_entry
        mock_repository.save.return_value = None

        result = await handler.handle(command)

        assert result.success is True
        assert "updated successfully" in result.message
        mock_repository.find_by_id.assert_called_once()
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_success_merchant_update(
        self, handler, mock_repository, sample_entry
    ):
        """Test successful merchant update."""
        entry_id = sample_entry.id.value
        command = UpdateSpendingEntryCommand(
            entry_id=entry_id,
            merchant="New Merchant",
        )

        mock_repository.find_by_id.return_value = sample_entry
        mock_repository.save.return_value = None

        result = await handler.handle(command)

        assert result.success is True
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_success_category_update(
        self, handler, mock_repository, sample_entry
    ):
        """Test successful category update."""
        entry_id = sample_entry.id.value
        command = UpdateSpendingEntryCommand(
            entry_id=entry_id,
            category="Transportation",
        )

        mock_repository.find_by_id.return_value = sample_entry
        mock_repository.save.return_value = None

        result = await handler.handle(command)

        assert result.success is True
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_entry_not_found(self, handler, mock_repository):
        """Test handling when entry is not found."""
        command = UpdateSpendingEntryCommand(
            entry_id="550e8400-e29b-41d4-a716-446655440000",
            amount=150.0,
        )

        mock_repository.find_by_id.return_value = None

        result = await handler.handle(command)

        assert result.success is False
        assert "not found" in result.message
        assert "No entry found with ID" in result.errors[0]
        mock_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_validation_failure(self, handler, mock_repository):
        """Test handling validation failure."""
        command = UpdateSpendingEntryCommand(
            entry_id="invalid-id",  # Invalid UUID format
            amount=150.0,
        )

        result = await handler.handle(command)

        assert result.success is False
        assert "Invalid entry ID format" in result.error
        mock_repository.find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_repository_error(
        self, handler, mock_repository, sample_entry
    ):
        """Test handling repository error."""
        entry_id = sample_entry.id.value
        command = UpdateSpendingEntryCommand(
            entry_id=entry_id,
            amount=150.0,
        )

        mock_repository.find_by_id.return_value = sample_entry
        mock_repository.save.side_effect = Exception("Database error")

        result = await handler.handle(command)

        assert result.success is False
        assert "Failed to update spending entry" in result.message

    @pytest.mark.asyncio
    async def test_handle_multiple_field_updates(
        self, handler, mock_repository, sample_entry
    ):
        """Test updating multiple fields at once."""
        entry_id = sample_entry.id.value
        command = UpdateSpendingEntryCommand(
            entry_id=entry_id,
            amount=200.0,
            merchant="Updated Merchant",
            category="Entertainment",
        )

        mock_repository.find_by_id.return_value = sample_entry
        mock_repository.save.return_value = None

        result = await handler.handle(command)

        assert result.success is True
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_no_updates_provided(
        self, handler, mock_repository, sample_entry
    ):
        """Test when no update fields are provided."""
        entry_id = sample_entry.id.value
        command = UpdateSpendingEntryCommand(entry_id=entry_id)

        mock_repository.find_by_id.return_value = sample_entry
        mock_repository.save.return_value = None

        result = await handler.handle(command)

        # Should still succeed even with no changes
        assert result.success is True
        mock_repository.save.assert_called_once()


class TestUpdateSpendingEntryCommand:
    """Test UpdateSpendingEntryCommand validation."""

    def test_command_validation_success(self):
        """Test successful command validation."""
        command = UpdateSpendingEntryCommand(
            entry_id="550e8400-e29b-41d4-a716-446655440000",
            amount=100.0,
        )

        # Should not raise any exception
        command.validate()

    def test_command_validation_empty_entry_id(self):
        """Test validation with empty entry ID."""
        command = UpdateSpendingEntryCommand(
            entry_id="",
            amount=100.0,
        )

        with pytest.raises(ValueError, match="Entry ID cannot be empty"):
            command.validate()

    def test_command_validation_invalid_uuid(self):
        """Test validation with invalid UUID format."""
        command = UpdateSpendingEntryCommand(
            entry_id="invalid-uuid",
            amount=100.0,
        )

        with pytest.raises(ValueError, match="Invalid entry ID format"):
            command.validate()

    def test_command_validation_negative_amount(self):
        """Test validation with negative amount."""
        command = UpdateSpendingEntryCommand(
            entry_id="550e8400-e29b-41d4-a716-446655440000",
            amount=-50.0,
        )

        with pytest.raises(ValueError, match="Amount must be positive"):
            command.validate()

    def test_command_validation_zero_amount(self):
        """Test validation with zero amount."""
        command = UpdateSpendingEntryCommand(
            entry_id="550e8400-e29b-41d4-a716-446655440000",
            amount=0.0,
        )

        with pytest.raises(ValueError, match="Amount must be positive"):
            command.validate()

    def test_command_creation_with_all_fields(self):
        """Test creating command with all fields."""
        command = UpdateSpendingEntryCommand(
            entry_id="550e8400-e29b-41d4-a716-446655440000",
            amount=150.0,
            merchant="New Merchant",
            category="Transportation",
        )

        assert command.entry_id == "550e8400-e29b-41d4-a716-446655440000"
        assert command.amount == 150.0
        assert command.merchant == "New Merchant"
        assert command.category == "Transportation"

    def test_command_creation_minimal(self):
        """Test creating command with minimal fields."""
        command = UpdateSpendingEntryCommand(
            entry_id="550e8400-e29b-41d4-a716-446655440000"
        )

        assert command.entry_id == "550e8400-e29b-41d4-a716-446655440000"
        assert command.amount is None
        assert command.merchant is None
        assert command.category is None
