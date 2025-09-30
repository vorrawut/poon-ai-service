"""Unit tests for command handlers."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from ai_service.application.commands.spending_commands import (
    CreateSpendingEntryCommand,
    CreateSpendingEntryCommandHandler,
    ProcessTextCommand,
    ProcessTextCommandHandler,
)
from ai_service.domain.entities.spending_entry import SpendingEntry
from ai_service.domain.value_objects.money import Currency
from ai_service.domain.value_objects.spending_category import SpendingCategory
from ai_service.domain.value_objects.text_content import TextContent


@pytest.mark.unit
class TestCreateSpendingEntryCommandHandler:
    """Test CreateSpendingEntryCommandHandler."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def command_handler(self, mock_repository):
        """Create command handler with mock repository."""
        return CreateSpendingEntryCommandHandler(mock_repository)

    @pytest.fixture
    def valid_command(self):
        """Create valid command."""
        from datetime import datetime

        return CreateSpendingEntryCommand(
            merchant="Test Cafe",
            amount=25.50,
            currency="USD",
            category="Food & Dining",
            description="Coffee and pastry",
            transaction_date=datetime.utcnow(),
        )

    async def test_handle_success(
        self, command_handler, valid_command, mock_repository
    ):
        """Test successful command handling."""
        # Setup
        mock_repository.save.return_value = None

        # Execute
        result = await command_handler.handle(valid_command)

        # Verify
        assert result.success is True
        assert result.data is not None
        assert "entry_id" in result.data

        # Verify repository was called
        mock_repository.save.assert_called_once()
        saved_entry = mock_repository.save.call_args[0][0]
        assert isinstance(saved_entry, SpendingEntry)
        assert saved_entry.merchant == "Test Cafe"
        assert saved_entry.amount.amount == Decimal("25.50")
        assert saved_entry.amount.currency == Currency.USD
        assert saved_entry.category == SpendingCategory.FOOD_DINING

    async def test_handle_validation_failure(self, command_handler, mock_repository):
        """Test handling with validation failure."""
        # Create invalid command
        invalid_command = CreateSpendingEntryCommand(
            merchant="",  # Empty merchant should fail validation
            amount=25.50,
            currency="USD",
            category="Food & Dining",
            description="Test",
            transaction_date=datetime.utcnow(),
        )

        # Execute
        result = await command_handler.handle(invalid_command)

        # Verify
        assert result.success is False
        assert result.error is not None
        assert "merchant" in result.error.lower()

        # Repository should not be called
        mock_repository.save.assert_not_called()

    async def test_handle_repository_error(
        self, command_handler, valid_command, mock_repository
    ):
        """Test handling with repository error."""
        # Setup repository to raise exception
        mock_repository.save.side_effect = Exception("Database error")

        # Execute
        result = await command_handler.handle(valid_command)

        # Verify
        assert result.success is False
        assert result.error is not None
        assert "database error" in result.error.lower()

    async def test_handle_invalid_currency(self, command_handler, mock_repository):
        """Test handling with invalid currency."""
        invalid_command = CreateSpendingEntryCommand(
            merchant="Test Cafe",
            amount=25.50,
            currency="INVALID",  # Invalid currency
            category="Food & Dining",
            description="Test",
            transaction_date=datetime.utcnow(),
        )

        result = await command_handler.handle(invalid_command)

        assert result.success is False
        assert result.error is not None
        mock_repository.save.assert_not_called()

    async def test_handle_invalid_category(self, command_handler, mock_repository):
        """Test handling with invalid category."""
        invalid_command = CreateSpendingEntryCommand(
            merchant="Test Cafe",
            amount=25.50,
            currency="USD",
            category="Invalid Category",  # Invalid category
            description="Test",
            transaction_date=datetime.utcnow(),
        )

        result = await command_handler.handle(invalid_command)

        assert result.success is False
        assert result.error is not None
        mock_repository.save.assert_not_called()

    async def test_handle_negative_amount(self, command_handler, mock_repository):
        """Test handling with negative amount."""
        invalid_command = CreateSpendingEntryCommand(
            merchant="Test Cafe",
            amount=-25.50,  # Negative amount
            currency="USD",
            category="Food & Dining",
            description="Test",
            transaction_date=datetime.utcnow(),
        )

        result = await command_handler.handle(invalid_command)

        assert result.success is False
        assert result.error is not None
        mock_repository.save.assert_not_called()


