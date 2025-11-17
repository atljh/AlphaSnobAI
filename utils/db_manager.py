"""Database management utilities."""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiosqlite


class DatabaseManager:
    """Manage database operations."""

    def __init__(self, db_path: Path):
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

    async def backup(self, output_path: Path | None = None) -> Path:
        """Create database backup.

        Args:
            output_path: Output path (default: db_backup_TIMESTAMP.db)

        Returns:
            Path to backup file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.db_path.parent / f"backup_{timestamp}.db"

        # Copy database file
        shutil.copy2(self.db_path, output_path)

        return output_path

    async def restore(self, backup_path: Path) -> bool:
        """Restore database from backup.

        Args:
            backup_path: Path to backup file

        Returns:
            True if successful
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Create backup of current database first
        current_backup = await self.backup()

        try:
            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            return True
        except Exception as e:
            # Restore original if restore failed
            shutil.copy2(current_backup, self.db_path)
            raise e

    async def clean_old_messages(
        self,
        older_than: timedelta,
        chat_id: int | None = None,
    ) -> int:
        """Delete old messages.

        Args:
            older_than: Delete messages older than this
            chat_id: Only delete from specific chat (None = all chats)

        Returns:
            Number of messages deleted
        """
        cutoff_date = datetime.now() - older_than

        async with aiosqlite.connect(self.db_path) as db:
            if chat_id:
                cursor = await db.execute(
                    "DELETE FROM messages WHERE chat_id = ? AND timestamp < ?",
                    (chat_id, cutoff_date),
                )
            else:
                cursor = await db.execute(
                    "DELETE FROM messages WHERE timestamp < ?",
                    (cutoff_date,),
                )

            deleted = cursor.rowcount
            await db.commit()

            return deleted

    async def export_chat_history(
        self,
        chat_id: int,
        format: str = "json",
        output_path: Path | None = None,
    ) -> Path:
        """Export chat history.

        Args:
            chat_id: Chat ID to export
            format: Export format ('json' or 'txt')
            output_path: Output file path

        Returns:
            Path to exported file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"chat_{chat_id}_{timestamp}.{format}")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT chat_id, user_id, username, text, timestamp, persona_mode
                FROM messages
                WHERE chat_id = ?
                ORDER BY timestamp ASC
                """,
                (chat_id,),
            )
            messages = await cursor.fetchall()

        if format == "json":
            data = [dict(msg) for msg in messages]
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        elif format == "txt":
            with open(output_path, "w", encoding="utf-8") as f:
                for msg in messages:
                    timestamp = msg["timestamp"]
                    username = msg["username"]
                    text = msg["text"]
                    persona = f" [{msg['persona_mode']}]" if msg["persona_mode"] else ""
                    f.write(f"[{timestamp}] {username}{persona}: {text}\n")

        return output_path

    async def vacuum(self) -> None:
        """Optimize database (VACUUM)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("VACUUM")
            await db.commit()

    async def get_stats(self) -> dict[str, Any]:
        """Get database statistics.

        Returns:
            Database stats dict
        """
        stats = {}

        # File size
        if self.db_path.exists():
            stats["file_size_mb"] = self.db_path.stat().st_size / (1024 * 1024)
        else:
            stats["file_size_mb"] = 0

        async with aiosqlite.connect(self.db_path) as db:
            # Table counts
            cursor = await db.execute("SELECT COUNT(*) FROM messages")
            stats["messages_count"] = (await cursor.fetchone())[0]

            cursor = await db.execute("SELECT COUNT(*) FROM user_profiles")
            stats["profiles_count"] = (await cursor.fetchone())[0]

            # Oldest and newest message
            cursor = await db.execute(
                "SELECT MIN(timestamp), MAX(timestamp) FROM messages",
            )
            oldest, newest = await cursor.fetchone()
            stats["oldest_message"] = oldest
            stats["newest_message"] = newest

            # Database info
            cursor = await db.execute("PRAGMA page_count")
            page_count = (await cursor.fetchone())[0]

            cursor = await db.execute("PRAGMA page_size")
            page_size = (await cursor.fetchone())[0]

            stats["total_pages"] = page_count
            stats["page_size"] = page_size
            stats["db_size_mb"] = (page_count * page_size) / (1024 * 1024)

        return stats

    async def migrate(self) -> bool:
        """Apply database migrations.

        Returns:
            True if migrations applied successfully
        """
        # Import migration module if it exists
        try:
            from utils.db_migration import migrate_database

            return await migrate_database(self.db_path)
        except ImportError:
            # No migrations defined
            return False

    async def check_integrity(self) -> bool:
        """Check database integrity.

        Returns:
            True if database is OK
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("PRAGMA integrity_check")
            result = (await cursor.fetchone())[0]
            return result == "ok"

    async def get_table_info(self) -> dict[str, list[dict[str, Any]]]:
        """Get information about all tables.

        Returns:
            Dict mapping table names to column info
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Get all table names
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'",
            )
            tables = [row[0] for row in await cursor.fetchall()]

            table_info = {}
            for table in tables:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(f"PRAGMA table_info({table})")
                columns = [dict(row) for row in await cursor.fetchall()]
                table_info[table] = columns

            return table_info

    async def export_profiles(self, output_path: Path) -> int:
        """Export user profiles to JSON.

        Args:
            output_path: Output file path

        Returns:
            Number of profiles exported
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM user_profiles")
            profiles = [dict(row) for row in await cursor.fetchall()]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False, default=str)

        return len(profiles)

    async def import_profiles(self, input_path: Path) -> int:
        """Import user profiles from JSON.

        Args:
            input_path: Input file path

        Returns:
            Number of profiles imported
        """
        with open(input_path, encoding="utf-8") as f:
            profiles = json.load(f)

        async with aiosqlite.connect(self.db_path) as db:
            for profile in profiles:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO user_profiles
                    (user_id, username, first_name, last_name, relationship_level,
                     trust_score, interaction_count, detected_topics, preferred_persona,
                     notes, first_interaction, last_interaction)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        profile["user_id"],
                        profile.get("username"),
                        profile.get("first_name"),
                        profile.get("last_name"),
                        profile.get("relationship_level", "stranger"),
                        profile.get("trust_score", 0.0),
                        profile.get("interaction_count", 0),
                        profile.get("detected_topics", ""),
                        profile.get("preferred_persona"),
                        profile.get("notes"),
                        profile.get("first_interaction"),
                        profile.get("last_interaction"),
                    ),
                )

            await db.commit()

        return len(profiles)
