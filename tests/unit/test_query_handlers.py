"""Unit tests for query handlers."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from ai_service.application.queries.spending_queries import (
    GetSpendingEntriesQuery,
    GetSpendingEntriesQueryHandler,
    GetSpendingEntryByIdQuery,
    GetSpendingEntryByIdQueryHandler,
)
from ai_service.domain.entities.spending_entry import SpendingEntry, SpendingEntryId
from ai_service.domain.value_objects.money import Currency, Money
from ai_service.domain.value_objects.spending_category import SpendingCategory


@pytest.mark.unit
class TestGetSpendingEntryByIdQueryHandler:
    """Test GetSpendingEntryByIdQueryHandler."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def query_handler(self, mock_repository):
        """Create query handler with mock repository."""
        return GetSpendingEntryByIdQueryHandler(mock_repository)

    @pytest.fixture
    def sample_entry(self):
        """Create sample spending entry."""
        return SpendingEntry.create(
            merchant="Test Cafe",
            amount=Money.from_float(25.50, Currency.USD),
            category=SpendingCategory.FOOD_DINING,
            description="Coffee and pastry",
        )

    @pytest.fixture
    def valid_query(self, sample_entry):
        """Create valid query."""
        return GetSpendingEntryByIdQuery(entry_id=str(sample_entry.id.value))

    async def test_handle_success(
        self, query_handler, valid_query, mock_repository, sample_entry
    ):
        """Test successful query handling."""
        # Setup
        mock_repository.find_by_id.return_value = sample_entry

        # Execute
        result = await query_handler.handle(valid_query)

        # Verify
        assert result.success is True
        assert result.data is not None
        assert result.data.id.value == sample_entry.id.value
        assert result.data.merchant == "Test Cafe"
        assert result.data.amount.amount == sample_entry.amount.amount

        # Verify repository was called with correct ID
        mock_repository.find_by_id.assert_called_once()
        called_id = mock_repository.find_by_id.call_args[0][0]
        assert str(called_id.value) == str(sample_entry.id.value)

    async def test_handle_entry_not_found(
        self, query_handler, valid_query, mock_repository
    ):
        """Test handling when entry is not found."""
        # Setup
        mock_repository.find_by_id.return_value = None

        # Execute
        result = await query_handler.handle(valid_query)

        # Verify
        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower()

    async def test_handle_validation_failure(self, query_handler, mock_repository):
        """Test handling with validation failure."""
        # Create invalid query
        invalid_query = GetSpendingEntryByIdQuery(entry_id="invalid-id")

        # Execute
        result = await query_handler.handle(invalid_query)

        # Verify
        assert result.success is False
        assert result.error is not None
        assert "invalid" in result.error.lower()

        # Repository should not be called
        mock_repository.find_by_id.assert_not_called()

    async def test_handle_repository_error(
        self, query_handler, valid_query, mock_repository
    ):
        """Test handling with repository error."""
        # Setup repository to raise exception
        mock_repository.find_by_id.side_effect = Exception("Database error")

        # Execute
        result = await query_handler.handle(valid_query)

        # Verify
        assert result.success is False
        assert result.error is not None
        assert "database error" in result.error.lower()

    async def test_handle_empty_entry_id(self, query_handler, mock_repository):
        """Test handling with empty entry ID."""
        invalid_query = GetSpendingEntryByIdQuery(entry_id="")

        result = await query_handler.handle(invalid_query)

        assert result.success is False
        assert result.error is not None
        mock_repository.find_by_id.assert_not_called()