@pytest.mark.unit
class TestProcessTextCommandHandler:
    """Test ProcessTextCommandHandler."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_llama_client(self):
        """Create mock Llama client."""
        mock_client = AsyncMock()
        mock_client.parse_spending_text.return_value = {
            "merchant": "Coffee Shop",
            "amount": 4.50,
            "category": "Food & Dining",
            "description": "Coffee purchase",
        }
        return mock_client

    @pytest.fixture
    def command_handler(self, mock_repository, mock_llama_client):
        """Create command handler with mocks."""
        return ProcessTextCommandHandler(
            repository=mock_repository, text_processing_service=mock_llama_client
        )

    @pytest.fixture
    def valid_command(self):
        """Create valid process text command."""
        return ProcessTextCommand(text="Coffee at Coffee Shop $4.50")

    async def test_handle_success_with_ai(
        self, command_handler, valid_command, mock_repository, mock_llama_client
    ):
        """Test successful text processing with AI enhancement."""
        # Setup
        mock_repository.save.return_value = None

        # Execute
        result = await command_handler.handle(valid_command)

        # Verify
        assert result.success is True
        assert result.data is not None
        assert "entry_id" in result.data
        assert "confidence" in result.data
        assert "processing_method" in result.data

        # Verify text processing service was called
        mock_llama_client.process_text.assert_called_once()

        # Verify repository was called
        mock_repository.save.assert_called_once()

    async def test_handle_success_without_ai(
        self, command_handler, mock_repository, mock_llama_client
    ):
        """Test successful text processing without AI enhancement."""
        command = ProcessTextCommand(text="Coffee at Coffee Shop $4.50")

        # Execute
        result = await command_handler.handle(command)

        # Verify
        assert result.success is True
        assert result.data is not None

        # AI client should not be called
        mock_llama_client.parse_spending_text.assert_not_called()

        # Repository should still be called (with basic parsing)
        mock_repository.save.assert_called_once()

    async def test_handle_ai_parsing_failure(
        self, command_handler, valid_command, mock_repository, mock_llama_client
    ):
        """Test handling when AI parsing fails."""
        # Setup AI to return None (parsing failure)
        mock_llama_client.parse_spending_text.return_value = None

        # Execute
        result = await command_handler.handle(valid_command)

        # Should fall back to basic parsing
        assert result.success is True
        mock_repository.save.assert_called_once()

    async def test_handle_ai_client_error(
        self, command_handler, valid_command, mock_repository, mock_llama_client
    ):
        """Test handling when AI client raises exception."""
        # Setup AI to raise exception
        mock_llama_client.parse_spending_text.side_effect = Exception(
            "AI service error"
        )

        # Execute
        result = await command_handler.handle(valid_command)

        # Should fall back to basic parsing
        assert result.success is True
        mock_repository.save.assert_called_once()

    async def test_handle_empty_text(
        self, command_handler, mock_repository, mock_llama_client
    ):
        """Test handling with empty text."""
        command = ProcessTextCommand(text="")

        result = await command_handler.handle(command)

        assert result.success is False
        assert result.error is not None
        mock_repository.save.assert_not_called()

    async def test_handle_repository_error(
        self, command_handler, valid_command, mock_repository, mock_llama_client
    ):
        """Test handling with repository error."""
        # Setup repository to raise exception
        mock_repository.save.side_effect = Exception("Database error")

        result = await command_handler.handle(valid_command)

        assert result.success is False
        assert result.error is not None
        assert "database error" in result.error.lower()

    async def test_text_content_creation(
        self, command_handler, mock_repository, mock_llama_client
    ):
        """Test that TextContent is created properly."""
        command = ProcessTextCommand(text="Test spending text")

        # Mock the text processing service to verify TextContent creation
        async def mock_process_text(text_content, context=None):  # noqa: ARG001
            # Verify TextContent is created properly
            assert isinstance(text_content, TextContent)
            assert text_content.content == "Test spending text"

            # Return a mock processing result
            from unittest.mock import MagicMock

            mock_result = MagicMock()
            mock_result.success = True
            mock_result.spending_entry = MagicMock()
            mock_result.spending_entry.id.value = "test-id"
            mock_result.spending_entry.confidence.value = 0.8
            mock_result.spending_entry.processing_method.value = "manual"
            return mock_result

        mock_llama_client.process_text = mock_process_text

        result = await command_handler.handle(command)
        assert result.success is True


@pytest.mark.unit
class TestCommandValidation:
    """Test command validation logic."""

    def test_create_command_validation(self):
        """Test CreateSpendingEntryCommand validation."""
        # Valid command
        valid_command = CreateSpendingEntryCommand(
            merchant="Test Cafe",
            amount=25.50,
            currency="USD",
            category="Food & Dining",
            description="Test",
            transaction_date=datetime.utcnow(),
        )

        # Should not raise exception
        valid_command.validate()

    def test_create_command_validation_failures(self):
        """Test CreateSpendingEntryCommand validation failures."""
        # Empty merchant
        command = CreateSpendingEntryCommand(
            merchant="",
            amount=25.50,
            currency="USD",
            category="Food & Dining",
            description="Test",
            transaction_date=datetime.utcnow(),
        )
        with pytest.raises(ValueError, match="Merchant cannot be empty"):
            command.validate()

        # Negative amount
        command = CreateSpendingEntryCommand(
            merchant="Test Cafe",
            amount=-25.50,
            currency="USD",
            category="Food & Dining",
            description="Test",
            transaction_date=datetime.utcnow(),
        )
        with pytest.raises(ValueError, match="Amount must be positive"):
            command.validate()

    def test_process_text_command_validation(self):
        """Test ProcessTextCommand validation."""
        # Valid command
        valid_command = ProcessTextCommand(text="Coffee at Coffee Shop $4.50")

        # Should not raise exception
        valid_command.validate()

    def test_process_text_command_validation_failures(self):
        """Test ProcessTextCommand validation failures."""
        # Empty text
        command = ProcessTextCommand(text="")
        with pytest.raises(ValueError, match="Text cannot be empty"):
            command.validate()

        # Whitespace only text
        command = ProcessTextCommand(text="   ")
        with pytest.raises(ValueError, match="Text cannot be empty"):
            command.validate()
