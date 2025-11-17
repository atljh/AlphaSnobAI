import logging
from datetime import datetime, timedelta
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

from utils.db_migration import run_migration


class Message:
    """Represents a single message."""

    def __init__(self, chat_id: int, user_id: int, username: str, text: str, timestamp):
        self.chat_id = chat_id
        self.user_id = user_id
        self.username = username
        self.text = text
        # Convert string timestamp to datetime if needed
        if isinstance(timestamp, str):
            self.timestamp = datetime.fromisoformat(timestamp)
        elif isinstance(timestamp, datetime):
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "username": self.username,
            "text": self.text,
            "timestamp": self.timestamp.isoformat()
            if isinstance(self.timestamp, datetime)
            else self.timestamp,
        }

    def __repr__(self):
        return f"Message(user={self.username}, text={self.text[:30]}...)"


class Memory:
    """Manages conversation context using SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    text TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chat_timestamp
                ON messages(chat_id, timestamp DESC)
            """,
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chat_id
                ON messages(chat_id)
            """,
            )

            await db.commit()

        await run_migration(self.db_path)

        self._initialized = True
        logger.info(f"Memory initialized at {self.db_path}")

    async def add_message(
        self,
        chat_id: int,
        user_id: int,
        username: str | None,
        text: str,
        timestamp: datetime | None = None,
        persona_mode: str | None = None,
        response_delay_ms: int | None = None,
        decision_score: float | None = None,
    ):
        """Add a message to memory.

        Args:
            chat_id: Chat ID
            user_id: User ID
            username: Username (can be None)
            text: Message text
            timestamp: Message timestamp (defaults to now)
            persona_mode: Which persona was used (for bot messages)
            response_delay_ms: Response delay in ms (for bot messages)
            decision_score: Decision probability score
        """
        if not self._initialized:
            await self.initialize()

        if timestamp is None:
            timestamp = datetime.now()

        timestamp_str = timestamp.isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO messages (
                    chat_id, user_id, username, text, timestamp,
                    persona_mode, response_delay_ms, decision_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chat_id,
                    user_id,
                    username or "Unknown",
                    text,
                    timestamp_str,
                    persona_mode,
                    response_delay_ms,
                    decision_score,
                ),
            )
            await db.commit()

        logger.debug(f"Added message from {username} in chat {chat_id}")

    async def get_context(
        self,
        chat_id: int,
        limit: int = 50,
    ) -> list[Message]:
        """Get recent messages from a chat for context.

        Args:
            chat_id: Chat ID to get context from
            limit: Maximum number of messages to retrieve

        Returns:
            List of Message objects, ordered from oldest to newest
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute(
                """
                SELECT chat_id, user_id, username, text, timestamp
                FROM messages
                WHERE chat_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (chat_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()

        messages = [
            Message(
                chat_id=row["chat_id"],
                user_id=row["user_id"],
                username=row["username"],
                text=row["text"],
                timestamp=row["timestamp"],
            )
            for row in reversed(rows)
        ]

        logger.debug(f"Retrieved {len(messages)} messages for chat {chat_id}")
        return messages

    async def get_context_text(
        self,
        chat_id: int,
        limit: int = 50,
        include_usernames: bool = True,
    ) -> str:
        """Get context as formatted text.

        Args:
            chat_id: Chat ID
            limit: Maximum messages
            include_usernames: Whether to include usernames in format

        Returns:
            Formatted context string
        """
        messages = await self.get_context(chat_id, limit)

        if not messages:
            return ""

        if include_usernames:
            return "\n".join(f"{msg.username}: {msg.text}" for msg in messages)
        return "\n".join(msg.text for msg in messages)

    async def clear_chat_history(self, chat_id: int):
        """Clear all messages from a specific chat.

        Args:
            chat_id: Chat ID to clear
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM messages WHERE chat_id = ?",
                (chat_id,),
            )
            await db.commit()

        logger.info(f"Cleared history for chat {chat_id}")

    async def get_total_messages(self) -> int:
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM messages") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_chat_statistics(self, chat_id: int) -> dict:
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM messages WHERE chat_id = ?",
                (chat_id,),
            ) as cursor:
                row = await cursor.fetchone()
                total = row[0] if row else 0

            async with db.execute(
                "SELECT COUNT(DISTINCT user_id) FROM messages WHERE chat_id = ?",
                (chat_id,),
            ) as cursor:
                row = await cursor.fetchone()
                unique_users = row[0] if row else 0

        return {
            "total_messages": total,
            "unique_users": unique_users,
            "chat_id": chat_id,
        }

    async def count_recent_bot_messages(
        self,
        chat_id: int,
        bot_user_id: int,
        window_seconds: int = 60,
    ) -> int:
        if not self._initialized:
            await self.initialize()

        cutoff_time = (datetime.now() - timedelta(seconds=window_seconds)).isoformat()

        async with (
            aiosqlite.connect(self.db_path) as db,
            db.execute(
                """
                SELECT COUNT(*) FROM messages
                WHERE chat_id = ? AND user_id = ? AND timestamp > ?
                """,
                (chat_id, bot_user_id, cutoff_time),
            ) as cursor,
        ):
            row = await cursor.fetchone()
            return row[0] if row else 0