@pytest.mark.unit
class TestGetSpendingEntriesQueryHandler:
    """Test GetSpendingEntriesQueryHandler."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def query_handler(self, mock_repository):
        """Create query handler with mock repository."""
        return GetSpendingEntriesQueryHandler(mock_repository)

    @pytest.fixture
    def sample_entries(self):
        """Create sample spending entries."""
        entries = []
        for i in range(3):
            entry = SpendingEntry.create(
                merchant=f"Merchant {i}",
                amount=Money.from_float(10.0 + i, Currency.USD),
                category=SpendingCategory.FOOD_DINING,
                description=f"Description {i}",
            )
            entries.append(entry)
        return entries

    @pytest.fixture
    def default_query(self):
        """Create default query."""
        return GetSpendingEntriesQuery()

    async def test_handle_success(
        self, query_handler, default_query, mock_repository, sample_entries
    ):
        """Test successful query handling."""
        # Setup
        mock_repository.find_all.return_value = sample_entries
        mock_repository.count_total.return_value = len(sample_entries)

        # Execute
        result = await query_handler.handle(default_query)

        # Verify
        assert result.success is True
        assert result.data is not None
        assert len(result.data["entries"]) == 3
        assert result.data["total_count"] == 3
        assert result.data["has_more"] is False

        # Verify repository was called correctly
        mock_repository.find_all.assert_called_once_with(
            limit=10,  # actual default limit from query
            offset=0,  # default offset
        )

    async def test_handle_with_pagination(
        self, query_handler, mock_repository, sample_entries
    ):
        """Test handling with pagination parameters."""
        query = GetSpendingEntriesQuery(limit=2, offset=1)

        # Setup
        mock_repository.find_all.return_value = sample_entries[1:3]  # Skip first entry
        mock_repository.count_total.return_value = 3

        # Execute
        result = await query_handler.handle(query)

        # Verify
        assert result.success is True
        assert len(result.data["entries"]) == 2
        assert result.data["total_count"] == 3
        assert result.data["has_more"] is False  # offset(1) + returned(2) < total(3)

        # Verify repository was called with correct parameters
        mock_repository.find_all.assert_called_once_with(limit=2, offset=1)

    async def test_handle_with_category_filter(
        self, query_handler, mock_repository, sample_entries
    ):
        """Test handling with category filter."""
        query = GetSpendingEntriesQuery(category="Food & Dining")

        # Setup
        mock_repository.find_all.return_value = sample_entries
        mock_repository.count_total.return_value = len(sample_entries)

        # Execute
        result = await query_handler.handle(query)

        # Verify
        assert result.success is True

        # Verify repository was called with category filter
        mock_repository.find_all.assert_called_once_with(limit=10, offset=0)

    async def test_handle_with_date_range(
        self, query_handler, mock_repository, sample_entries
    ):
        """Test handling with date range filter."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        query = GetSpendingEntriesQuery(date_from=start_date, date_to=end_date)

        # Setup
        mock_repository.find_all.return_value = sample_entries
        mock_repository.count_total.return_value = len(sample_entries)

        # Execute
        result = await query_handler.handle(query)

        # Verify
        assert result.success is True

        # Verify repository was called with date range
        mock_repository.find_all.assert_called_once_with(limit=10, offset=0)

    async def test_handle_empty_results(
        self, query_handler, default_query, mock_repository
    ):
        """Test handling when no entries are found."""
        # Setup
        mock_repository.find_all.return_value = []
        mock_repository.count_total.return_value = 0

        # Execute
        result = await query_handler.handle(default_query)

        # Verify
        assert result.success is True
        assert result.data is not None
        assert len(result.data["entries"]) == 0
        assert result.data["total_count"] == 0
        assert result.data["has_more"] is False

    async def test_handle_validation_failure(self, query_handler, mock_repository):
        """Test handling with validation failure."""
        # Create invalid query
        invalid_query = GetSpendingEntriesQuery(limit=-1)  # Invalid limit

        # Execute
        result = await query_handler.handle(invalid_query)

        # Verify
        assert result.success is False
        assert result.error is not None

        # Repository should not be called
        mock_repository.find_all.assert_not_called()

    async def test_handle_repository_error(
        self, query_handler, default_query, mock_repository
    ):
        """Test handling with repository error."""
        # Setup repository to raise exception
        mock_repository.find_all.side_effect = Exception("Database error")

        # Execute
        result = await query_handler.handle(default_query)

        # Verify
        assert result.success is False
        assert result.error is not None
        assert "database error" in result.error.lower()

    async def test_has_more_calculation(
        self, query_handler, mock_repository, sample_entries
    ):
        """Test has_more flag calculation."""
        # Test case where there are more entries
        query = GetSpendingEntriesQuery(limit=2, offset=0)

        mock_repository.find_all.return_value = sample_entries[:2]
        mock_repository.count_total.return_value = 5  # More entries exist

        result = await query_handler.handle(query)

        assert result.success is True
        assert result.data["has_more"] is True  # offset(0) + returned(2) < total(5)

    async def test_entry_serialization(
        self, query_handler, default_query, mock_repository, sample_entries
    ):
        """Test that entries are properly serialized."""
        # Setup
        mock_repository.find_all.return_value = [sample_entries[0]]
        mock_repository.count_total.return_value = 1

        # Execute
        result = await query_handler.handle(default_query)

        # Verify entry structure
        assert result.success is True
        entry_data = result.data["entries"][0]

        # entry_data is a SpendingEntry object, not a dictionary
        assert hasattr(entry_data, "id")
        assert hasattr(entry_data, "merchant")
        assert hasattr(entry_data, "amount")
        assert hasattr(entry_data, "category")
        assert hasattr(entry_data, "description")
        assert hasattr(entry_data, "created_at")
        assert hasattr(entry_data, "updated_at")


