"""Chat entity - represents a Telegram chat."""

from datetime import datetime
from enum import Enum
from typing import Optional

from alphasnob.domain.messaging.value_objects.chat_id import ChatId
from alphasnob.domain.shared.base_entity import Entity


class ChatType(str, Enum):
    """Type of Telegram chat."""

    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


class Chat(Entity):
    """Telegram chat entity.

    Represents a chat (private, group, supergroup, or channel).

    Examples:
        chat = Chat(
            chat_id=ChatId(-987654321),
            title="My Group",
            chat_type=ChatType.GROUP,
        )

    Attributes:
        chat_id: Telegram chat ID
        title: Chat title (for groups/channels)
        chat_type: Type of chat
        username: Chat username (optional, for public groups/channels)
        description: Chat description (optional)
        member_count: Number of members (for groups)
        message_count: Total messages in this chat
        last_message_at: When last message was sent
        is_active: Whether chat is currently active
    """

    chat_id: ChatId
    title: Optional[str] = None
    chat_type: ChatType
    username: Optional[str] = None
    description: Optional[str] = None

    # Statistics
    member_count: Optional[int] = None
    message_count: int = 0
    last_message_at: Optional[datetime] = None

    # Status
    is_active: bool = True

    def is_private(self) -> bool:
        """Check if this is a private chat.

        Returns:
            True if private chat, False otherwise
        """
        return self.chat_type == ChatType.PRIVATE

    def is_group(self) -> bool:
        """Check if this is a group chat.

        Returns:
            True if group or supergroup, False otherwise
        """
        return self.chat_type in (ChatType.GROUP, ChatType.SUPERGROUP)

    def is_channel(self) -> bool:
        """Check if this is a channel.

        Returns:
            True if channel, False otherwise
        """
        return self.chat_type == ChatType.CHANNEL

    def record_message(self) -> None:
        """Record that a message was sent in this chat.

        Side effects:
            - Increments message_count
            - Updates last_message_at
            - Marks entity as updated
        """
        self.message_count += 1
        self.last_message_at = datetime.now()
        self.mark_updated()

    def deactivate(self) -> None:
        """Mark chat as inactive (e.g., bot was removed).

        Side effects:
            - Sets is_active to False
            - Marks entity as updated
        """
        self.is_active = False
        self.mark_updated()

    def activate(self) -> None:
        """Mark chat as active.

        Side effects:
            - Sets is_active to True
            - Marks entity as updated
        """
        self.is_active = True
        self.mark_updated()

    def display_name(self) -> str:
        """Get best display name for chat.

        Returns:
            Title, username, or "Private Chat"
        """
        if self.title:
            return self.title
        if self.username:
            return f"@{self.username}"
        if self.is_private():
            return "Private Chat"
        return f"Chat {self.chat_id}"

    def __str__(self) -> str:
        """Return human-readable string."""
        return f"Chat({self.display_name()}, {self.chat_type.value})"
