"""Message entity - represents a Telegram message."""

from datetime import datetime

from alphasnob.domain.messaging.value_objects.chat_id import ChatId
from alphasnob.domain.messaging.value_objects.message_content import MessageContent
from alphasnob.domain.shared.base_entity import Entity
from alphasnob.domain.users.value_objects.user_id import UserId


class Message(Entity):
    """Telegram message entity.

    Represents a message in a chat with all relevant metadata.

    Examples:
        message = Message(
            message_id=12345,
            chat_id=ChatId(-987654321),
            user_id=UserId(123456789),
            content=MessageContent("Hello!"),
            username="johndoe",
            timestamp=datetime.now()
        )

    Attributes:
        message_id: Telegram message ID
        chat_id: Chat where message was sent
        user_id: User who sent the message
        content: Message text content
        username: Sender's username (optional)
        timestamp: When message was sent
        is_from_bot: Whether this message is from our bot
        persona_mode: Persona used for bot's message (if applicable)
        response_delay_ms: Delay before sending response (if bot message)
        decision_score: Decision score for responding (if incoming)
        replied_to_id: ID of message this is replying to (optional)
    """

    message_id: int
    chat_id: ChatId
    user_id: UserId
    content: MessageContent
    username: str | None = None
    timestamp: datetime

    # Bot-specific fields
    is_from_bot: bool = False
    persona_mode: str | None = None
    response_delay_ms: int | None = None
    decision_score: float | None = None

    # Reply chain
    replied_to_id: int | None = None

    def is_reply(self) -> bool:
        """Check if this message is a reply to another message.

        Returns:
            True if this is a reply, False otherwise
        """
        return self.replied_to_id is not None

    def is_in_private_chat(self) -> bool:
        """Check if message is in private chat.

        Returns:
            True if in private chat, False otherwise
        """
        return self.chat_id.is_private()

    def is_in_group(self) -> bool:
        """Check if message is in group chat.

        Returns:
            True if in group, False otherwise
        """
        return self.chat_id.is_group() or self.chat_id.is_supergroup_or_channel()

    def mentions_user(self, username: str) -> bool:
        """Check if message mentions a user.

        Args:
            username: Username to check (with or without @)

        Returns:
            True if user is mentioned, False otherwise
        """
        return self.content.contains_mention(username)

    def preview(self, max_length: int = 50) -> str:
        """Get preview of message.

        Args:
            max_length: Maximum preview length

        Returns:
            Preview text
        """
        return self.content.preview(max_length)

    def __str__(self) -> str:
        """Return human-readable string."""
        sender = f"@{self.username}" if self.username else f"User{self.user_id}"
        preview = self.content.preview(30)
        return f"Message({sender}: {preview})"
