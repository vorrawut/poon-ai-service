"""Query handlers for CQRS pattern."""

from .base import Query, QueryHandler, QueryResult
from .spending_queries import (
    GetSpendingEntriesQuery,
    GetSpendingEntriesQueryHandler,
    GetSpendingEntryByIdQuery,
    GetSpendingEntryByIdQueryHandler,
)

__all__ = [
    "GetSpendingEntriesQuery",
    "GetSpendingEntriesQueryHandler",
    "GetSpendingEntryByIdQuery",
    "GetSpendingEntryByIdQueryHandler",
    "Query",
    "QueryHandler",
    "QueryResult",
]
