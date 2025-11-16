"""User entity - represents a Telegram user."""

from datetime import datetime
from typing import Optional

from alphasnob.domain.shared.base_entity import Entity
from alphasnob.domain.users.value_objects.user_id import UserId


class User(Entity):
    """Telegram user entity.

    Represents basic information about a Telegram user.
    This is a lightweight entity used for identification.

    For full user information including relationships and trust,
    use UserProfile entity.

    Examples:
        user = User(
            user_id=UserId(123456789),
            username="johndoe",
            first_name="John",
            last_name="Doe"
        )

    Attributes:
        user_id: Telegram user ID
        username: Telegram username (without @)
        first_name: User's first name
        last_name: User's last name (optional)
        is_bot: Whether this user is a bot
        language_code: User's language code (e.g., "en", "ru")
    """

    user_id: UserId
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    is_bot: bool = False
    language_code: Optional[str] = None

    def full_name(self) -> str:
        """Get user's full name.

        Returns:
            Full name (first + last) or just first name
        """
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    def display_name(self) -> str:
        """Get best display name for user.

        Returns:
            Username if available, otherwise full name
        """
        if self.username:
            return f"@{self.username}"
        return self.full_name()

    def update_info(
        self,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> None:
        """Update user information.

        Args:
            username: New username
            first_name: New first name
            last_name: New last name
            language_code: New language code
        """
        if username is not None:
            self.username = username
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if language_code is not None:
            self.language_code = language_code

        self.mark_updated()

    def __str__(self) -> str:
        """Return human-readable string."""
        return f"User({self.display_name()})"
