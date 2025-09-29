"""SQLite implementation of spending repository."""

from __future__ import annotations

from datetime import datetime
import json

import aiosqlite
import structlog

from ...domain.entities.spending_entry import SpendingEntry, SpendingEntryId
from ...domain.repositories.spending_repository import SpendingRepository
from ...domain.value_objects.confidence import ConfidenceScore
from ...domain.value_objects.money import Currency, Money
from ...domain.value_objects.processing_method import ProcessingMethod
from ...domain.value_objects.spending_category import PaymentMethod, SpendingCategory

logger = structlog.get_logger(__name__)


class SqliteSpendingRepository(SpendingRepository):
    """SQLite implementation of the spending repository."""

    def __init__(self, database_url: str) -> None:
        """Initialize repository with database URL."""
        self.database_url = database_url.replace("sqlite:///", "")
        self._connection: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Initialize database connection and create tables."""
        self._connection = await aiosqlite.connect(self.database_url)
        self._connection.row_factory = aiosqlite.Row

        await self._create_tables()
        logger.info("SQLite repository initialized", database=self.database_url)

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("SQLite repository closed")

    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        if not self._connection:
            msg = "Database connection not initialized"
            raise RuntimeError(msg)

        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS spending_entries (
                id TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                merchant TEXT NOT NULL,
                description TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                payment_method TEXT NOT NULL,
                location TEXT,
                tags TEXT,
                confidence REAL NOT NULL,
                processing_method TEXT NOT NULL,
                raw_text TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_spending_entries_date
            ON spending_entries(transaction_date)
        """)

        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_spending_entries_category
            ON spending_entries(category)
        """)

        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_spending_entries_merchant
            ON spending_entries(merchant)
        """)

        await self._connection.commit()

    async def save(self, entry: SpendingEntry) -> None:
        """Save a spending entry."""
        if not self._connection:
            msg = "Database connection not initialized"
            raise RuntimeError(msg)

        try:
            await self._connection.execute("""
                INSERT OR REPLACE INTO spending_entries (
                    id, amount, currency, merchant, description, transaction_date,
                    category, subcategory, payment_method, location, tags,
                    confidence, processing_method, raw_text, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id.value,
                entry.amount.to_float(),
                entry.amount.currency.value,
                entry.merchant,
                entry.description,
                entry.transaction_date.isoformat(),
                entry.category.value,
                entry.subcategory,
                entry.payment_method.value,
                entry.location,
                json.dumps(entry.tags) if entry.tags else None,
                entry.confidence.value,
                entry.processing_method.value,
                entry.raw_text,
                entry.created_at.isoformat(),
                entry.updated_at.isoformat(),
            ))

            await self._connection.commit()
            logger.debug("Spending entry saved", entry_id=entry.id.value)

        except Exception as e:
            await self._connection.rollback()
            logger.error("Failed to save spending entry", entry_id=entry.id.value, error=str(e))
            raise

    async def find_by_id(self, entry_id: SpendingEntryId) -> SpendingEntry | None:
        """Find a spending entry by ID."""
        if not self._connection:
            msg = "Database connection not initialized"
            raise RuntimeError(msg)

        cursor = await self._connection.execute(
            "SELECT * FROM spending_entries WHERE id = ?",
            (entry_id.value,)
        )

        row = await cursor.fetchone()
        await cursor.close()

        return self._row_to_entry(row) if row else None

    async def find_all(self, limit: int = 100, offset: int = 0) -> list[SpendingEntry]:
        """Find all spending entries with pagination."""
        if not self._connection:
            msg = "Database connection not initialized"
            raise RuntimeError(msg)

        cursor = await self._connection.execute(
            "SELECT * FROM spending_entries ORDER BY transaction_date DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )

        rows = await cursor.fetchall()
        await cursor.close()

        return [self._row_to_entry(row) for row in rows]

    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> list[SpendingEntry]:
        """Find spending entries within a date range."""
        if not self._connection:
            msg = "Database connection not initialized"
            raise RuntimeError(msg)

        cursor = await self._connection.execute("""
            SELECT * FROM spending_entries
            WHERE transaction_date >= ? AND transaction_date <= ?
            ORDER BY transaction_date DESC
            LIMIT ? OFFSET ?
        """, (
            start_date.isoformat(),
            end_date.isoformat(),
            limit,
            offset
        ))

        rows = await cursor.fetchall()
        await cursor.close()

        return [self._row_to_entry(row) for row in rows]

    async def find_by_category(
        self,
        category: SpendingCategory,
        limit: int = 100,
        offset: int = 0
    ) -> list[SpendingEntry]:
        """Find spending entries by category."""
        if not self._connection:
            msg = "Database connection not initialized"
            raise RuntimeError(msg)

        cursor = await self._connection.execute("""
            SELECT * FROM spending_entries
            WHERE category = ?
            ORDER BY transaction_date DESC
            LIMIT ? OFFSET ?
        """, (category.value, limit, offset))

        rows = await cursor.fetchall()
        await cursor.close()

        return [self._row_to_entry(row) for row in rows]

    async def find_by_merchant(
        self,
        merchant: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[SpendingEntry]:
        """Find spending entries by merchant name."""
        if not self._connection:
            msg = "Database connection not initialized"
            raise RuntimeError(msg)

        cursor = await self._connection.execute("""
            SELECT * FROM spending_entries
            WHERE merchant LIKE ?
            ORDER BY transaction_date DESC
            LIMIT ? OFFSET ?
        """, (f"%{merchant}%", limit, offset))

        rows = await cursor.fetchall()
        await cursor.close()

        return [self._row_to_entry(row) for row in rows]

    async def search_by_text(
        self,
        search_text: str,
        limit: int = 100,
        offset: int = 0
    ) -> list[SpendingEntry]:
        """Search spending entries by text in merchant or description."""
        if not self._connection:
            msg = "Database connection not initialized"
            raise RuntimeError(msg)

        search_pattern = f"%{search_text}%"

        cursor = await self._connection.execute("""
            SELECT * FROM spending_entries
            WHERE merchant LIKE ? OR description LIKE ? OR raw_text LIKE ?
            ORDER BY transaction_date DESC
            LIMIT ? OFFSET ?
        """, (search_pattern, search_pattern, search_pattern, limit, offset))

        rows = await cursor.fetchall()
        await cursor.close()

        return [self._row_to_entry(row) for row in rows]

    async def count_total(self) -> int:
        """Get total count of spending entries."""
        if not self._connection:
            msg = "Database connection not initialized"
            raise RuntimeError(msg)

        cursor = await self._connection.execute("SELECT COUNT(*) FROM spending_entries")
        result = await cursor.fetchone()
        await cursor.close()

        return result[0] if result else 0

    async def count_by_category(self, category: SpendingCategory) -> int:
        """Get count of spending entries by category."""
        if not self._connection:
            msg = "Database connection not initialized"
            raise RuntimeError(msg)

        cursor = await self._connection.execute(
            "SELECT COUNT(*) FROM spending_entries WHERE category = ?",
            (category.value,)
        )
        result = await cursor.fetchone()
        await cursor.close()

        return result[0] if result else 0

    async def delete(self, entry_id: SpendingEntryId) -> bool:
        """Delete a spending entry."""
        if not self._connection:
            msg = "Database connection not initialized"
            raise RuntimeError(msg)

        cursor = await self._connection.execute(
            "DELETE FROM spending_entries WHERE id = ?",
            (entry_id.value,)
        )

        await self._connection.commit()
        deleted = cursor.rowcount > 0
        await cursor.close()

        if deleted:
            logger.debug("Spending entry deleted", entry_id=entry_id.value)

        return deleted

    async def exists(self, entry_id: SpendingEntryId) -> bool:
        """Check if a spending entry exists."""
        if not self._connection:
            msg = "Database connection not initialized"
            raise RuntimeError(msg)

        cursor = await self._connection.execute(
            "SELECT 1 FROM spending_entries WHERE id = ? LIMIT 1",
            (entry_id.value,)
        )

        result = await cursor.fetchone()
        await cursor.close()

        return result is not None

    def _row_to_entry(self, row: aiosqlite.Row) -> SpendingEntry:
        """Convert database row to SpendingEntry entity."""
        tags = json.loads(row['tags']) if row['tags'] else []

        return SpendingEntry(
            id=SpendingEntryId(row['id']),
            amount=Money.from_float(row['amount'], Currency(row['currency'])),
            merchant=row['merchant'],
            description=row['description'],
            transaction_date=datetime.fromisoformat(row['transaction_date']),
            category=SpendingCategory(row['category']),
            subcategory=row['subcategory'],
            payment_method=PaymentMethod(row['payment_method']),
            location=row['location'],
            tags=tags,
            confidence=ConfidenceScore(row['confidence']),
            processing_method=ProcessingMethod(row['processing_method']),
            raw_text=row['raw_text'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
        )
