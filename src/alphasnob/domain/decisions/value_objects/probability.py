"""Probability value object."""

from alphasnob.domain.shared.base_value_object import ValueObject
from alphasnob.domain.shared.errors import ValidationError


class Probability(ValueObject):
    """Probability value (0.0 to 1.0).

    Represents likelihood of an event or decision.

    Examples:
        never = Probability(0.0)
        unlikely = Probability(0.3)
        likely = Probability(0.7)
        always = Probability(1.0)

    Validation:
        - Must be between 0.0 and 1.0 (inclusive)
    """

    value: float

    def __init__(self, value: float) -> None:
        """Initialize probability with validation.

        Args:
            value: Probability between 0.0 and 1.0

        Raises:
            ValidationError: If value is out of range
        """
        if not 0.0 <= value <= 1.0:
            raise ValidationError(
                "Probability must be between 0.0 and 1.0",
                value=value,
            )

        super().__init__(value=value)

    def is_certain(self) -> bool:
        """Check if probability is 1.0 (certain).

        Returns:
            True if value is 1.0, False otherwise
        """
        return self.value == 1.0

    def is_impossible(self) -> bool:
        """Check if probability is 0.0 (impossible).

        Returns:
            True if value is 0.0, False otherwise
        """
        return self.value == 0.0

    def is_likely(self) -> bool:
        """Check if probability is > 0.5 (more likely than not).

        Returns:
            True if value > 0.5, False otherwise
        """
        return self.value > 0.5

    def complement(self) -> "Probability":
        """Get complement probability (1 - p).

        Returns:
            New Probability representing complement

        Examples:
            p = Probability(0.3)
            p.complement()  # Probability(0.7)
        """
        return Probability(1.0 - self.value)

    def multiply(self, other: "Probability" | float) -> "Probability":
        """Multiply with another probability.

        Args:
            other: Probability or float to multiply with

        Returns:
            New Probability with product (clamped to 0.0-1.0)

        Examples:
            p1 = Probability(0.8)
            p2 = Probability(0.5)
            p1.multiply(p2)  # Probability(0.4)
        """
        if isinstance(other, Probability):
            value = self.value * other.value
        else:
            value = self.value * other

        # Clamp to valid range
        value = max(0.0, min(1.0, value))
        return Probability(value)

    def as_percentage(self) -> str:
        """Get probability as percentage string.

        Returns:
            Percentage string (e.g., "75%")
        """
        return f"{self.value:.0%}"

    def __float__(self) -> float:
        """Allow conversion to float."""
        return self.value

    def __str__(self) -> str:
        """String representation as percentage."""
        return self.as_percentage()
