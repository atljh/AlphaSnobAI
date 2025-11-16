import aiosqlite
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseMigration:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    async def run_migrations(self):
        logger.info(f"Starting database migration for {self.db_path}")

        async with aiosqlite.connect(self.db_path) as db:
            current_version = await self._get_schema_version(db)
            logger.info(f"Current schema version: {current_version}")

            if current_version < 1:
                await self._migrate_to_v1(db)

            if current_version < 2:
                await self._migrate_to_v2(db)

            await db.commit()

        logger.info("Database migration completed successfully")

    async def _get_schema_version(self, db: aiosqlite.Connection) -> int:
        try:
            cursor = await db.execute(
                "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
        except aiosqlite.OperationalError:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            return 0

    async def _migrate_to_v1(self, db: aiosqlite.Connection):
        logger.info("Applying migration v1: Extend messages table")

        cursor = await db.execute("PRAGMA table_info(messages)")
        columns = {row[1] for row in await cursor.fetchall()}

        if 'persona_mode' not in columns:
            await db.execute("ALTER TABLE messages ADD COLUMN persona_mode TEXT DEFAULT 'alphasnob'")
            logger.info("Added persona_mode column to messages")

        if 'response_delay_ms' not in columns:
            await db.execute("ALTER TABLE messages ADD COLUMN response_delay_ms INTEGER")
            logger.info("Added response_delay_ms column to messages")

        if 'decision_score' not in columns:
            await db.execute("ALTER TABLE messages ADD COLUMN decision_score REAL")
            logger.info("Added decision_score column to messages")

        await db.execute("INSERT INTO schema_version (version) VALUES (1)")
        logger.info("Migration v1 completed")

    async def _migrate_to_v2(self, db: aiosqlite.Connection):
        logger.info("Applying migration v2: Create new tables")

        await db.execute("""
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
        """)
        logger.info("Created user_profiles table")

        await db.execute("CREATE INDEX IF NOT EXISTS idx_relationship ON user_profiles(relationship_level)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_last_interaction ON user_profiles(last_interaction)")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversation_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                confidence REAL,
                persona_used TEXT,
                first_mentioned TIMESTAMP,
                last_mentioned TIMESTAMP,
                mention_count INTEGER DEFAULT 1,

                UNIQUE(chat_id, topic)
            )
        """)
        logger.info("Created conversation_topics table")

        await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_topics ON conversation_topics(chat_id, last_mentioned DESC)")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS response_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                should_respond BOOLEAN,
                decision_reason TEXT,
                persona_mode TEXT,

                read_delay_ms INTEGER,
                typing_delay_ms INTEGER,
                total_delay_ms INTEGER,

                context_used TEXT,

                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("Created response_history table")

        await db.execute("CREATE INDEX IF NOT EXISTS idx_response_chat ON response_history(chat_id, timestamp DESC)")

        await db.execute("INSERT INTO schema_version (version) VALUES (2)")
        logger.info("Migration v2 completed")


async def run_migration(db_path: Path):
    migration = DatabaseMigration(db_path)
    await migration.run_migrations()


if __name__ == "__main__":
    import asyncio
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])
    else:
        db_path = Path(__file__).parent.parent / "data" / "context.db"

    asyncio.run(run_migration(db_path))
