import aiosqlite
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import json

from config.settings import settings


@dataclass
class ConversationRecord:
    id: str
    user_id: str
    user_message: str
    assistant_message: str
    skill_used: Optional[str]
    timestamp: datetime
    tokens_input: int
    tokens_output: int
    metadata: Dict[str, Any] = None


class ConversationMemory:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or settings.DATABASE_URL
        self.db_path = self.db_url.replace("sqlite+aiosqlite:///", "")
        self._initialized = False

    async def initialize(self):
        if not self._initialized:
            await self._create_tables()
            self._initialized = True

    async def _create_tables(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_message TEXT NOT NULL,
                    skill_used TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    tokens_input INTEGER DEFAULT 0,
                    tokens_output INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    hashed_password TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            await db.commit()

    async def save_conversation(
        self,
        conversation_id: str,
        user_id: str,
        user_message: str,
        assistant_message: str,
        skill_used: Optional[str] = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        await self.initialize()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO conversations 
                (id, user_id, user_message, assistant_message, skill_used, tokens_input, tokens_output, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation_id,
                user_id,
                user_message,
                assistant_message,
                skill_used,
                tokens_input,
                tokens_output,
                metadata_json,
            ))
            await db.commit()

    async def get_conversation(self, conversation_id: str) -> Optional[ConversationRecord]:
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                return ConversationRecord(
                    id=row["id"],
                    user_id=row["user_id"],
                    user_message=row["user_message"],
                    assistant_message=row["assistant_message"],
                    skill_used=row["skill_used"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    tokens_input=row["tokens_input"],
                    tokens_output=row["tokens_output"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                )

    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ConversationRecord]:
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM conversations 
                   WHERE user_id = ? 
                   ORDER BY timestamp DESC 
                   LIMIT ? OFFSET ?""",
                (user_id, limit, offset),
            ) as cursor:
                rows = await cursor.fetchall()
                
                return [
                    ConversationRecord(
                        id=row["id"],
                        user_id=row["user_id"],
                        user_message=row["user_message"],
                        assistant_message=row["assistant_message"],
                        skill_used=row["skill_used"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        tokens_input=row["tokens_input"],
                        tokens_output=row["tokens_output"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                    )
                    for row in rows
                ]

    async def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """SELECT 
                    COUNT(*) as total_conversations,
                    SUM(tokens_input) as total_input_tokens,
                    SUM(tokens_output) as total_output_tokens,
                    MAX(timestamp) as last_conversation
                   FROM conversations 
                   WHERE user_id = ?""",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
                
                return {
                    "total_conversations": row[0] or 0,
                    "total_input_tokens": row[1] or 0,
                    "total_output_tokens": row[2] or 0,
                    "total_tokens": (row[1] or 0) + (row[2] or 0),
                    "last_conversation": row[3],
                }

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def clear_user_history(self, user_id: str) -> int:
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM conversations WHERE user_id = ?", (user_id,)
            )
            await db.commit()
            return cursor.rowcount
