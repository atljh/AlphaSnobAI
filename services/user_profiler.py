import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import aiosqlite
from config.settings import ProfilingConfig

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    user_id: int
    username: str
    first_name: str | None = None
    last_name: str | None = None
    relationship_level: str = "stranger"
    trust_score: float = 0.0
    interaction_count: int = 0
    notes: str | None = None
    detected_topics: list[str] = None
    preferred_persona: str | None = None
    first_interaction: datetime | None = None
    last_interaction: datetime | None = None
    avg_response_time_ms: int = 0

    def __post_init__(self):
        if self.detected_topics is None:
            self.detected_topics = []

    def __repr__(self):
        return (
            f"UserProfile({self.username}, {self.relationship_level}, trust={self.trust_score:.2f})"
        )


class UserProfiler:
    def __init__(self, db_path: Path, profiling_config: ProfilingConfig):
        self.db_path = db_path
        self.config = profiling_config
        self._initialized = False
        logger.info(f"UserProfiler initialized (enabled: {self.config.enabled})")

    async def initialize(self):
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    relationship_level TEXT DEFAULT 'stranger',
                    trust_score REAL DEFAULT 0.0,
                    interaction_count INTEGER DEFAULT 0,
                    notes TEXT,
                    detected_topics TEXT,
                    preferred_persona TEXT,
                    first_interaction TIMESTAMP,
                    last_interaction TIMESTAMP,
                    avg_response_time_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            )

            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_relationship ON user_profiles(relationship_level)",
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_last_interaction ON user_profiles(last_interaction)",
            )

            await db.commit()

        self._initialized = True
        logger.info("UserProfiler database initialized")

    async def get_or_create_profile(self, user_id: int, username: str) -> UserProfile:
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute(
                "SELECT * FROM user_profiles WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()

            if row:
                detected_topics = (
                    json.loads(row["detected_topics"]) if row["detected_topics"] else []
                )

                return UserProfile(
                    user_id=row["user_id"],
                    username=row["username"],
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                    relationship_level=row["relationship_level"],
                    trust_score=row["trust_score"],
                    interaction_count=row["interaction_count"],
                    notes=row["notes"],
                    detected_topics=detected_topics,
                    preferred_persona=row["preferred_persona"],
                    first_interaction=(
                        datetime.fromisoformat(row["first_interaction"])
                        if row["first_interaction"]
                        else None
                    ),
                    last_interaction=(
                        datetime.fromisoformat(row["last_interaction"])
                        if row["last_interaction"]
                        else None
                    ),
                    avg_response_time_ms=row["avg_response_time_ms"],
                )
            now = datetime.now()
            await db.execute(
                """
                    INSERT INTO user_profiles (
                        user_id, username, first_interaction, last_interaction
                    ) VALUES (?, ?, ?, ?)
                    """,
                (user_id, username, now.isoformat(), now.isoformat()),
            )
            await db.commit()

            logger.info(f"Created new profile for user {username} ({user_id})")

            return UserProfile(
                user_id=user_id,
                username=username,
                first_interaction=now,
                last_interaction=now,
            )

    async def update_profile(self, user_id: int, **kwargs):
        if not self._initialized:
            await self.initialize()

        if "detected_topics" in kwargs and isinstance(kwargs["detected_topics"], list):
            kwargs["detected_topics"] = json.dumps(kwargs["detected_topics"])

        if not kwargs:
            return

        # Whitelist of allowed column names to prevent SQL injection
        allowed_columns = {
            "username",
            "first_name",
            "last_name",
            "relationship_level",
            "trust_score",
            "interaction_count",
            "positive_interactions",
            "preferred_persona",
            "detected_topics",
            "last_interaction",
        }

        # Filter to only allowed columns
        safe_kwargs = {k: v for k, v in kwargs.items() if k in allowed_columns}
        if not safe_kwargs:
            return

        set_clauses = ", ".join(f"{key} = ?" for key in safe_kwargs)
        set_clauses += ", updated_at = CURRENT_TIMESTAMP"

        values = list(safe_kwargs.values()) + [user_id]

        query = f"UPDATE user_profiles SET {set_clauses} WHERE user_id = ?"  # nosec B608

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, values)
            await db.commit()

        logger.debug(f"Updated profile for user {user_id}: {list(kwargs.keys())}")

    async def increment_interaction(self, user_id: int):
        if not self._initialized:
            await self.initialize()

        now = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE user_profiles
                SET interaction_count = interaction_count + 1,
                    last_interaction = ?
                WHERE user_id = ?
                """,
                (now, user_id),
            )
            await db.commit()

        if self.config.auto_upgrade.enabled:
            await self._check_and_upgrade_relationship(user_id)

    async def adjust_trust_score(self, user_id: int, delta: float):
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE user_profiles
                SET trust_score = CASE
                    WHEN trust_score + ? > 1.0 THEN 1.0
                    WHEN trust_score + ? < -1.0 THEN -1.0
                    ELSE trust_score + ?
                END
                WHERE user_id = ?
                """,
                (delta, delta, delta, user_id),
            )
            await db.commit()

        logger.debug(f"Adjusted trust score for user {user_id} by {delta:+.2f}")

    async def analyze_and_adjust_trust(self, user_id: int, message: str):
        if not self.config.enabled:
            return

        message_lower = message.lower()

        positive_count = sum(
            1 for marker in self.config.trust_adjustment.positive_markers if marker in message_lower
        )

        negative_count = sum(
            1 for marker in self.config.trust_adjustment.negative_markers if marker in message_lower
        )

        if positive_count > 0:
            delta = positive_count * self.config.trust_adjustment.adjustment_amount
            await self.adjust_trust_score(user_id, delta)

        if negative_count > 0:
            delta = -negative_count * self.config.trust_adjustment.adjustment_amount
            await self.adjust_trust_score(user_id, delta)

    async def _check_and_upgrade_relationship(self, user_id: int):
        profile = await self.get_or_create_profile(user_id, "Unknown")

        old_level = profile.relationship_level
        new_level = old_level

        count = profile.interaction_count

        if count >= self.config.auto_upgrade.friend_to_close_friend:
            new_level = "close_friend"
        elif count >= self.config.auto_upgrade.acquaintance_to_friend:
            new_level = "friend"
        elif count >= self.config.auto_upgrade.stranger_to_acquaintance:
            new_level = "acquaintance"

        if new_level != old_level:
            await self.update_profile(user_id, relationship_level=new_level)
            logger.info(f"User {user_id} relationship upgraded: {old_level} → {new_level}")

    async def add_topic(self, user_id: int, topic: str):
        profile = await self.get_or_create_profile(user_id, "Unknown")

        if topic not in profile.detected_topics:
            profile.detected_topics.append(topic)

            if len(profile.detected_topics) > 20:
                profile.detected_topics = profile.detected_topics[-20:]

            await self.update_profile(user_id, detected_topics=profile.detected_topics)

    async def get_profile_summary(self, user_id: int) -> str:
        profile = await self.get_or_create_profile(user_id, "Unknown")

        summary = f"""User Profile: {profile.username}
- Relationship: {profile.relationship_level}
- Trust: {profile.trust_score:+.2f}
- Interactions: {profile.interaction_count}
- Topics: {", ".join(profile.detected_topics[:5]) if profile.detected_topics else "None"}
- Preferred persona: {profile.preferred_persona or "Default"}
"""
        return summary
