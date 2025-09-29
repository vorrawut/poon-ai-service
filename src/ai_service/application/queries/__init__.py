"""Query handlers for CQRS pattern."""

from .base import Query, QueryHandler
from .spending_queries import (
    AnalyzeSpendingPatternsQuery,
    AnalyzeSpendingPatternsQueryHandler,
    GetSpendingEntriesQuery,
    GetSpendingEntriesQueryHandler,
    GetSpendingEntryQuery,
    GetSpendingEntryQueryHandler,
    GetSpendingStatisticsQuery,
    GetSpendingStatisticsQueryHandler,
    SearchSpendingEntriesQuery,
    SearchSpendingEntriesQueryHandler,
)

__all__ = [
    "AnalyzeSpendingPatternsQuery",
    "AnalyzeSpendingPatternsQueryHandler",
    "GetSpendingEntriesQuery",
    "GetSpendingEntriesQueryHandler",
    "GetSpendingEntryQuery",
    "GetSpendingEntryQueryHandler",
    "GetSpendingStatisticsQuery",
    "GetSpendingStatisticsQueryHandler",
    "Query",
    "QueryHandler",
    "SearchSpendingEntriesQuery",
    "SearchSpendingEntriesQueryHandler",
]
