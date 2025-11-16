"""LLM response value object."""

from typing import Optional

from alphasnob.domain.shared.base_value_object import ValueObject
from alphasnob.domain.shared.errors import ValidationError


class LLMResponse(ValueObject):
    """Response from LLM with metadata.

    Encapsulates the generated text along with metadata about generation.

    Examples:
        response = LLMResponse(
            text="Hello! How can I help you?",
            model="claude-3-5-sonnet-20241022",
            tokens_used=25,
            finish_reason="stop",
        )

    Attributes:
        text: Generated response text
        model: Model that generated response
        tokens_used: Number of tokens used (input + output)
        finish_reason: Why generation stopped (stop, length, etc.)
    """

    text: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None

    def __init__(
        self,
        text: str,
        model: str,
        tokens_used: Optional[int] = None,
        finish_reason: Optional[str] = None,
    ) -> None:
        """Initialize LLM response with validation.

        Args:
            text: Generated text
            model: Model name
            tokens_used: Token count (optional)
            finish_reason: Finish reason (optional)

        Raises:
            ValidationError: If text is empty
        """
        if not text.strip():
            raise ValidationError("LLM response text cannot be empty")

        super().__init__(
            text=text,
            model=model,
            tokens_used=tokens_used,
            finish_reason=finish_reason,
        )

    def is_complete(self) -> bool:
        """Check if response completed normally.

        Returns:
            True if finish_reason is 'stop' or 'end_turn', False otherwise
        """
        return self.finish_reason in ("stop", "end_turn", None)

    def was_truncated(self) -> bool:
        """Check if response was truncated due to length.

        Returns:
            True if finish_reason is 'length', False otherwise
        """
        return self.finish_reason == "length"

    def __str__(self) -> str:
        """Return response text."""
        return self.text

    def __len__(self) -> int:
        """Return response length in characters."""
        return len(self.text)
