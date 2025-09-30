"""Base classes for CQRS queries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

# Type variables for query and result
TQuery = TypeVar("TQuery", bound="Query")
TResult = TypeVar("TResult")


@dataclass(frozen=True)
class Query(ABC):
    """
    Base class for all queries in the CQRS pattern.

    Queries represent requests for data from the system.
    They should be immutable and contain all the data needed
    to perform the query.
    """

    @abstractmethod
    def validate(self) -> None:
        """
        Validate query parameters.

        Raises:
            ValidationError: If query parameters are invalid
        """


class QueryHandler(ABC, Generic[TQuery, TResult]):
    """
    Base class for query handlers.

    Query handlers contain the logic for retrieving and
    formatting data in response to queries.
    """

    @abstractmethod
    async def handle(self, query: TQuery) -> TResult:
        """
        Handle a query and return a result.

        Args:
            query: The query to handle

        Returns:
            The result of handling the query

        Raises:
            QueryHandlerError: If query handling fails
        """
        pass


@dataclass(frozen=True)
class QueryResult:
    """Result of executing a query."""

    success: bool
    data: Any = None
    message: str | None = None
    errors: list[str] | None = None
    total_count: int | None = None

    @property
    def error(self) -> str | None:
        """Get the first error message if any."""
        if self.errors and len(self.errors) > 0:
            return self.errors[0]
        return self.message if not self.success else None

    @classmethod
    def success_result(
        cls,
        data: Any = None,
        message: str | None = None,
        total_count: int | None = None,
    ) -> QueryResult:
        """Create a successful query result."""
        return cls(success=True, data=data, message=message, total_count=total_count)

    @classmethod
    def failure_result(
        cls, message: str | None = None, errors: list[str] | None = None
    ) -> QueryResult:
        """Create a failed query result."""
        return cls(success=False, message=message, errors=errors)

    def is_success(self) -> bool:
        """Check if the query was successful."""
        return self.success

    def is_failure(self) -> bool:
        """Check if the query failed."""
        return not self.success
