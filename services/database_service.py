"""
Database Service for storing processed spending entries
Handles database operations for the AI-processed spending data
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import sqlite3
import aiosqlite
from pathlib import Path
from models.spending_models import SpendingEntry, NLPResult, OCRResult

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for storing spending entries"""
    
    def __init__(self, db_path: str = "ai_spending.db"):
        self.db_path = db_path
        self.initialized = False
    
    async def initialize(self):
        """Initialize database and create tables"""
        try:
            # Ensure directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            async with aiosqlite.connect(self.db_path) as db:
                # Create spending_entries table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS spending_entries (
                        id TEXT PRIMARY KEY,
                        amount REAL NOT NULL,
                        merchant TEXT NOT NULL,
                        category TEXT NOT NULL,
                        subcategory TEXT,
                        description TEXT NOT NULL,
                        date TEXT NOT NULL,
                        payment_method TEXT,
                        location TEXT,
                        tags TEXT,
                        confidence REAL NOT NULL,
                        processing_method TEXT NOT NULL,
                        raw_text TEXT,
                        metadata TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # Create processing_logs table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS processing_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entry_id TEXT,
                        processing_step TEXT NOT NULL,
                        method TEXT NOT NULL,
                        confidence REAL,
                        processing_time REAL,
                        raw_data TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (entry_id) REFERENCES spending_entries (id)
                    )
                """)
                
                # Create indexes for better performance
                await db.execute("CREATE INDEX IF NOT EXISTS idx_spending_date ON spending_entries(date)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_spending_category ON spending_entries(category)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_spending_merchant ON spending_entries(merchant)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_processing_logs_entry ON processing_logs(entry_id)")
                
                await db.commit()
                
            self.initialized = True
            logger.info("✅ Database service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    async def store_spending_entry(self, entry: SpendingEntry) -> bool:
        """Store a spending entry in the database"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                # Convert entry to database format
                entry_data = self._spending_entry_to_dict(entry)
                
                await db.execute("""
                    INSERT OR REPLACE INTO spending_entries (
                        id, amount, merchant, category, subcategory, description,
                        date, payment_method, location, tags, confidence,
                        processing_method, raw_text, metadata, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry_data['id'],
                    entry_data['amount'],
                    entry_data['merchant'],
                    entry_data['category'],
                    entry_data['subcategory'],
                    entry_data['description'],
                    entry_data['date'],
                    entry_data['payment_method'],
                    entry_data['location'],
                    json.dumps(entry_data['tags']),
                    entry_data['confidence'],
                    entry_data['processing_method'],
                    entry_data['raw_text'],
                    json.dumps(entry_data['metadata']),
                    entry_data['created_at'],
                    datetime.utcnow().isoformat()
                ))
                
                await db.commit()
                
            logger.info(f"✅ Stored spending entry: {entry.merchant} - ฿{entry.amount}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store spending entry: {e}")
            return False
    
    async def get_spending_entries(
        self, 
        limit: int = 100,
        offset: int = 0,
        category: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve spending entries with filtering"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Build query
            query = "SELECT * FROM spending_entries WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if date_from:
                query += " AND date >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND date <= ?"
                params.append(date_to)
            
            query += " ORDER BY date DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    
                    entries = []
                    for row in rows:
                        entry = dict(row)
                        # Parse JSON fields
                        entry['tags'] = json.loads(entry['tags']) if entry['tags'] else []
                        entry['metadata'] = json.loads(entry['metadata']) if entry['metadata'] else {}
                        entries.append(entry)
                    
                    return entries
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve spending entries: {e}")
            return []
    
    async def get_spending_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific spending entry by ID"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM spending_entries WHERE id = ?", 
                    (entry_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        entry = dict(row)
                        entry['tags'] = json.loads(entry['tags']) if entry['tags'] else []
                        entry['metadata'] = json.loads(entry['metadata']) if entry['metadata'] else {}
                        return entry
                    
                    return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get spending entry {entry_id}: {e}")
            return None
    
    async def update_spending_entry(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update a spending entry"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Build update query
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                if key in ['tags', 'metadata']:
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ?")
                params.append(value)
            
            if not set_clauses:
                return False
            
            # Add updated_at
            set_clauses.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(entry_id)
            
            query = f"UPDATE spending_entries SET {', '.join(set_clauses)} WHERE id = ?"
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(query, params)
                await db.commit()
                
            logger.info(f"✅ Updated spending entry: {entry_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update spending entry {entry_id}: {e}")
            return False
    
    async def delete_spending_entry(self, entry_id: str) -> bool:
        """Delete a spending entry"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                # Delete processing logs first
                await db.execute("DELETE FROM processing_logs WHERE entry_id = ?", (entry_id,))
                
                # Delete the entry
                cursor = await db.execute("DELETE FROM spending_entries WHERE id = ?", (entry_id,))
                await db.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ Deleted spending entry: {entry_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Spending entry not found: {entry_id}")
                    return False
            
        except Exception as e:
            logger.error(f"❌ Failed to delete spending entry {entry_id}: {e}")
            return False
    
    async def log_processing_step(
        self,
        entry_id: str,
        step: str,
        method: str,
        confidence: Optional[float] = None,
        processing_time: Optional[float] = None,
        raw_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log a processing step for debugging and analysis"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO processing_logs (
                        entry_id, processing_step, method, confidence,
                        processing_time, raw_data, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry_id,
                    step,
                    method,
                    confidence,
                    processing_time,
                    json.dumps(raw_data) if raw_data else None,
                    datetime.utcnow().isoformat()
                ))
                
                await db.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log processing step: {e}")
            return False
    
    async def get_processing_logs(self, entry_id: str) -> List[Dict[str, Any]]:
        """Get processing logs for an entry"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM processing_logs WHERE entry_id = ? ORDER BY created_at",
                    (entry_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    
                    logs = []
                    for row in rows:
                        log = dict(row)
                        if log['raw_data']:
                            log['raw_data'] = json.loads(log['raw_data'])
                        logs.append(log)
                    
                    return logs
            
        except Exception as e:
            logger.error(f"❌ Failed to get processing logs: {e}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            if not self.initialized:
                await self.initialize()
            
            async with aiosqlite.connect(self.db_path) as db:
                # Total entries
                async with db.execute("SELECT COUNT(*) FROM spending_entries") as cursor:
                    total_entries = (await cursor.fetchone())[0]
                
                # Total amount
                async with db.execute("SELECT SUM(amount) FROM spending_entries") as cursor:
                    total_amount = (await cursor.fetchone())[0] or 0
                
                # Average confidence
                async with db.execute("SELECT AVG(confidence) FROM spending_entries") as cursor:
                    avg_confidence = (await cursor.fetchone())[0] or 0
                
                # Category breakdown
                async with db.execute("""
                    SELECT category, COUNT(*), SUM(amount) 
                    FROM spending_entries 
                    GROUP BY category
                """) as cursor:
                    category_stats = {}
                    async for row in cursor:
                        category_stats[row[0]] = {
                            'count': row[1],
                            'total_amount': row[2]
                        }
                
                # Processing method breakdown
                async with db.execute("""
                    SELECT processing_method, COUNT(*) 
                    FROM spending_entries 
                    GROUP BY processing_method
                """) as cursor:
                    method_stats = {}
                    async for row in cursor:
                        method_stats[row[0]] = row[1]
                
                return {
                    'total_entries': total_entries,
                    'total_amount': total_amount,
                    'average_confidence': round(avg_confidence, 3),
                    'category_breakdown': category_stats,
                    'method_breakdown': method_stats,
                    'last_updated': datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {}
    
    def _spending_entry_to_dict(self, entry: SpendingEntry) -> Dict[str, Any]:
        """Convert SpendingEntry to dictionary for database storage"""
        return {
            'id': entry.id or f"entry_{int(datetime.utcnow().timestamp() * 1000)}",
            'amount': entry.amount,
            'merchant': entry.merchant,
            'category': entry.category,
            'subcategory': entry.subcategory,
            'description': entry.description,
            'date': entry.date.isoformat() if isinstance(entry.date, datetime) else entry.date,
            'payment_method': entry.payment_method,
            'location': entry.location,
            'tags': entry.tags,
            'confidence': entry.confidence,
            'processing_method': entry.processing_method,
            'raw_text': entry.raw_text,
            'metadata': entry.metadata,
            'created_at': entry.created_at.isoformat() if isinstance(entry.created_at, datetime) else entry.created_at
        }
    
    async def close(self):
        """Close database connections"""
        # SQLite connections are closed automatically
        logger.info("📊 Database service closed")

# Global database service instance
database_service = DatabaseService()
