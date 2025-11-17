"""Temperature value object for LLM generation."""

from alphasnob.domain.shared.base_value_object import ValueObject
from alphasnob.domain.shared.errors import ValidationError


class Temperature(ValueObject):
    """LLM temperature parameter (0.0 to 2.0).

    Temperature controls randomness in LLM responses:
    - 0.0: Deterministic, focused, conservative
    - 0.5-0.7: Balanced (recommended for most cases)
    - 0.9-1.0: Creative, varied
    - 1.5-2.0: Very creative, experimental, chaotic

    Examples:
        conservative = Temperature(0.3)
        balanced = Temperature(0.7)
        creative = Temperature(1.2)

    Validation:
        - Must be between 0.0 and 2.0
    """

    value: float

    def __init__(self, value: float) -> None:
        """Initialize temperature with validation.

        Args:
            value: Temperature between 0.0 and 2.0

        Raises:
            ValidationError: If value is out of range
        """
        if not 0.0 <= value <= 2.0:  # noqa: PLR2004
            msg = "Temperature must be between 0.0 and 2.0"
            raise ValidationError(
                msg,
                value=value,
            )

        super().__init__(value=value)  # type: ignore[call-arg]

    def is_conservative(self) -> bool:
        """Check if temperature is conservative (<= 0.3).

        Returns:
            True if conservative, False otherwise
        """
        return self.value <= 0.3  # noqa: PLR2004

    def is_balanced(self) -> bool:
        """Check if temperature is balanced (0.4-0.9).

        Returns:
            True if balanced, False otherwise
        """
        return 0.4 <= self.value <= 0.9  # noqa: PLR2004

    def is_creative(self) -> bool:
        """Check if temperature is creative (>= 1.0).

        Returns:
            True if creative, False otherwise
        """
        return self.value >= 1.0

    def __float__(self) -> float:
        """Allow conversion to float."""
        return self.value

    def __str__(self) -> str:
        """String representation."""
        return f"{self.value:.1f}"
