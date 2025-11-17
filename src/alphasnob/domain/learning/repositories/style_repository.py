"""Style repository interface (port)."""

from typing import Protocol
from uuid import UUID

from alphasnob.domain.learning.entities.style_analysis import StyleAnalysis
from alphasnob.domain.learning.entities.style_sample import StyleSample


class StyleSampleRepository(Protocol):
    """Repository interface for style sample persistence.

    Samples can be stored in:
    - Text files (one sample per line)
    - Database
    - Hybrid approach
    """

    async def get_by_id(self, sample_id: UUID) -> StyleSample | None:
        """Get sample by internal UUID.

        Args:
            sample_id: Internal entity UUID

        Returns:
            StyleSample if found, None otherwise
        """
        ...

    async def save(self, sample: StyleSample) -> None:
        """Save or update sample.

        Args:
            sample: StyleSample entity to save
        """
        ...

    async def delete(self, sample: StyleSample) -> None:
        """Delete sample.

        Args:
            sample: StyleSample entity to delete
        """
        ...

    async def find_all(self, *, verified_only: bool = True) -> list[StyleSample]:
        """Get all samples.

        Args:
            verified_only: Whether to return only verified samples

        Returns:
            List of StyleSample entities
        """
        ...

    async def find_by_source(self, source: str) -> list[StyleSample]:
        """Get samples by source.

        Args:
            source: Source type ("manual", "auto_collected", etc.)

        Returns:
            List of StyleSample entities
        """
        ...

    async def find_by_language(self, language: str) -> list[StyleSample]:
        """Get samples by language.

        Args:
            language: Language code (e.g., "en", "ru")

        Returns:
            List of StyleSample entities
        """
        ...

    async def count(self, *, verified_only: bool = True) -> int:
        """Count total samples.

        Args:
            verified_only: Whether to count only verified samples

        Returns:
            Total sample count
        """
        ...

    async def clear_all(self, source: str | None = None) -> None:
        """Clear all samples or samples from specific source.

        Args:
            source: Optional source filter
        """
        ...


class StyleAnalysisRepository(Protocol):
    """Repository interface for style analysis persistence.

    Typically only one analysis exists at a time (latest).
    """

    async def get_latest(self) -> StyleAnalysis | None:
        """Get latest style analysis.

        Returns:
            Latest StyleAnalysis if exists, None otherwise
        """
        ...

    async def save(self, analysis: StyleAnalysis) -> None:
        """Save analysis (replaces existing).

        Args:
            analysis: StyleAnalysis entity to save
        """
        ...

    async def exists(self) -> bool:
        """Check if analysis exists.

        Returns:
            True if analysis exists, False otherwise
        """
        ...
