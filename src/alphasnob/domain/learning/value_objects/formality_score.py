"""Formality score value object."""

from alphasnob.domain.shared.base_value_object import ValueObject
from alphasnob.domain.shared.errors import ValidationError


class FormalityScore(ValueObject):
    """Formality score for text style (0.0 to 1.0).

    Measures how formal/casual the writing style is:
    - 0.0: Very casual (slang, abbreviations, emojis)
    - 0.5: Neutral
    - 1.0: Very formal (proper grammar, professional)

    Examples:
        casual = FormalityScore(0.2)  # "yo whats up lol 😂"
        neutral = FormalityScore(0.5)  # "Hey, how are you?"
        formal = FormalityScore(0.9)  # "Good evening. How are you today?"

    Validation:
        - Must be between 0.0 and 1.0
    """

    value: float

    def __init__(self, value: float) -> None:
        """Initialize formality score with validation.

        Args:
            value: Formality score between 0.0 and 1.0

        Raises:
            ValidationError: If value is out of range
        """
        if not 0.0 <= value <= 1.0:
            raise ValidationError(
                "Formality score must be between 0.0 and 1.0",
                value=value,
            )

        super().__init__(value=value)

    def is_casual(self) -> bool:
        """Check if style is casual (< 0.4).

        Returns:
            True if casual, False otherwise
        """
        return self.value < 0.4

    def is_neutral(self) -> bool:
        """Check if style is neutral (0.4-0.6).

        Returns:
            True if neutral, False otherwise
        """
        return 0.4 <= self.value <= 0.6

    def is_formal(self) -> bool:
        """Check if style is formal (> 0.6).

        Returns:
            True if formal, False otherwise
        """
        return self.value > 0.6

    def get_label(self) -> str:
        """Get human-readable label.

        Returns:
            Label: "Casual", "Neutral", or "Formal"
        """
        if self.is_casual():
            return "Casual"
        elif self.is_neutral():
            return "Neutral"
        else:
            return "Formal"

    def __float__(self) -> float:
        """Allow conversion to float."""
        return self.value

    def __str__(self) -> str:
        """String representation with label and score."""
        return f"{self.get_label()} ({self.value:.1f})"
