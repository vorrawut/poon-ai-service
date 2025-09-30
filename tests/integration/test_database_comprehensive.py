"""Comprehensive integration tests for database operations."""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from ai_service.domain.entities.spending_entry import SpendingEntry
from ai_service.domain.value_objects.money import Currency, Money
from ai_service.domain.value_objects.spending_category import SpendingCategory
from ai_service.infrastructure.database.sqlite_repository import (
    SqliteSpendingRepository,
)


@pytest.mark.integration
class TestSqliteSpendingRepositoryComprehensive:
    """Comprehensive tests for SQLite spending repository."""

    @pytest.fixture
    async def repository(self):
        """Create a test repository with temporary database."""
        # Create temporary database file
        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()

        repo = SqliteSpendingRepository(f"sqlite:///{temp_db.name}")
        await repo.initialize()
        yield repo
        await repo.close()

    @pytest.fixture
    def sample_entry(self):
        """Create a sample spending entry for testing."""
        return SpendingEntry.create(
            merchant="Test Cafe",
            amount=Money.from_float(25.50, Currency.USD),
            category=SpendingCategory.FOOD_DINING,
            description="Coffee and pastry",
        )

    async def test_save_and_retrieve(self, repository, sample_entry):
        """Test saving and retrieving an entry."""
        # Save entry
        await repository.save(sample_entry)

        # Retrieve by ID
        retrieved = await repository.find_by_id(sample_entry.id)

        assert retrieved is not None
        assert retrieved.id == sample_entry.id
        assert retrieved.merchant == sample_entry.merchant
        assert retrieved.amount.amount == sample_entry.amount.amount
        assert retrieved.category == sample_entry.category

    async def test_find_all_empty(self, repository):
        """Test finding all entries when repository is empty."""
        entries = await repository.find_all()
        assert len(entries) == 0

    async def test_find_all_with_entries(self, repository):
        """Test finding all entries with multiple entries."""
        # Create multiple entries
        entries = []
        for i in range(3):
            entry = SpendingEntry.create(
                merchant=f"Merchant {i}",
                amount=Money.from_float(10.0 + i, Currency.USD),
                category=SpendingCategory.FOOD_DINING,
                description=f"Description {i}",
            )
            entries.append(entry)
            await repository.save(entry)

        # Retrieve all
        all_entries = await repository.find_all()
        assert len(all_entries) == 3

        # Check they're sorted by created_at (newest first)
        for i in range(len(all_entries) - 1):
            assert all_entries[i].created_at >= all_entries[i + 1].created_at

    async def test_find_all_with_pagination(self, repository):
        """Test pagination with limit and offset."""
        # Create 5 entries
        for i in range(5):
            entry = SpendingEntry.create(
                merchant=f"Merchant {i}",
                amount=Money.from_float(10.0 + i, Currency.USD),
                category=SpendingCategory.FOOD_DINING,
                description=f"Transaction {i}",
            )
            await repository.save(entry)

        # Test limit
        limited = await repository.find_all(limit=3)
        assert len(limited) == 3

        # Test offset
        offset = await repository.find_all(limit=3, offset=2)
        assert len(offset) == 3

        # Test limit + offset
        page = await repository.find_all(limit=2, offset=1)
        assert len(page) == 2

    async def test_find_by_category(self, repository):
        """Test finding entries by category."""
        # Create entries with different categories
        food_entry = SpendingEntry.create(
            merchant="Restaurant",
            amount=Money.from_float(30.0, Currency.USD),
            category=SpendingCategory.FOOD_DINING,
            description="Dinner at restaurant",
        )
        transport_entry = SpendingEntry.create(
            merchant="Taxi",
            amount=Money.from_float(15.0, Currency.USD),
            category=SpendingCategory.TRANSPORTATION,
            description="Taxi ride",
        )

        await repository.save(food_entry)
        await repository.save(transport_entry)

        # Find by category
        food_entries = await repository.find_by_category(SpendingCategory.FOOD_DINING)
        transport_entries = await repository.find_by_category(
            SpendingCategory.TRANSPORTATION
        )

        assert len(food_entries) == 1
        assert len(transport_entries) == 1
        assert food_entries[0].category == SpendingCategory.FOOD_DINING
        assert transport_entries[0].category == SpendingCategory.TRANSPORTATION

    async def test_find_by_date_range(self, repository):
        """Test finding entries by date range."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        # Create entry
        entry = SpendingEntry.create(
            merchant="Test Merchant",
            amount=Money.from_float(20.0, Currency.USD),
            category=SpendingCategory.FOOD_DINING,
            description="Test transaction",
        )
        await repository.save(entry)

        # Find in range (should include entry)
        entries_in_range = await repository.find_by_date_range(yesterday, tomorrow)
        assert len(entries_in_range) == 1

        # Find outside range (should be empty)
        future_start = now + timedelta(days=2)
        future_end = now + timedelta(days=3)
        entries_outside = await repository.find_by_date_range(future_start, future_end)
        assert len(entries_outside) == 0

    async def test_count_operations(self, repository):
        """Test counting operations."""
        # Initially empty
        total_count = await repository.count_total()
        assert total_count == 0

        # Add entries
        for i in range(3):
            entry = SpendingEntry.create(
                merchant=f"Merchant {i}",
                amount=Money.from_float(10.0, Currency.USD),
                category=SpendingCategory.FOOD_DINING
                if i < 2
                else SpendingCategory.TRANSPORTATION,
                description=f"Count test transaction {i}",
            )
            await repository.save(entry)

        # Count total
        total_count = await repository.count_total()
        assert total_count == 3

        # Count by category
        food_count = await repository.count_by_category(SpendingCategory.FOOD_DINING)
        transport_count = await repository.count_by_category(
            SpendingCategory.TRANSPORTATION
        )

        assert food_count == 2
        assert transport_count == 1

    async def test_delete_operations(self, repository, sample_entry):
        """Test delete operations."""
        # Save entry
        await repository.save(sample_entry)

        # Verify it exists
        assert await repository.exists(sample_entry.id)

        # Delete it
        deleted = await repository.delete(sample_entry.id)
        assert deleted is True

        # Verify it's gone
        assert not await repository.exists(sample_entry.id)
        retrieved = await repository.find_by_id(sample_entry.id)
        assert retrieved is None

        # Try to delete non-existent entry
        deleted_again = await repository.delete(sample_entry.id)
        assert deleted_again is False

    async def test_update_operations(self, repository, sample_entry):
        """Test updating entries."""
        # Save original entry
        await repository.save(sample_entry)

        # Update the entry
        updated_entry = sample_entry.update_amount(Money.from_float(50.0, Currency.USD))
        await repository.save(updated_entry)

        # Retrieve and verify update
        retrieved = await repository.find_by_id(sample_entry.id)
        assert retrieved is not None
        assert retrieved.amount.amount == Decimal("50.0")

    async def test_repository_lifecycle(self):
        """Test repository initialization and cleanup."""
        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()

        repo = SqliteSpendingRepository(f"sqlite:///{temp_db.name}")

        # Should not be initialized yet
        assert repo._connection is None

        # Initialize
        await repo.initialize()
        assert repo._connection is not None

        # Close
        await repo.close()
        # Connection should be closed but reference might still exist

    async def test_error_handling(self, repository):
        """Test error handling for invalid operations."""
        from ai_service.domain.entities.spending_entry import SpendingEntryId

        # Try to find non-existent entry
        non_existent_id = SpendingEntryId.generate()
        result = await repository.find_by_id(non_existent_id)
        assert result is None

        # Try to delete non-existent entry
        deleted = await repository.delete(non_existent_id)
        assert deleted is False

        # Check exists for non-existent entry
        exists = await repository.exists(non_existent_id)
        assert exists is False

    async def test_concurrent_operations(self, repository):
        """Test concurrent database operations."""
        import asyncio

        # Create multiple entries concurrently
        async def create_entry(i):
            entry = SpendingEntry.create(
                merchant=f"Concurrent Merchant {i}",
                amount=Money.from_float(10.0 + i, Currency.USD),
                category=SpendingCategory.FOOD_DINING,
                description=f"Concurrent transaction {i}",
            )
            await repository.save(entry)
            return entry

        # Create 5 entries concurrently
        tasks = [create_entry(i) for i in range(5)]
        await asyncio.gather(*tasks)

        # Verify all were created
        all_entries = await repository.find_all()
        assert len(all_entries) == 5

        # Verify all IDs are unique
        ids = [entry.id for entry in all_entries]
        assert len(set(ids)) == 5
