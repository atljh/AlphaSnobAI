"""User ID value object."""

from alphasnob.domain.shared.base_value_object import ValueObject
from alphasnob.domain.shared.errors import ValidationError


class UserId(ValueObject):
    """Telegram user ID.

    User IDs in Telegram are positive integers.
    We wrap them in a value object for type safety and validation.

    Examples:
        user_id = UserId(123456789)
        user_id.value  # 123456789

    Validation:
        - Must be positive integer
        - Must be within Telegram's valid range
    """

    value: int

    def __init__(self, value: int) -> None:
        """Initialize user ID with validation.

        Args:
            value: Telegram user ID

        Raises:
            ValidationError: If user ID is invalid
        """
        if value <= 0:
            msg = "User ID must be positive"
            raise ValidationError(
                msg,
                user_id=value,
            )

        # Telegram user IDs are typically < 10 billion
        if value > 10_000_000_000:  # noqa: PLR2004
            msg = "User ID exceeds maximum value"
            raise ValidationError(
                msg,
                user_id=value,
            )

        super().__init__(value=value)  # type: ignore[call-arg]

    def __int__(self) -> int:
        """Allow conversion to int."""
        return self.value

    def __str__(self) -> str:
        """String representation is just the ID value."""
        return str(self.value)
