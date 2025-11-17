"""Style analysis entity (aggregate root)."""

from dataclasses import field
from datetime import UTC, datetime

from alphasnob.domain.learning.value_objects.formality_score import FormalityScore
from alphasnob.domain.shared.base_entity import Entity


class StyleAnalysis(Entity):
    """Analysis of owner's writing style.

    Aggregate root that encapsulates the results of analyzing
    owner's message samples.

    This contains statistical and linguistic analysis used for
    generating responses in owner's style.

    Examples:
        analysis = StyleAnalysis(
            sample_count=100,
            avg_message_length=45.3,
            avg_sentence_length=12.5,
            formality_score=FormalityScore(0.3),
            emoji_frequency=0.85,
            common_words=["omega", "basic", "sophisticated"],
            common_phrases=["you're so basic", "tap water"],
        )

    Attributes:
        sample_count: Number of samples analyzed
        avg_message_length: Average message length (words)
        avg_sentence_length: Average sentence length (words)
        formality_score: Formality score
        emoji_frequency: Emoji usage frequency (0.0-1.0)
        common_words: Most common words
        common_phrases: Most common phrases
        language_distribution: Language distribution (e.g., {"en": 0.7, "ru": 0.3})
        analyzed_at: When analysis was performed
    """

    sample_count: int
    avg_message_length: float
    avg_sentence_length: float
    formality_score: FormalityScore
    emoji_frequency: float
    common_words: list[str] = field(default_factory=list)
    common_phrases: list[str] = field(default_factory=list)
    language_distribution: dict[str, float] = field(default_factory=dict)
    analyzed_at: datetime

    def __init__(self, **kwargs: object) -> None:
        """Initialize style analysis.

        Args:
            **kwargs: Analysis fields
        """
        analyzed_at = kwargs.pop("analyzed_at", datetime.now(UTC))
        super().__init__(analyzed_at=analyzed_at, **kwargs)  # type: ignore[call-arg, arg-type]

    def is_sufficient(self, min_samples: int = 50) -> bool:
        """Check if analysis has sufficient samples.

        Args:
            min_samples: Minimum required samples

        Returns:
            True if sample_count >= min_samples, False otherwise
        """
        return self.sample_count >= min_samples

    def get_primary_language(self) -> str | None:
        """Get primary language (most common).

        Returns:
            Language code or None if no languages
        """
        if not self.language_distribution:
            return None

        return max(self.language_distribution.items(), key=lambda x: x[1])[0]

    def get_style_summary(self) -> str:
        """Get human-readable style summary.

        Returns:
            Multi-line summary
        """
        lines = [
            f"Samples analyzed: {self.sample_count}",
            f"Avg message length: {self.avg_message_length:.1f} words",
            f"Avg sentence length: {self.avg_sentence_length:.1f} words",
            f"Formality: {self.formality_score}",
            f"Emoji frequency: {self.emoji_frequency:.0%}",
        ]

        if self.common_words:
            lines.append(f"Common words: {', '.join(self.common_words[:5])}")

        if self.language_distribution:
            primary_lang = self.get_primary_language()
            percentage = self.language_distribution.get(primary_lang or "", 0)
            lines.append(f"Primary language: {primary_lang} ({percentage:.0%})")

        return "\n".join(lines)

    def __str__(self) -> str:
        """Return human-readable string."""
        return (
            f"StyleAnalysis({self.sample_count} samples, "
            f"{self.formality_score.get_label().lower()})"
        )
