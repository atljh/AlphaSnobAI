"""Auto-collection of owner messages for style learning."""

import logging
from datetime import datetime
from pathlib import Path

from config.settings import OwnerLearningConfig

logger = logging.getLogger(__name__)


class OwnerMessageCollector:
    """Automatically collect owner messages for style learning."""

    def __init__(self, config: OwnerLearningConfig):
        """Initialize owner message collector.

        Args:
            config: Owner learning configuration
        """
        self.config = config
        self.collection_path = Path(config.collection_path)
        self.collected_file = self.collection_path / "messages.txt"
        self.collected_messages: set[str] = set()

        # Create collection directory
        self.collection_path.mkdir(parents=True, exist_ok=True)

        # Load existing collected messages to avoid duplicates
        self._load_existing_messages()

        logger.info(f"OwnerMessageCollector initialized (auto_collect: {config.auto_collect})")
        logger.info(f"Collection path: {self.collected_file}")
        logger.info(f"Already collected: {len(self.collected_messages)} messages")

    def _load_existing_messages(self):
        """Load existing collected messages to avoid duplicates."""
        if not self.collected_file.exists():
            return

        try:
            with open(self.collected_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self.collected_messages.add(line)
            logger.debug(f"Loaded {len(self.collected_messages)} existing messages")
        except Exception as e:
            logger.error(f"Failed to load existing messages: {e}")

    def is_owner(self, user_id: int) -> bool:
        """Check if user is owner.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user is in owner_user_ids list
        """
        return user_id in self.config.owner_user_ids

    async def collect_message(
        self,
        user_id: int,
        username: str,
        text: str,
    ) -> bool:
        """Collect owner message if it's new.

        Args:
            user_id: User ID
            username: Username
            text: Message text

        Returns:
            True if message was collected (new), False if duplicate
        """
        if not self.config.auto_collect:
            return False

        if not self.is_owner(user_id):
            return False

        # Skip empty messages
        text = text.strip()
        if not text:
            return False

        # Skip if already collected
        if text in self.collected_messages:
            logger.debug(f"Skipping duplicate message from {username}")
            return False

        # Collect the message
        try:
            with open(self.collected_file, "a", encoding="utf-8") as f:
                f.write(f"{text}\n")

            self.collected_messages.add(text)
            logger.info(
                f"✅ Collected owner message from {username} (total: {len(self.collected_messages)})",
            )

            # Check if we should trigger re-analysis
            if len(self.collected_messages) % 10 == 0:
                logger.info(
                    f"📊 Milestone reached: {len(self.collected_messages)} messages collected",
                )

            return True

        except Exception as e:
            logger.error(f"Failed to collect message: {e}")
            return False

    def get_collection_stats(self) -> dict:
        """Get collection statistics.

        Returns:
            Dict with collection stats
        """
        return {
            "total_collected": len(self.collected_messages),
            "collection_path": str(self.collected_file),
            "auto_collect_enabled": self.config.auto_collect,
            "owner_user_ids": self.config.owner_user_ids,
            "min_samples_required": self.config.min_samples,
            "has_sufficient_samples": len(self.collected_messages) >= self.config.min_samples,
        }

    def get_all_samples(self) -> list[str]:
        """Get all collected samples.

        Returns:
            List of all collected messages
        """
        return list(self.collected_messages)

    def merge_with_manual_samples(self, manual_samples_path: Path) -> int:
        """Merge auto-collected samples with manual samples.

        Args:
            manual_samples_path: Path to manual samples file

        Returns:
            Number of samples merged
        """
        if not self.collected_file.exists():
            logger.warning("No auto-collected messages to merge")
            return 0

        try:
            # Read auto-collected messages
            with open(self.collected_file, encoding="utf-8") as f:
                auto_messages = set(
                    line.strip() for line in f if line.strip() and not line.startswith("#")
                )

            # Read existing manual messages
            manual_messages = set()
            if manual_samples_path.exists():
                with open(manual_samples_path, encoding="utf-8") as f:
                    manual_messages = set(
                        line.strip() for line in f if line.strip() and not line.startswith("#")
                    )

            # Find new messages to add
            new_messages = auto_messages - manual_messages

            if not new_messages:
                logger.info("No new messages to merge")
                return 0

            # Append new messages to manual samples
            with open(manual_samples_path, "a", encoding="utf-8") as f:
                f.write(f"\n# Auto-collected on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                for msg in sorted(new_messages):
                    f.write(f"{msg}\n")

            logger.info(f"Merged {len(new_messages)} auto-collected messages into manual samples")
            return len(new_messages)

        except Exception as e:
            logger.error(f"Failed to merge samples: {e}")
            return 0

    def clear_collection(self):
        """Clear all collected messages."""
        try:
            if self.collected_file.exists():
                self.collected_file.unlink()

            self.collected_messages.clear()
            logger.info("Cleared all collected messages")

        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
