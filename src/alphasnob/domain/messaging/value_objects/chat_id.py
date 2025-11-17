"""Chat ID value object."""

from alphasnob.domain.shared.base_value_object import ValueObject
from alphasnob.domain.shared.errors import ValidationError


class ChatId(ValueObject):
    """Telegram chat ID.

    Chat IDs in Telegram can be:
    - Positive: user chats (private messages)
    - Negative: group chats
    - Very negative: supergroups/channels (-100...)

    Examples:
        private_chat = ChatId(123456789)  # Private chat
        group_chat = ChatId(-987654321)   # Group chat
        supergroup = ChatId(-1001234567890)  # Supergroup

    Validation:
        - Must be non-zero integer
        - Must be within Telegram's valid range
    """

    value: int

    def __init__(self, value: int) -> None:
        """Initialize chat ID with validation.

        Args:
            value: Telegram chat ID

        Raises:
            ValidationError: If chat ID is invalid
        """
        if value == 0:
            msg = "Chat ID cannot be zero"
            raise ValidationError(msg, chat_id=value)

        # Telegram chat IDs typically don't exceed these ranges
        if value > 10_000_000_000:  # noqa: PLR2004
            msg = "Chat ID exceeds maximum value"
            raise ValidationError(msg, chat_id=value)

        if value < -10_000_000_000_000:  # noqa: PLR2004
            msg = "Chat ID below minimum value"
            raise ValidationError(msg, chat_id=value)

        super().__init__(value=value)  # type: ignore[call-arg]

    def is_private(self) -> bool:
        """Check if this is a private chat.

        Returns:
            True if positive (user chat), False otherwise
        """
        return self.value > 0

    def is_group(self) -> bool:
        """Check if this is a group chat.

        Returns:
            True if negative but not supergroup, False otherwise
        """
        return self.value < 0 and self.value > -1000000000000  # noqa: PLR2004

    def is_supergroup_or_channel(self) -> bool:
        """Check if this is a supergroup or channel.

        Returns:
            True if very negative (-100...), False otherwise
        """
        return self.value <= -1000000000000  # noqa: PLR2004

    def __int__(self) -> int:
        """Allow conversion to int."""
        return self.value

    def __str__(self) -> str:
        """String representation is just the ID value."""
        return str(self.value)
