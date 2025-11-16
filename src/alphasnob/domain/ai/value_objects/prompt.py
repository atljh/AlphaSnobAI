"""Prompt value object."""

from alphasnob.domain.shared.base_value_object import ValueObject
from alphasnob.domain.shared.errors import ValidationError


class Prompt(ValueObject):
    """LLM prompt text.

    Encapsulates prompt text with validation and utility methods.

    Examples:
        prompt = Prompt(
            "You are a helpful assistant. Respond to the user's message: {message}"
        )
        formatted = prompt.format(message="Hello!")

    Validation:
        - Must not be empty
        - Maximum length to prevent token limit issues
    """

    text: str

    def __init__(self, text: str) -> None:
        """Initialize prompt with validation.

        Args:
            text: Prompt text

        Raises:
            ValidationError: If prompt is empty or too long
        """
        if not text.strip():
            raise ValidationError("Prompt cannot be empty")

        # Rough limit to prevent context window issues
        # (actual token limit depends on model, this is characters)
        if len(text) > 50000:
            raise ValidationError(
                "Prompt exceeds maximum length",
                length=len(text),
            )

        super().__init__(text=text)

    def format(self, **kwargs: str | int | float) -> "Prompt":
        """Format prompt with variables.

        Args:
            **kwargs: Variables to substitute in prompt

        Returns:
            New Prompt with formatted text

        Examples:
            prompt = Prompt("Hello, {name}!")
            formatted = prompt.format(name="Alice")
            # Prompt("Hello, Alice!")
        """
        formatted_text = self.text.format(**kwargs)
        return Prompt(formatted_text)

    def token_estimate(self) -> int:
        """Estimate token count (rough approximation).

        Returns:
            Estimated token count (chars / 4)

        Note:
            This is a very rough estimate. Actual tokenization
            depends on the specific model and tokenizer.
        """
        return len(self.text) // 4

    def __str__(self) -> str:
        """Return prompt text."""
        return self.text

    def __len__(self) -> int:
        """Return prompt length in characters."""
        return len(self.text)
