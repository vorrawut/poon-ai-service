"""Unit tests for CQRS commands and queries."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from ai_service.application.commands.spending_commands import (
    CreateSpendingEntryCommand,
    CreateSpendingEntryCommandHandler,
    UpdateSpendingEntryCommand,
)
from ai_service.application.queries.spending_queries import (
    GetSpendingEntriesQuery,
    GetSpendingEntriesQueryHandler,
    GetSpendingEntryByIdQuery,
    GetSpendingEntryByIdQueryHandler,
)
from ai_service.domain.entities.spending_entry import SpendingEntry, SpendingEntryId
from ai_service.domain.value_objects.confidence import ConfidenceScore
from ai_service.domain.value_objects.money import Currency, Money
from ai_service.domain.value_objects.processing_method import ProcessingMethod
from ai_service.domain.value_objects.spending_category import (
    PaymentMethod,
    SpendingCategory,
)


@pytest.mark.unit
class TestCreateSpendingEntryCommand:
    """Test CreateSpendingEntryCommand."""

    def test_command_creation(self):
        """Test creating a command."""
        command = CreateSpendingEntryCommand(
            amount=100.0,
            currency="THB",
            merchant="Test Cafe",
            description="Coffee and pastry",
            transaction_date=datetime(2024, 1, 15, 10, 30),
            category="Food & Dining",
            payment_method="Credit Card",
        )

        assert command.amount == 100.0
        assert command.currency == "THB"
        assert command.merchant == "Test Cafe"
        assert command.description == "Coffee and pastry"
        assert command.category == "Food & Dining"
        assert command.payment_method == "Credit Card"

    def test_command_validation_success(self):
        """Test successful command validation."""
        command = CreateSpendingEntryCommand(
            amount=100.0,
            currency="THB",
            merchant="Test Cafe",
            description="Coffee and pastry",
            transaction_date=datetime.utcnow(),
            category="Food & Dining",
            payment_method="Credit Card",
        )

        # Should not raise any exception
        command.validate()

    def test_command_validation_empty_merchant(self):
        """Test validation with empty merchant."""
        command = CreateSpendingEntryCommand(
            amount=100.0,
            currency="THB",
            merchant="",
            description="Coffee and pastry",
            transaction_date=datetime.utcnow(),
            category="Food & Dining",
            payment_method="Credit Card",
        )

        with pytest.raises(ValueError, match="Merchant cannot be empty"):
            command.validate()

    def test_command_validation_empty_description(self):
        """Test validation with empty description."""
        command = CreateSpendingEntryCommand(
            amount=100.0,
            currency="THB",
            merchant="Test Cafe",
            description="",
            transaction_date=datetime.utcnow(),
            category="Food & Dining",
            payment_method="Credit Card",
        )

        with pytest.raises(ValueError, match="Description cannot be empty"):
            command.validate()

    def test_command_validation_negative_amount(self):
        """Test validation with negative amount."""
        command = CreateSpendingEntryCommand(
            amount=-100.0,
            currency="THB",
            merchant="Test Cafe",
            description="Coffee and pastry",
            transaction_date=datetime.utcnow(),
            category="Food & Dining",
            payment_method="Credit Card",
        )

        with pytest.raises(ValueError, match="Amount must be positive"):
            command.validate()


@pytest.mark.unit
class TestCreateSpendingEntryCommandHandler:
    """Test CreateSpendingEntryCommandHandler."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        repository = AsyncMock()
        repository.save.return_value = None
        return repository

    @pytest.fixture
    def valid_command(self):
        """Create a valid command."""
        return CreateSpendingEntryCommand(
            amount=100.0,
            currency="THB",
            merchant="Test Cafe",
            description="Coffee and pastry",
            transaction_date=datetime(2024, 1, 15, 10, 30),
            category="Food & Dining",
            payment_method="Credit Card",
        )

    async def test_handler_success(self, mock_repository, valid_command):
        """Test successful command handling."""
        handler = CreateSpendingEntryCommandHandler(mock_repository)
        result = await handler.handle(valid_command)

        assert result.is_success()
        assert result.message == "Spending entry created successfully"
        assert "entry_id" in result.data

        # Verify repository was called
        mock_repository.save.assert_called_once()

    async def test_handler_validation_failure(self, mock_repository):
        """Test handler with invalid command."""
        invalid_command = CreateSpendingEntryCommand(
            amount=-100.0,  # Invalid negative amount
            currency="THB",
            merchant="Test Cafe",
            description="Coffee and pastry",
            transaction_date=datetime.utcnow(),
            category="Food & Dining",
            payment_method="Credit Card",
        )

        handler = CreateSpendingEntryCommandHandler(mock_repository)
        result = await handler.handle(invalid_command)

        assert result.is_failure()
        assert "Amount must be positive" in result.message

        # Verify repository was not called
        mock_repository.save.assert_not_called()

    async def test_handler_repository_error(self, mock_repository, valid_command):
        """Test handler with repository error."""
        mock_repository.save.side_effect = Exception("Database error")

        handler = CreateSpendingEntryCommandHandler(mock_repository)
        result = await handler.handle(valid_command)

        assert result.is_failure()
        assert "Failed to save spending entry" in result.message


