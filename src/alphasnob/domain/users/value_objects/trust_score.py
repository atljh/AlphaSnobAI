"""Trust score value object."""

from alphasnob.domain.shared.base_value_object import ValueObject
from alphasnob.domain.shared.errors import ValidationError


class TrustScore(ValueObject):
    """User trust score (0.0 to 1.0).

    Trust score represents how much the bot trusts a user:
    - 0.0: No trust (new user, suspicious behavior)
    - 0.5: Neutral trust
    - 1.0: Complete trust (verified, long history)

    Trust score affects:
    - Response probability
    - Persona selection
    - Feature access

    Trust is earned through:
    - Positive interactions
    - Consistent behavior
    - Time
    - Owner vouching

    Trust decreases through:
    - Negative interactions
    - Suspicious patterns
    - Long inactivity

    Examples:
        trust = TrustScore(0.75)
        trust.is_trusted()  # True (>= 0.7)
        trust.adjust(0.1)  # Returns new TrustScore(0.85)
    """

    value: float

    def __init__(self, value: float) -> None:
        """Initialize trust score with validation.

        Args:
            value: Trust score between 0.0 and 1.0

        Raises:
            ValidationError: If value is out of range
        """
        if not 0.0 <= value <= 1.0:
            msg = "Trust score must be between 0.0 and 1.0"
            raise ValidationError(
                msg,
                value=value,
            )

        super().__init__(value=value)  # type: ignore[call-arg]

    def is_trusted(self) -> bool:
        """Check if user is considered trusted.

        Returns:
            True if trust score >= 0.7, False otherwise
        """
        return self.value >= 0.7  # noqa: PLR2004

    def is_suspicious(self) -> bool:
        """Check if user is considered suspicious.

        Returns:
            True if trust score < 0.3, False otherwise
        """
        return self.value < 0.3  # noqa: PLR2004

    def adjust(self, delta: float) -> "TrustScore":
        """Create new trust score with adjustment.

        Args:
            delta: Amount to adjust (-1.0 to 1.0)

        Returns:
            New TrustScore with adjusted value (clamped to 0.0-1.0)

        Examples:
            trust = TrustScore(0.5)
            new_trust = trust.adjust(0.2)  # TrustScore(0.7)
            new_trust = trust.adjust(-0.6)  # TrustScore(0.0)
        """
        new_value = max(0.0, min(1.0, self.value + delta))
        return TrustScore(new_value)

    def multiplier(self) -> float:
        """Get multiplier for decision making based on trust.

        Returns:
            Multiplier between 0.5 and 1.5
        """
        # Map 0.0-1.0 to 0.5-1.5
        return 0.5 + self.value

    def __float__(self) -> float:
        """Allow conversion to float."""
        return self.value

    def __str__(self) -> str:
        """String representation with percentage."""
        return f"{self.value:.0%}"
