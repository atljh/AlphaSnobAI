"""Statistics collection from database."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite


@dataclass
class GeneralStats:
    """General bot statistics."""

    total_messages: int
    bot_messages: int
    user_messages: int
    unique_users: int
    unique_chats: int
    response_rate: float
    avg_decision_score: float
    messages_today: int
    responses_today: int


@dataclass
class ChatStats:
    """Per-chat statistics."""

    chat_id: int
    total_messages: int
    unique_users: int
    bot_messages: int
    first_message: datetime | None
    last_message: datetime | None


@dataclass
class UserStats:
    """Per-user statistics."""

    user_id: int
    username: str
    total_messages: int
    total_chats: int
    relationship_level: str
    trust_score: float
    interaction_count: int
    first_interaction: datetime | None
    last_interaction: datetime | None


@dataclass
class PersonaStats:
    """Persona usage statistics."""

    persona_name: str
    usage_count: int
    percentage: float


class StatsCollector:
    """Collect statistics from database."""

    def __init__(self, db_path: Path):
        """Initialize stats collector.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

    async def get_general_stats(self) -> GeneralStats:
        """Get general bot statistics.

        Returns:
            General statistics
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Total messages
            cursor = await db.execute("SELECT COUNT(*) FROM messages")
            total_messages = (await cursor.fetchone())[0]

            # Bot vs user messages (assuming bot user_id is stored in config)
            cursor = await db.execute(
                "SELECT COUNT(*) FROM messages WHERE persona_mode IS NOT NULL",
            )
            bot_messages = (await cursor.fetchone())[0]
            user_messages = total_messages - bot_messages

            # Unique users
            cursor = await db.execute("SELECT COUNT(DISTINCT user_id) FROM messages")
            unique_users = (await cursor.fetchone())[0]

            # Unique chats
            cursor = await db.execute("SELECT COUNT(DISTINCT chat_id) FROM messages")
            unique_chats = (await cursor.fetchone())[0]

            # Response rate
            response_rate = (bot_messages / user_messages * 100) if user_messages > 0 else 0

            # Average decision score
            cursor = await db.execute(
                "SELECT AVG(decision_score) FROM messages WHERE decision_score IS NOT NULL",
            )
            result = await cursor.fetchone()
            avg_decision_score = result[0] if result[0] is not None else 0.0

            # Messages today
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cursor = await db.execute(
                "SELECT COUNT(*) FROM messages WHERE timestamp >= ?",
                (today,),
            )
            messages_today = (await cursor.fetchone())[0]

            # Responses today
            cursor = await db.execute(
                "SELECT COUNT(*) FROM messages WHERE timestamp >= ? AND persona_mode IS NOT NULL",
                (today,),
            )
            responses_today = (await cursor.fetchone())[0]

            return GeneralStats(
                total_messages=total_messages,
                bot_messages=bot_messages,
                user_messages=user_messages,
                unique_users=unique_users,
                unique_chats=unique_chats,
                response_rate=response_rate,
                avg_decision_score=avg_decision_score,
                messages_today=messages_today,
                responses_today=responses_today,
            )

    async def get_chat_stats(self, chat_id: int) -> ChatStats | None:
        async with aiosqlite.connect(self.db_path) as db:
            # Total messages
            cursor = await db.execute(
                "SELECT COUNT(*) FROM messages WHERE chat_id = ?",
                (chat_id,),
            )
            total_messages = (await cursor.fetchone())[0]

            if total_messages == 0:
                return None

            # Unique users
            cursor = await db.execute(
                "SELECT COUNT(DISTINCT user_id) FROM messages WHERE chat_id = ?",
                (chat_id,),
            )
            unique_users = (await cursor.fetchone())[0]

            # Bot messages
            cursor = await db.execute(
                "SELECT COUNT(*) FROM messages WHERE chat_id = ? AND persona_mode IS NOT NULL",
                (chat_id,),
            )
            bot_messages = (await cursor.fetchone())[0]

            # First and last message
            cursor = await db.execute(
                "SELECT MIN(timestamp), MAX(timestamp) FROM messages WHERE chat_id = ?",
                (chat_id,),
            )
            first, last = await cursor.fetchone()

            return ChatStats(
                chat_id=chat_id,
                total_messages=total_messages,
                unique_users=unique_users,
                bot_messages=bot_messages,
                first_message=datetime.fromisoformat(first) if first else None,
                last_message=datetime.fromisoformat(last) if last else None,
            )

    async def get_user_stats(self, user_id: int) -> UserStats | None:
        async with aiosqlite.connect(self.db_path) as db:
            # Get profile
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM user_profiles WHERE user_id = ?",
                (user_id,),
            )
            profile = await cursor.fetchone()

            if not profile:
                return None

            # Total messages
            cursor = await db.execute(
                "SELECT COUNT(*) FROM messages WHERE user_id = ?",
                (user_id,),
            )
            total_messages = (await cursor.fetchone())[0]

            # Total chats
            cursor = await db.execute(
                "SELECT COUNT(DISTINCT chat_id) FROM messages WHERE user_id = ?",
                (user_id,),
            )
            total_chats = (await cursor.fetchone())[0]

            return UserStats(
                user_id=user_id,
                username=profile["username"],
                total_messages=total_messages,
                total_chats=total_chats,
                relationship_level=profile["relationship_level"],
                trust_score=profile["trust_score"],
                interaction_count=profile["interaction_count"],
                first_interaction=datetime.fromisoformat(profile["first_interaction"])
                if profile["first_interaction"]
                else None,
                last_interaction=datetime.fromisoformat(profile["last_interaction"])
                if profile["last_interaction"]
                else None,
            )

    async def get_top_chats(self, limit: int = 5) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT chat_id, COUNT(*) as message_count
                FROM messages
                GROUP BY chat_id
                ORDER BY message_count DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = await cursor.fetchall()

            return [dict(row) for row in rows]

    async def get_top_users(self, limit: int = 5) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT m.user_id, m.username, COUNT(*) as message_count
                FROM messages m
                WHERE m.persona_mode IS NULL
                GROUP BY m.user_id
                ORDER BY message_count DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = await cursor.fetchall()

            return [dict(row) for row in rows]

    async def get_persona_stats(self) -> list[PersonaStats]:
        async with aiosqlite.connect(self.db_path) as db:
            # Total bot messages
            cursor = await db.execute(
                "SELECT COUNT(*) FROM messages WHERE persona_mode IS NOT NULL",
            )
            total_bot_messages = (await cursor.fetchone())[0]

            if total_bot_messages == 0:
                return []

            # Per persona
            cursor = await db.execute(
                """
                SELECT persona_mode, COUNT(*) as count
                FROM messages
                WHERE persona_mode IS NOT NULL
                GROUP BY persona_mode
                ORDER BY count DESC
                """,
            )
            rows = await cursor.fetchall()

            stats = []
            for persona_name, count in rows:
                percentage = count / total_bot_messages * 100
                stats.append(
                    PersonaStats(
                        persona_name=persona_name,
                        usage_count=count,
                        percentage=percentage,
                    ),
                )

            return stats

    async def get_decision_stats(self) -> dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            # Average score
            cursor = await db.execute(
                "SELECT AVG(decision_score) FROM messages WHERE decision_score IS NOT NULL",
            )
            avg_score = (await cursor.fetchone())[0] or 0.0

            # Min/max scores
            cursor = await db.execute(
                "SELECT MIN(decision_score), MAX(decision_score) FROM messages WHERE decision_score IS NOT NULL",
            )
            min_score, max_score = await cursor.fetchone()

            # Score distribution (ranges)
            cursor = await db.execute(
                """
                SELECT
                    SUM(CASE WHEN decision_score < 0.3 THEN 1 ELSE 0 END) as low,
                    SUM(CASE WHEN decision_score >= 0.3 AND decision_score < 0.7 THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN decision_score >= 0.7 THEN 1 ELSE 0 END) as high
                FROM messages
                WHERE decision_score IS NOT NULL
                """,
            )
            low, medium, high = await cursor.fetchone()

            return {
                "avg_score": avg_score,
                "min_score": min_score or 0.0,
                "max_score": max_score or 0.0,
                "distribution": {
                    "low (<0.3)": low or 0,
                    "medium (0.3-0.7)": medium or 0,
                    "high (≥0.7)": high or 0,
                },
            }

    async def export_stats(self, format: str = "json") -> dict[str, Any]:
        general = await self.get_general_stats()
        top_chats = await self.get_top_chats()
        top_users = await self.get_top_users()
        persona_stats = await self.get_persona_stats()
        decision_stats = await self.get_decision_stats()

        return {
            "general": {
                "total_messages": general.total_messages,
                "bot_messages": general.bot_messages,
                "user_messages": general.user_messages,
                "unique_users": general.unique_users,
                "unique_chats": general.unique_chats,
                "response_rate": general.response_rate,
                "avg_decision_score": general.avg_decision_score,
                "messages_today": general.messages_today,
                "responses_today": general.responses_today,
            },
            "top_chats": top_chats,
            "top_users": top_users,
            "personas": [
                {
                    "name": ps.persona_name,
                    "usage": ps.usage_count,
                    "percentage": ps.percentage,
                }
                for ps in persona_stats
            ],
            "decision_engine": decision_stats,
        }
