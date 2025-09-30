"""Spending-related queries for CQRS pattern."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from ...domain.entities.spending_entry import SpendingEntryId
from ...domain.repositories.spending_repository import SpendingRepository
from .base import Query, QueryHandler, QueryResult


@dataclass(frozen=True)
class GetSpendingEntryByIdQuery(Query):
    """Query to get a spending entry by its ID."""

    entry_id: str

    def validate(self) -> None:
        """Validate the query parameters."""
        if not self.entry_id:
            raise ValueError("Entry ID cannot be empty")

        try:
            uuid.UUID(self.entry_id)
        except ValueError as e:
            raise ValueError("Invalid entry ID format") from e


@dataclass(frozen=True)
class GetSpendingEntriesQuery(Query):
    """Query to get spending entries with optional filters."""

    limit: int = 10
    offset: int = 0
    category: str | None = None
    payment_method: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None

    def validate(self) -> None:
        """Validate the query parameters."""
        if self.limit <= 0:
            raise ValueError("Limit must be positive")

        if self.limit > 1000:
            raise ValueError("Limit cannot exceed 1000")

        if self.offset < 0:
            raise ValueError("Offset cannot be negative")

        if self.date_from and self.date_to and self.date_from >= self.date_to:
            raise ValueError("date_from must be before date_to")


class GetSpendingEntryByIdQueryHandler(
    QueryHandler[GetSpendingEntryByIdQuery, QueryResult]
):
    """Handler for GetSpendingEntryByIdQuery."""

    def __init__(self, repository: SpendingRepository) -> None:
        """Initialize the handler with repository."""
        self._repository = repository

    async def handle(self, query: GetSpendingEntryByIdQuery) -> QueryResult:
        """Handle the query."""
        try:
            # Validate the query
            query.validate()

            # Get the entry from repository
            entry_id = SpendingEntryId(query.entry_id)
            entry = await self._repository.find_by_id(entry_id)

            if entry is None:
                return QueryResult.failure_result(
                    message=f"Spending entry not found: {query.entry_id}"
                )

            return QueryResult.success_result(
                data=entry, message="Spending entry retrieved successfully"
            )

        except ValueError as e:
            return QueryResult.failure_result(message=str(e))
        except Exception as e:
            return QueryResult.failure_result(
                message=f"Failed to retrieve spending entry: {e!s}"
            )


class GetSpendingEntriesQueryHandler(
    QueryHandler[GetSpendingEntriesQuery, QueryResult]
):
    """Handler for GetSpendingEntriesQuery."""

    def __init__(self, repository: SpendingRepository) -> None:
        """Initialize the handler with repository."""
        self._repository = repository

    async def handle(self, query: GetSpendingEntriesQuery) -> QueryResult:
        """Handle the query."""
        try:
            # Validate the query
            query.validate()

            # Get entries from repository
            entries = await self._repository.find_all(
                limit=query.limit, offset=query.offset
            )

            # Get total count
            total_count = await self._repository.count_total()

            # Calculate has_more
            has_more = (query.offset + len(entries)) < total_count

            result_data = {
                "entries": entries,
                "total_count": total_count,
                "limit": query.limit,
                "offset": query.offset,
                "has_more": has_more,
            }

            return QueryResult.success_result(
                data=result_data, message=f"Retrieved {len(entries)} spending entries"
            )

        except ValueError as e:
            return QueryResult.failure_result(message=str(e))
        except Exception as e:
            return QueryResult.failure_result(
                message=f"Failed to retrieve spending entries: {e!s}"
            )
