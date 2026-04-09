"""Crew Session - Session management for multi-agent runs"""

import uuid
import json
import aiosqlite
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from config.settings import settings


@dataclass
class SessionRecord:
    """A record of a crew session"""
    session_id: str
    task: str
    started_at: str
    completed_at: Optional[str] = None
    status: str = "running"  # running, completed, failed, cancelled
    result: Optional[str] = None
    num_agents: int = 0
    num_subtasks: int = 0
    num_completed: int = 0
    num_failed: int = 0
    elapsed_seconds: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionRecord":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class CrewSession:
    """Manages crew session persistence and history"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "jarvis.db"
        self._current_session: Optional[SessionRecord] = None
        self._initialized = False

    async def initialize(self):
        """Initialize database tables"""
        if not self._initialized:
            await self._create_tables()
            self._initialized = True

    async def _create_tables(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS crew_sessions (
                    session_id TEXT PRIMARY KEY,
                    task TEXT NOT NULL,
                    started_at DATETIME NOT NULL,
                    completed_at DATETIME,
                    status TEXT NOT NULL DEFAULT 'running',
                    result TEXT,
                    num_agents INTEGER DEFAULT 0,
                    num_subtasks INTEGER DEFAULT 0,
                    num_completed INTEGER DEFAULT 0,
                    num_failed INTEGER DEFAULT 0,
                    elapsed_seconds REAL DEFAULT 0,
                    metadata TEXT
                )
            """)
            await db.commit()

    async def start_session(self, task: str, num_agents: int = 0) -> SessionRecord:
        """Start a new crew session"""
        await self.initialize()

        session = SessionRecord(
            session_id=str(uuid.uuid4()),
            task=task,
            started_at=datetime.now().isoformat(),
            num_agents=num_agents,
        )

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO crew_sessions
                (session_id, task, started_at, status, num_agents)
                VALUES (?, ?, ?, 'running', ?)
            """, (session.session_id, session.task, session.started_at, session.num_agents))
            await db.commit()

        self._current_session = session
        return session

    async def update_session(self, **kwargs):
        """Update current session"""
        if not self._current_session:
            return

        for key, value in kwargs.items():
            if hasattr(self._current_session, key):
                setattr(self._current_session, key, value)

        # Persist to database
        if self._current_session.status == "running":
            updates = ", ".join(f"{k} = ?" for k in kwargs.keys())
            values = list(kwargs.values())
        else:
            updates = ", ".join(f"{k} = ?" for k in kwargs.keys())
            values = list(kwargs.values())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE crew_sessions SET {updates} WHERE session_id = ?",
                values + [self._current_session.session_id]
            )
            await db.commit()

    async def complete_session(self, result: str, elapsed: float = 0,
                               num_subtasks: int = 0, num_completed: int = 0,
                               num_failed: int = 0):
        """Mark session as completed"""
        if self._current_session:
            await self.update_session(
                status="completed",
                completed_at=datetime.now().isoformat(),
                result=result,
                elapsed_seconds=elapsed,
                num_subtasks=num_subtasks,
                num_completed=num_completed,
                num_failed=num_failed,
            )

    async def fail_session(self, error: str, elapsed: float = 0):
        """Mark session as failed"""
        if self._current_session:
            await self.update_session(
                status="failed",
                completed_at=datetime.now().isoformat(),
                result=error,
                elapsed_seconds=elapsed,
            )

    async def get_session(self, session_id: str) -> Optional[SessionRecord]:
        """Get a session by ID"""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM crew_sessions WHERE session_id = ?", (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return SessionRecord(
                        session_id=row["session_id"],
                        task=row["task"],
                        started_at=row["started_at"],
                        completed_at=row["completed_at"],
                        status=row["status"],
                        result=row["result"],
                        num_agents=row["num_agents"],
                        num_subtasks=row["num_subtasks"],
                        num_completed=row["num_completed"],
                        num_failed=row["num_failed"],
                        elapsed_seconds=row["elapsed_seconds"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    )
        return None

    async def get_recent_sessions(self, limit: int = 10) -> List[SessionRecord]:
        """Get recent sessions"""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM crew_sessions ORDER BY started_at DESC LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    SessionRecord(
                        session_id=row["session_id"],
                        task=row["task"],
                        started_at=row["started_at"],
                        completed_at=row["completed_at"],
                        status=row["status"],
                        result=row["result"],
                        num_agents=row["num_agents"],
                        num_subtasks=row["num_subtasks"],
                        num_completed=row["num_completed"],
                        num_failed=row["num_failed"],
                        elapsed_seconds=row["elapsed_seconds"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    )
                    for row in rows
                ]

    async def get_session_stats(self) -> Dict[str, Any]:
        """Get overall session statistics"""
        await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    AVG(elapsed_seconds) as avg_elapsed,
                    SUM(num_subtasks) as total_subtasks,
                    SUM(num_completed) as total_completed_subtasks,
                    SUM(num_failed) as total_failed_subtasks
                FROM crew_sessions
            """) as cursor:
                row = await cursor.fetchone()
                return {
                    "total_sessions": row[0] or 0,
                    "completed": row[1] or 0,
                    "failed": row[2] or 0,
                    "avg_elapsed_seconds": row[3] or 0,
                    "total_subtasks": row[4] or 0,
                    "total_completed_subtasks": row[5] or 0,
                    "total_failed_subtasks": row[6] or 0,
                    "success_rate": (row[1] / row[0] * 100) if row[0] else 0,
                }

    @property
    def current_session(self) -> Optional[SessionRecord]:
        return self._current_session
