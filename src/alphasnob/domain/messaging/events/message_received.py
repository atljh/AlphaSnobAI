"""Message received domain event."""

from uuid import UUID

from alphasnob.domain.shared.domain_event import DomainEvent


class MessageReceived(DomainEvent):
    """Event emitted when a message is received from Telegram.

    This event triggers the message handling pipeline:
    1. User profiling
    2. Decision making
    3. Response generation
    4. Typing simulation
    5. Message sending

    Examples:
        event = MessageReceived(
            message_id=UUID(...),
            chat_id=-987654321,
            user_id=123456789,
            text="Hello bot!",
            username="johndoe",
            is_private_chat=False,
            mentions_bot=False,
        )

    Attributes:
        message_id: Internal message UUID
        chat_id: Telegram chat ID
        user_id: Telegram user ID
        text: Message text
        username: Sender username (optional)
        is_private_chat: Whether message is in private chat
        mentions_bot: Whether message mentions bot
        replied_to_bot: Whether message is reply to bot's message
    """

    message_id: UUID
    chat_id: int
    user_id: int
    text: str
    username: str | None = None
    is_private_chat: bool
    mentions_bot: bool
    replied_to_bot: bool = False
