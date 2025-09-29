"""Repository interface for spending entries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from ..entities.spending_entry import SpendingEntry, SpendingEntryId
    from ..value_objects.spending_category import SpendingCategory


class SpendingRepository(ABC):
    """
    Repository interface for spending entry persistence.

    This interface defines the contract for storing and retrieving
    spending entries without coupling the domain to specific storage
    implementations.
    """

    @abstractmethod
    async def save(self, entry: SpendingEntry) -> None:
        """
        Save a spending entry.

        Args:
            entry: The spending entry to save

        Raises:
            RepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    async def find_by_id(self, entry_id: SpendingEntryId) -> SpendingEntry | None:
        """
        Find a spending entry by its ID.

        Args:
            entry_id: The unique identifier

        Returns:
            The spending entry if found, None otherwise

        Raises:
            RepositoryError: If query operation fails
        """
        pass

    @abstractmethod
    async def find_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> list[SpendingEntry]:
        """
        Find all spending entries with pagination.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of spending entries

        Raises:
            RepositoryError: If query operation fails
        """
        pass

    @abstractmethod
    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> list[SpendingEntry]:
        """
        Find spending entries within a date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of spending entries within date range

        Raises:
            RepositoryError: If query operation fails
        """
        pass

    @abstractmethod
    async def find_by_category(
        self,
        category: SpendingCategory,
        limit: int = 100,
        offset: int = 0
    ) -> list[SpendingEntry]:
        """
        Find spending entries by category.

        Args:
            category: The spending category to filter by
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of spending entries in the category

        Raises:
            RepositoryError: If query operation fails
        """
        pass

    @abstractmethod
    async def find_by_merchant(
        self,
        merchant: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[SpendingEntry]:
        """
        Find spending entries by merchant name.

        Args:
            merchant: The merchant name to search for
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of spending entries from the merchant

        Raises:
            RepositoryError: If query operation fails
        """
        pass

    @abstractmethod
    async def search_by_text(
        self,
        search_text: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[SpendingEntry]:
        """
        Search spending entries by text in merchant or description.

        Args:
            search_text: Text to search for
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of matching spending entries

        Raises:
            RepositoryError: If search operation fails
        """
        pass

    @abstractmethod
    async def count_total(self) -> int:
        """
        Get total count of spending entries.

        Returns:
            Total number of spending entries

        Raises:
            RepositoryError: If count operation fails
        """
        pass

    @abstractmethod
    async def count_by_category(self, category: SpendingCategory) -> int:
        """
        Get count of spending entries by category.

        Args:
            category: The spending category

        Returns:
            Number of entries in the category

        Raises:
            RepositoryError: If count operation fails
        """
        pass

    @abstractmethod
    async def delete(self, entry_id: SpendingEntryId) -> bool:
        """
        Delete a spending entry.

        Args:
            entry_id: The unique identifier of entry to delete

        Returns:
            True if entry was deleted, False if not found

        Raises:
            RepositoryError: If delete operation fails
        """
        pass

    @abstractmethod
    async def exists(self, entry_id: SpendingEntryId) -> bool:
        """
        Check if a spending entry exists.

        Args:
            entry_id: The unique identifier to check

        Returns:
            True if entry exists, False otherwise

        Raises:
            RepositoryError: If check operation fails
        """
        pass
