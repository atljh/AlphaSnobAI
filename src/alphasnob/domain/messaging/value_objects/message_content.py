"""Message content value object."""

from alphasnob.domain.shared.base_value_object import ValueObject
from alphasnob.domain.shared.errors import ValidationError


class MessageContent(ValueObject):
    """Message text content.

    Encapsulates message text with validation and text processing capabilities.

    Examples:
        content = MessageContent("Hello, world!")
        content.is_empty()  # False
        content.word_count()  # 2
        content.contains_mention("@user")  # False

    Validation:
        - Must be string (can be empty for media messages)
        - Maximum length based on Telegram limits
    """

    text: str

    def __init__(self, text: str) -> None:
        """Initialize message content with validation.

        Args:
            text: Message text

        Raises:
            ValidationError: If text exceeds Telegram limits
        """
        # Telegram message limit is 4096 characters
        if len(text) > 4096:
            raise ValidationError(
                "Message text exceeds Telegram limit of 4096 characters",
                length=len(text),
            )

        super().__init__(text=text)

    def is_empty(self) -> bool:
        """Check if message is empty.

        Returns:
            True if text is empty or whitespace only, False otherwise
        """
        return not self.text.strip()

    def word_count(self) -> int:
        """Get word count.

        Returns:
            Number of words in text
        """
        if self.is_empty():
            return 0
        return len(self.text.split())

    def character_count(self) -> int:
        """Get character count.

        Returns:
            Number of characters
        """
        return len(self.text)

    def contains_mention(self, username: str) -> bool:
        """Check if text contains mention of username.

        Args:
            username: Username to check (with or without @)

        Returns:
            True if username is mentioned, False otherwise
        """
        username_clean = username.lstrip("@").lower()
        text_lower = self.text.lower()
        return f"@{username_clean}" in text_lower

    def contains_keyword(self, keyword: str, case_sensitive: bool = False) -> bool:
        """Check if text contains keyword.

        Args:
            keyword: Keyword to search for
            case_sensitive: Whether search is case sensitive

        Returns:
            True if keyword found, False otherwise
        """
        text = self.text if case_sensitive else self.text.lower()
        search = keyword if case_sensitive else keyword.lower()
        return search in text

    def truncate(self, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length.

        Args:
            max_length: Maximum length
            suffix: Suffix to add if truncated

        Returns:
            Truncated text
        """
        if len(self.text) <= max_length:
            return self.text

        return self.text[: max_length - len(suffix)] + suffix

    def preview(self, max_length: int = 100) -> str:
        """Get preview of message content.

        Args:
            max_length: Maximum preview length

        Returns:
            Preview text
        """
        return self.truncate(max_length)

    def __str__(self) -> str:
        """Return text content."""
        return self.text

    def __len__(self) -> int:
        """Return text length."""
        return len(self.text)
