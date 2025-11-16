"""Message repository interface (port)."""

from datetime import datetime
from typing import Optional, Protocol
from uuid import UUID

from alphasnob.domain.messaging.entities.chat import Chat
from alphasnob.domain.messaging.entities.message import Message
from alphasnob.domain.messaging.value_objects.chat_id import ChatId
from alphasnob.domain.users.value_objects.user_id import UserId


class MessageRepository(Protocol):
    """Repository interface for message persistence.

    Handles storage and retrieval of messages with various query capabilities.
    """

    async def get_by_id(self, id: UUID) -> Optional[Message]:
        """Get message by internal UUID.

        Args:
            id: Internal entity UUID

        Returns:
            Message if found, None otherwise
        """
        ...

    async def get_by_message_id(self, message_id: int, chat_id: ChatId) -> Optional[Message]:
        """Get message by Telegram message ID in specific chat.

        Args:
            message_id: Telegram message ID
            chat_id: Chat ID where message was sent

        Returns:
            Message if found, None otherwise
        """
        ...

    async def save(self, message: Message) -> None:
        """Save or update message.

        Args:
            message: Message entity to save
        """
        ...

    async def delete(self, message: Message) -> None:
        """Delete message.

        Args:
            message: Message entity to delete
        """
        ...

    async def find_recent_in_chat(
        self, chat_id: ChatId, limit: int = 50
    ) -> list[Message]:
        """Get recent messages in a chat.

        Args:
            chat_id: Chat ID
            limit: Maximum number of messages

        Returns:
            List of messages, newest first
        """
        ...

    async def find_by_user(
        self, user_id: UserId, limit: int = 100
    ) -> list[Message]:
        """Get messages from a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of messages

        Returns:
            List of messages, newest first
        """
        ...

    async def find_bot_messages(
        self, chat_id: ChatId, limit: int = 50
    ) -> list[Message]:
        """Get messages sent by bot in a chat.

        Args:
            chat_id: Chat ID
            limit: Maximum number of messages

        Returns:
            List of bot messages, newest first
        """
        ...

    async def find_in_time_range(
        self,
        chat_id: ChatId,
        start_time: datetime,
        end_time: datetime,
    ) -> list[Message]:
        """Get messages in time range.

        Args:
            chat_id: Chat ID
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of messages in time range
        """
        ...

    async def count_by_chat(self, chat_id: ChatId) -> int:
        """Count total messages in a chat.

        Args:
            chat_id: Chat ID

        Returns:
            Total message count
        """
        ...

    async def count_by_user(self, user_id: UserId) -> int:
        """Count total messages from a user.

        Args:
            user_id: User ID

        Returns:
            Total message count
        """
        ...


class ChatRepository(Protocol):
    """Repository interface for chat persistence."""

    async def get_by_id(self, id: UUID) -> Optional[Chat]:
        """Get chat by internal UUID.

        Args:
            id: Internal entity UUID

        Returns:
            Chat if found, None otherwise
        """
        ...

    async def get_by_chat_id(self, chat_id: ChatId) -> Optional[Chat]:
        """Get chat by Telegram chat ID.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Chat if found, None otherwise
        """
        ...

    async def get_or_create(self, chat_id: ChatId, **kwargs: str) -> Chat:
        """Get existing chat or create new one.

        Args:
            chat_id: Telegram chat ID
            **kwargs: Additional chat info (title, type, etc.)

        Returns:
            Chat entity (existing or newly created)
        """
        ...

    async def save(self, chat: Chat) -> None:
        """Save or update chat.

        Args:
            chat: Chat entity to save
        """
        ...

    async def delete(self, chat: Chat) -> None:
        """Delete chat.

        Args:
            chat: Chat entity to delete
        """
        ...

    async def find_active(self, limit: int = 100) -> list[Chat]:
        """Get active chats.

        Args:
            limit: Maximum number of chats

        Returns:
            List of active chats, sorted by last activity
        """
        ...

    async def count(self) -> int:
        """Get total number of chats.

        Returns:
            Total chat count
        """
        ...