@pytest.mark.unit
class TestUpdateSpendingEntryCommand:
    """Test UpdateSpendingEntryCommand."""

    def test_command_creation(self):
        """Test creating an update command."""
        entry_id = str(SpendingEntryId())
        command = UpdateSpendingEntryCommand(
            entry_id=entry_id,
            amount=150.0,
            merchant="Updated Cafe",
            description="Updated description",
        )

        assert command.entry_id == entry_id
        assert command.amount == 150.0
        assert command.merchant == "Updated Cafe"
        assert command.description == "Updated description"

    def test_command_validation_success(self):
        """Test successful validation."""
        entry_id = str(SpendingEntryId())
        command = UpdateSpendingEntryCommand(entry_id=entry_id, amount=150.0)

        # Should not raise any exception
        command.validate()

    def test_command_validation_invalid_entry_id(self):
        """Test validation with invalid entry ID."""
        command = UpdateSpendingEntryCommand(entry_id="invalid-uuid", amount=150.0)

        with pytest.raises(ValueError, match="Invalid entry ID format"):
            command.validate()


@pytest.mark.unit
class TestGetSpendingEntryByIdQuery:
    """Test GetSpendingEntryByIdQuery."""

    def test_query_creation(self):
        """Test creating a query."""
        entry_id = str(SpendingEntryId())
        query = GetSpendingEntryByIdQuery(entry_id=entry_id)

        assert query.entry_id == entry_id

    def test_query_validation_success(self):
        """Test successful validation."""
        entry_id = str(SpendingEntryId())
        query = GetSpendingEntryByIdQuery(entry_id=entry_id)

        # Should not raise any exception
        query.validate()

    def test_query_validation_invalid_id(self):
        """Test validation with invalid ID."""
        query = GetSpendingEntryByIdQuery(entry_id="invalid-uuid")

        with pytest.raises(ValueError, match="Invalid entry ID format"):
            query.validate()


