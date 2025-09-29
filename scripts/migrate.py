#!/usr/bin/env python3
"""Database migration script for Poon AI Service."""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_service.core.config import get_settings
from ai_service.infrastructure.database.sqlite_repository import (
    SqliteSpendingRepository,
)


async def migrate():
    """Run database migrations."""
    try:
        settings = get_settings()
        repo = SqliteSpendingRepository(settings.get_database_url())
        await repo.initialize()
        print("✅ Database initialized successfully")
        await repo.close()
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(migrate())
    sys.exit(0 if success else 1)
