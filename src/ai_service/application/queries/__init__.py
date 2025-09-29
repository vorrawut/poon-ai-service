"""Query handlers for CQRS pattern."""

from .base import Query, QueryHandler, QueryResult
from .spending_queries import (
    GetSpendingEntriesQuery,
    GetSpendingEntriesQueryHandler,
    GetSpendingEntryByIdQuery,
    GetSpendingEntryByIdQueryHandler,
)

__all__ = [
    "Query",
    "QueryHandler",
    "QueryResult",
    "GetSpendingEntryByIdQuery",
    "GetSpendingEntryByIdQueryHandler",
    "GetSpendingEntriesQuery",
    "GetSpendingEntriesQueryHandler",
]