@pytest.mark.unit
class TestGetSpendingEntryByIdQueryHandler:
    """Test GetSpendingEntryByIdQueryHandler."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock()

    @pytest.fixture
    def sample_entry(self):
        """Create a sample spending entry."""
        return SpendingEntry(
            amount=Money.from_float(100.0, Currency.THB),
            merchant="Test Cafe",
            description="Coffee and pastry",
            transaction_date=datetime(2024, 1, 15, 10, 30),
            category=SpendingCategory.FOOD_DINING,
            payment_method=PaymentMethod.CREDIT_CARD,
            confidence=ConfidenceScore.high(),
            processing_method=ProcessingMethod.MANUAL_ENTRY,
        )

    async def test_handler_success(self, mock_repository, sample_entry):
        """Test successful query handling."""
        entry_id = str(sample_entry.id)
        mock_repository.find_by_id.return_value = sample_entry

        query = GetSpendingEntryByIdQuery(entry_id=entry_id)
        handler = GetSpendingEntryByIdQueryHandler(mock_repository)
        result = await handler.handle(query)

        assert result.is_success()
        assert result.data == sample_entry

        # Verify repository was called with correct ID
        mock_repository.find_by_id.assert_called_once_with(SpendingEntryId(entry_id))

    async def test_handler_entry_not_found(self, mock_repository):
        """Test handler when entry is not found."""
        entry_id = str(SpendingEntryId())
        mock_repository.find_by_id.return_value = None

        query = GetSpendingEntryByIdQuery(entry_id=entry_id)
        handler = GetSpendingEntryByIdQueryHandler(mock_repository)
        result = await handler.handle(query)

        assert result.is_failure()
        assert "Spending entry not found" in result.message

    async def test_handler_validation_failure(self, mock_repository):
        """Test handler with invalid query."""
        query = GetSpendingEntryByIdQuery(entry_id="invalid-uuid")
        handler = GetSpendingEntryByIdQueryHandler(mock_repository)
        result = await handler.handle(query)

        assert result.is_failure()
        assert "Invalid entry ID format" in result.message

        # Verify repository was not called
        mock_repository.find_by_id.assert_not_called()


@pytest.mark.unit
class TestGetSpendingEntriesQuery:
    """Test GetSpendingEntriesQuery."""

    def test_query_creation_defaults(self):
        """Test creating query with defaults."""
        query = GetSpendingEntriesQuery()

        assert query.limit == 10
        assert query.offset == 0
        assert query.category is None
        assert query.payment_method is None
        assert query.date_from is None
        assert query.date_to is None

    def test_query_creation_with_parameters(self):
        """Test creating query with parameters."""
        date_from = datetime(2024, 1, 1)
        date_to = datetime(2024, 1, 31)

        query = GetSpendingEntriesQuery(
            limit=20,
            offset=10,
            category="Food & Dining",
            payment_method="Credit Card",
            date_from=date_from,
            date_to=date_to,
        )

        assert query.limit == 20
        assert query.offset == 10
        assert query.category == "Food & Dining"
        assert query.payment_method == "Credit Card"
        assert query.date_from == date_from
        assert query.date_to == date_to

    def test_query_validation_success(self):
        """Test successful validation."""
        query = GetSpendingEntriesQuery(limit=20, offset=0)

        # Should not raise any exception
        query.validate()

    def test_query_validation_invalid_limit(self):
        """Test validation with invalid limit."""
        query = GetSpendingEntriesQuery(limit=0)

        with pytest.raises(ValueError, match="Limit must be positive"):
            query.validate()

    def test_query_validation_invalid_offset(self):
        """Test validation with invalid offset."""
        query = GetSpendingEntriesQuery(offset=-1)

        with pytest.raises(ValueError, match="Offset cannot be negative"):
            query.validate()

    def test_query_validation_invalid_date_range(self):
        """Test validation with invalid date range."""
        query = GetSpendingEntriesQuery(
            date_from=datetime(2024, 1, 31), date_to=datetime(2024, 1, 1)
        )

        with pytest.raises(ValueError, match="date_from must be before date_to"):
            query.validate()


@pytest.mark.unit
class TestGetSpendingEntriesQueryHandler:
    """Test GetSpendingEntriesQueryHandler."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository."""
        return AsyncMock()

    @pytest.fixture
    def sample_entries(self):
        """Create sample spending entries."""
        return [
            SpendingEntry(
                amount=Money.from_float(100.0, Currency.THB),
                merchant="Cafe A",
                description="Coffee",
                transaction_date=datetime(2024, 1, 15),
                category=SpendingCategory.FOOD_DINING,
                payment_method=PaymentMethod.CREDIT_CARD,
                confidence=ConfidenceScore.high(),
                processing_method=ProcessingMethod.MANUAL_ENTRY,
            ),
            SpendingEntry(
                amount=Money.from_float(200.0, Currency.THB),
                merchant="Restaurant B",
                description="Dinner",
                transaction_date=datetime(2024, 1, 16),
                category=SpendingCategory.FOOD_DINING,
                payment_method=PaymentMethod.CASH,
                confidence=ConfidenceScore.medium(),
                processing_method=ProcessingMethod.MANUAL_ENTRY,
            ),
        ]

    async def test_handler_success(self, mock_repository, sample_entries):
        """Test successful query handling."""
        mock_repository.find_all.return_value = sample_entries
        mock_repository.count_total.return_value = 2

        query = GetSpendingEntriesQuery(limit=10)
        handler = GetSpendingEntriesQueryHandler(mock_repository)
        result = await handler.handle(query)

        assert result.is_success()
        assert result.data["entries"] == sample_entries
        assert result.data["total_count"] == 2

        # Verify repository was called
        mock_repository.find_all.assert_called_once()
        mock_repository.count_total.assert_called_once()

    async def test_handler_empty_results(self, mock_repository):
        """Test handler with empty results."""
        mock_repository.find_all.return_value = []
        mock_repository.count_total.return_value = 0

        query = GetSpendingEntriesQuery()
        handler = GetSpendingEntriesQueryHandler(mock_repository)
        result = await handler.handle(query)

        assert result.is_success()
        assert result.data["entries"] == []
        assert result.data["total_count"] == 0

    async def test_handler_validation_failure(self, mock_repository):
        """Test handler with invalid query."""
        query = GetSpendingEntriesQuery(limit=0)  # Invalid limit
        handler = GetSpendingEntriesQueryHandler(mock_repository)
        result = await handler.handle(query)

        assert result.is_failure()
        assert "Limit must be positive" in result.message

        # Verify repository was not called
        mock_repository.find_all.assert_not_called()
        mock_repository.count_total.assert_not_called()