@pytest.mark.unit
class TestQueryValidation:
    """Test query validation logic."""

    def test_get_entry_by_id_validation(self):
        """Test GetSpendingEntryByIdQuery validation."""
        # Valid query
        entry_id = str(SpendingEntryId.generate().value)
        valid_query = GetSpendingEntryByIdQuery(entry_id=entry_id)

        # Should not raise exception
        valid_query.validate()

    def test_get_entry_by_id_validation_failures(self):
        """Test GetSpendingEntryByIdQuery validation failures."""
        # Empty entry ID
        query = GetSpendingEntryByIdQuery(entry_id="")
        with pytest.raises(ValueError, match="Entry ID cannot be empty"):
            query.validate()

        # Invalid UUID format
        query = GetSpendingEntryByIdQuery(entry_id="invalid-uuid")
        with pytest.raises(ValueError, match="Invalid entry ID format"):
            query.validate()

    def test_get_entries_validation(self):
        """Test GetSpendingEntriesQuery validation."""
        # Valid query with all parameters
        valid_query = GetSpendingEntriesQuery(
            limit=10,
            offset=0,
            category="Food & Dining",
            date_from=datetime.utcnow() - timedelta(days=7),
            date_to=datetime.utcnow(),
        )

        # Should not raise exception
        valid_query.validate()

    def test_get_entries_validation_failures(self):
        """Test GetSpendingEntriesQuery validation failures."""
        # Invalid limit
        query = GetSpendingEntriesQuery(limit=-1)
        with pytest.raises(ValueError, match="Limit must be positive"):
            query.validate()

        query = GetSpendingEntriesQuery(limit=1001)
        with pytest.raises(ValueError, match="Limit cannot exceed"):
            query.validate()

        # Invalid offset
        query = GetSpendingEntriesQuery(offset=-1)
        with pytest.raises(ValueError, match="Offset cannot be negative"):
            query.validate()

        # Invalid date range
        start_date = datetime.utcnow()
        end_date = start_date - timedelta(days=1)  # End before start

        query = GetSpendingEntriesQuery(date_from=start_date, date_to=end_date)
        with pytest.raises(ValueError, match="date_from must be before date_to"):
            query.validate()

    def test_default_values(self):
        """Test default values for queries."""
        query = GetSpendingEntriesQuery()

        assert query.limit == 10
        assert query.offset == 0
        assert query.category is None
        assert query.date_from is None
        assert query.date_to is None
