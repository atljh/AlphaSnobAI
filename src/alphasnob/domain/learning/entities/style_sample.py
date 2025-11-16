"""Style sample entity."""

from datetime import datetime
from typing import Optional

from alphasnob.domain.shared.base_entity import Entity


class StyleSample(Entity):
    """Sample of owner's writing style.

    Used for style analysis and learning to mimic owner's communication patterns.

    Examples:
        sample = StyleSample(
            text="Omega, you're so basic even tap water looks sophisticated.",
            source="manual",
            language="en",
        )

    Attributes:
        text: Sample text
        source: Source of sample ("manual", "auto_collected", "imported")
        language: Language code (e.g., "en", "ru")
        character_count: Number of characters
        word_count: Number of words
        collected_at: When sample was collected
        is_verified: Whether sample is verified as owner's style
    """

    text: str
    source: str = "manual"
    language: Optional[str] = None
    character_count: int
    word_count: int
    collected_at: datetime
    is_verified: bool = True

    def __init__(self, text: str, **kwargs):  # type: ignore
        """Initialize style sample with text analysis.

        Args:
            text: Sample text
            **kwargs: Additional fields
        """
        # Calculate counts
        character_count = len(text)
        word_count = len(text.split())
        collected_at = kwargs.pop("collected_at", datetime.now())

        super().__init__(
            text=text,
            character_count=character_count,
            word_count=word_count,
            collected_at=collected_at,
            **kwargs,
        )

    def mark_verified(self) -> None:
        """Mark sample as verified.

        Side effects:
            - Sets is_verified to True
            - Marks entity as updated
        """
        self.is_verified = True
        self.mark_updated()

    def mark_unverified(self) -> None:
        """Mark sample as unverified.

        Side effects:
            - Sets is_verified to False
            - Marks entity as updated
        """
        self.is_verified = False
        self.mark_updated()

    def preview(self, max_length: int = 50) -> str:
        """Get preview of sample text.

        Args:
            max_length: Maximum preview length

        Returns:
            Truncated text
        """
        if len(self.text) <= max_length:
            return self.text
        return self.text[: max_length - 3] + "..."

    def __str__(self) -> str:
        """Return human-readable string."""
        preview = self.preview(30)
        return f"StyleSample({self.source}, {self.word_count} words): {preview}"
