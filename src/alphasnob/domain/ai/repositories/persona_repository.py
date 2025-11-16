"""Persona repository interface (port)."""

from typing import Optional, Protocol
from uuid import UUID

from alphasnob.domain.ai.entities.persona import Persona


class PersonaRepository(Protocol):
    """Repository interface for persona persistence.

    Personas can be stored in:
    - YAML files (static configuration)
    - Database (runtime modifications)
    - Hybrid (load from YAML, modify in DB)

    Infrastructure layer decides implementation strategy.
    """

    async def get_by_id(self, id: UUID) -> Optional[Persona]:
        """Get persona by internal UUID.

        Args:
            id: Internal entity UUID

        Returns:
            Persona if found, None otherwise
        """
        ...

    async def get_by_name(self, name: str) -> Optional[Persona]:
        """Get persona by name.

        Args:
            name: Persona name (e.g., "alphasnob", "normal", "owner")

        Returns:
            Persona if found, None otherwise
        """
        ...

    async def save(self, persona: Persona) -> None:
        """Save or update persona.

        Args:
            persona: Persona entity to save
        """
        ...

    async def delete(self, persona: Persona) -> None:
        """Delete persona.

        Args:
            persona: Persona entity to delete
        """
        ...

    async def find_all_active(self) -> list[Persona]:
        """Get all active personas.

        Returns:
            List of active Persona entities
        """
        ...

    async def find_all(self) -> list[Persona]:
        """Get all personas (active and inactive).

        Returns:
            List of all Persona entities
        """
        ...

    async def get_default(self) -> Persona:
        """Get default persona.

        Returns:
            Default persona (typically "alphasnob" or "normal")

        Raises:
            EntityNotFoundError: If no default persona exists
        """
        ...

    async def exists(self, name: str) -> bool:
        """Check if persona exists by name.

        Args:
            name: Persona name

        Returns:
            True if persona exists, False otherwise
        """
        ...
