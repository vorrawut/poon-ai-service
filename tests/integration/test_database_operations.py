"""Integration tests for database operations."""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ai_service.domain.entities.spending_entry import SpendingEntry, SpendingEntryId
from ai_service.domain.value_objects.confidence import ConfidenceScore
from ai_service.domain.value_objects.money import Currency, Money
from ai_service.domain.value_objects.processing_method import ProcessingMethod
from ai_service.domain.value_objects.spending_category import (
    PaymentMethod,
    SpendingCategory,
)
from ai_service.infrastructure.database.sqlite_repository import (
    SqliteSpendingRepository,
)


@pytest.mark.integration
class TestSqliteSpendingRepository:
    """Integration tests for SQLite spending repository."""

    @pytest.fixture
    async def repository(self):
        """Create a test repository with temporary database."""
        # Create a temporary database file
        temp_fd, temp_path = tempfile.mkstemp(suffix=".db")
        os.close(temp_fd)  # Close the file descriptor

        try:
            repository = SqliteSpendingRepository(f"sqlite:///{temp_path}")
            await repository.initialize()
            yield repository
        finally:
            await repository.close()
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.fixture
    def sample_entry(self):
        """Create a sample spending entry."""
        return SpendingEntry(
            amount=Money.from_float(120.50, Currency.THB),
            merchant="Integration Test Cafe",
            description="Coffee and pastry for testing",
            transaction_date=datetime(2024, 1, 15, 10, 30, 0),
            category=SpendingCategory.FOOD_DINING,
            payment_method=PaymentMethod.CREDIT_CARD,
            confidence=ConfidenceScore.high(),
            processing_method=ProcessingMethod.MANUAL_ENTRY,
            tags=["test", "integration"],
            location="Bangkok, Thailand",
        )

    async def test_save_and_find_by_id(self, repository, sample_entry):
        """Test saving and retrieving an entry by ID."""
        # Save the entry
        await repository.save(sample_entry)

        # Retrieve the entry
        retrieved = await repository.find_by_id(sample_entry.id)

        assert retrieved is not None
        assert retrieved.id == sample_entry.id
        assert retrieved.amount.to_float() == 120.50
        assert retrieved.merchant == "Integration Test Cafe"
        assert retrieved.description == "Coffee and pastry for testing"
        assert retrieved.category == SpendingCategory.FOOD_DINING
        assert retrieved.payment_method == PaymentMethod.CREDIT_CARD
        assert retrieved.tags == ["test", "integration"]
        assert retrieved.location == "Bangkok, Thailand"

    async def test_save_duplicate_id_updates(self, repository, sample_entry):
        """Test that saving an entry with existing ID updates it."""
        # Save the entry
        await repository.save(sample_entry)

        # Update the entry
        sample_entry.update_merchant("Updated Cafe")
        sample_entry.update_amount(Money.from_float(200.0, Currency.THB))

        # Save again
        await repository.save(sample_entry)

        # Retrieve and verify update
        retrieved = await repository.find_by_id(sample_entry.id)
        assert retrieved.merchant == "Updated Cafe"
        assert retrieved.amount.to_float() == 200.0

    async def test_find_by_id_not_found(self, repository):
        """Test finding a non-existent entry."""
        non_existent_id = SpendingEntryId()
        result = await repository.find_by_id(non_existent_id)
        assert result is None

    async def test_find_all_empty(self, repository):
        """Test finding all entries when repository is empty."""
        entries = await repository.find_all()
        assert entries == []

    async def test_find_all_with_entries(self, repository):
        """Test finding all entries."""
        # Create and save multiple entries
        entries = []
        for i in range(3):
            entry = SpendingEntry(
                amount=Money.from_float(100.0 + i * 10, Currency.THB),
                merchant=f"Cafe {i}",
                description=f"Transaction {i}",
                transaction_date=datetime(2024, 1, 15 + i),
                category=SpendingCategory.FOOD_DINING,
                payment_method=PaymentMethod.CREDIT_CARD,
                confidence=ConfidenceScore.high(),
                processing_method=ProcessingMethod.MANUAL_ENTRY,
            )
            entries.append(entry)
            await repository.save(entry)

        # Retrieve all entries
        retrieved = await repository.find_all()

        assert len(retrieved) == 3
        # Check that all saved entries are retrieved (order might vary)
        retrieved_ids = {entry.id for entry in retrieved}
        saved_ids = {entry.id for entry in entries}
        assert retrieved_ids == saved_ids

    async def test_find_all_with_limit(self, repository):
        """Test finding entries with limit."""
        # Create and save multiple entries
        for i in range(5):
            entry = SpendingEntry(
                amount=Money.from_float(100.0 + i * 10, Currency.THB),
                merchant=f"Cafe {i}",
                description=f"Transaction {i}",
                transaction_date=datetime(2024, 1, 15 + i),
                category=SpendingCategory.FOOD_DINING,
                payment_method=PaymentMethod.CREDIT_CARD,
                confidence=ConfidenceScore.high(),
                processing_method=ProcessingMethod.MANUAL_ENTRY,
            )
            await repository.save(entry)

        # Retrieve with limit
        retrieved = await repository.find_all(limit=3)
        assert len(retrieved) == 3

    async def test_find_all_with_offset(self, repository):
        """Test finding entries with offset."""
        # Create and save multiple entries
        entries = []
        for i in range(5):
            entry = SpendingEntry(
                amount=Money.from_float(100.0 + i * 10, Currency.THB),
                merchant=f"Cafe {i}",
                description=f"Transaction {i}",
                transaction_date=datetime(2024, 1, 15 + i),
                category=SpendingCategory.FOOD_DINING,
                payment_method=PaymentMethod.CREDIT_CARD,
                confidence=ConfidenceScore.high(),
                processing_method=ProcessingMethod.MANUAL_ENTRY,
            )
            entries.append(entry)
            await repository.save(entry)

        # Retrieve with offset
        retrieved = await repository.find_all(offset=2, limit=2)
        assert len(retrieved) == 2

    async def test_find_by_category(self, repository):
        """Test finding entries by category."""
        # Create entries with different categories
        food_entry = SpendingEntry(
            amount=Money.from_float(100.0, Currency.THB),
            merchant="Restaurant",
            description="Dinner",
            transaction_date=datetime(2024, 1, 15),
            category=SpendingCategory.FOOD_DINING,
            payment_method=PaymentMethod.CREDIT_CARD,
            confidence=ConfidenceScore.high(),
            processing_method=ProcessingMethod.MANUAL_ENTRY,
        )

        transport_entry = SpendingEntry(
            amount=Money.from_float(50.0, Currency.THB),
            merchant="Taxi Service",
            description="Ride home",
            transaction_date=datetime(2024, 1, 16),
            category=SpendingCategory.TRANSPORTATION,
            payment_method=PaymentMethod.CASH,
            confidence=ConfidenceScore.medium(),
            processing_method=ProcessingMethod.MANUAL_ENTRY,
        )

        await repository.save(food_entry)
        await repository.save(transport_entry)

        # Find food entries
        food_entries = await repository.find_by_category(SpendingCategory.FOOD_DINING)
        assert len(food_entries) == 1
        assert food_entries[0].category == SpendingCategory.FOOD_DINING

        # Find transport entries
        transport_entries = await repository.find_by_category(
            SpendingCategory.TRANSPORTATION
        )
        assert len(transport_entries) == 1
        assert transport_entries[0].category == SpendingCategory.TRANSPORTATION

    async def test_find_by_date_range(self, repository):
        """Test finding entries by date range."""
        # Create entries with different dates
        old_entry = SpendingEntry(
            amount=Money.from_float(100.0, Currency.THB),
            merchant="Old Cafe",
            description="Old transaction",
            transaction_date=datetime(2024, 1, 1),
            category=SpendingCategory.FOOD_DINING,
            payment_method=PaymentMethod.CREDIT_CARD,
            confidence=ConfidenceScore.high(),
            processing_method=ProcessingMethod.MANUAL_ENTRY,
        )

        recent_entry = SpendingEntry(
            amount=Money.from_float(150.0, Currency.THB),
            merchant="Recent Cafe",
            description="Recent transaction",
            transaction_date=datetime(2024, 1, 15),
            category=SpendingCategory.FOOD_DINING,
            payment_method=PaymentMethod.CREDIT_CARD,
            confidence=ConfidenceScore.high(),
            processing_method=ProcessingMethod.MANUAL_ENTRY,
        )

        await repository.save(old_entry)
        await repository.save(recent_entry)

        # Find entries in January 2024
        jan_start = datetime(2024, 1, 10)
        jan_end = datetime(2024, 1, 20)
        jan_entries = await repository.find_by_date_range(jan_start, jan_end)

        assert len(jan_entries) == 1
        assert jan_entries[0].merchant == "Recent Cafe"

    async def test_count_total(self, repository):
        """Test counting total entries."""
        # Initially should be 0
        count = await repository.count_total()
        assert count == 0

        # Add some entries
        for i in range(3):
            entry = SpendingEntry(
                amount=Money.from_float(100.0, Currency.THB),
                merchant=f"Cafe {i}",
                description=f"Transaction {i}",
                transaction_date=datetime(2024, 1, 15 + i),
                category=SpendingCategory.FOOD_DINING,
                payment_method=PaymentMethod.CREDIT_CARD,
                confidence=ConfidenceScore.high(),
                processing_method=ProcessingMethod.MANUAL_ENTRY,
            )
            await repository.save(entry)

        # Should now be 3
        count = await repository.count_total()
        assert count == 3

    async def test_count_by_category(self, repository):
        """Test counting entries by category."""
        # Create entries with different categories
        for i in range(2):
            food_entry = SpendingEntry(
                amount=Money.from_float(100.0, Currency.THB),
                merchant=f"Restaurant {i}",
                description=f"Meal {i}",
                transaction_date=datetime(2024, 1, 15 + i),
                category=SpendingCategory.FOOD_DINING,
                payment_method=PaymentMethod.CREDIT_CARD,
                confidence=ConfidenceScore.high(),
                processing_method=ProcessingMethod.MANUAL_ENTRY,
            )
            await repository.save(food_entry)

        transport_entry = SpendingEntry(
            amount=Money.from_float(50.0, Currency.THB),
            merchant="Taxi",
            description="Ride",
            transaction_date=datetime(2024, 1, 17),
            category=SpendingCategory.TRANSPORTATION,
            payment_method=PaymentMethod.CASH,
            confidence=ConfidenceScore.medium(),
            processing_method=ProcessingMethod.MANUAL_ENTRY,
        )
        await repository.save(transport_entry)

        # Count by category
        food_count = await repository.count_by_category(SpendingCategory.FOOD_DINING)
        transport_count = await repository.count_by_category(
            SpendingCategory.TRANSPORTATION
        )

        assert food_count == 2
        assert transport_count == 1

    async def test_delete_entry(self, repository, sample_entry):
        """Test deleting an entry."""
        # Save the entry
        await repository.save(sample_entry)

        # Verify it exists
        retrieved = await repository.find_by_id(sample_entry.id)
        assert retrieved is not None

        # Delete the entry
        deleted = await repository.delete(sample_entry.id)
        assert deleted is True

        # Verify it's gone
        retrieved = await repository.find_by_id(sample_entry.id)
        assert retrieved is None

    async def test_delete_non_existent_entry(self, repository):
        """Test deleting a non-existent entry."""
        non_existent_id = SpendingEntryId()
        deleted = await repository.delete(non_existent_id)
        assert deleted is False

    async def test_exists_entry(self, repository, sample_entry):
        """Test checking if entry exists."""
        # Initially should not exist
        exists = await repository.exists(sample_entry.id)
        assert exists is False

        # Save the entry
        await repository.save(sample_entry)

        # Should now exist
        exists = await repository.exists(sample_entry.id)
        assert exists is True

    async def test_repository_initialization(self):
        """Test repository initialization."""
        temp_fd, temp_path = tempfile.mkstemp(suffix=".db")
        os.close(temp_fd)

        try:
            repository = SqliteSpendingRepository(f"sqlite:///{temp_path}")

            # Should initialize successfully
            await repository.initialize()

            # Should be able to perform operations
            count = await repository.count_total()
            assert count == 0

            await repository.close()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def test_repository_close(self, repository):
        """Test repository close operation."""
        # Should be able to close without errors
        await repository.close()

        # After closing, operations might fail (implementation dependent)
        # This test mainly ensures close() doesn't raise exceptions
