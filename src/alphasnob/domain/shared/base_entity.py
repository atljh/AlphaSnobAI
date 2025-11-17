"""Base Entity class for all domain entities.

Entities are objects that have an identity that runs through time and different states.
They are defined not by their attributes, but by their identity.
"""

from datetime import UTC, datetime
from typing import ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class Entity(BaseModel):
    """Base class for all domain entities.

    Entities have:
    - Unique identity (id)
    - Lifecycle (created_at, updated_at)
    - Equality based on identity, not attributes
    - Mutable state (unlike Value Objects)

    Examples:
        User, Message, Chat, Persona

    Usage:
        class User(Entity):
            user_id: int
            username: str
            relationship_level: str
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=False,  # Entities are mutable
        validate_assignment=True,  # Validate on attribute assignment
        arbitrary_types_allowed=True,  # Allow custom types
        extra="forbid",  # Forbid extra attributes
    )

    id: UUID = Field(default_factory=uuid4, description="Unique entity identifier")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last update timestamp",
    )

    def __eq__(self, other: object) -> bool:
        """Entities are equal if they have the same ID."""
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts."""
        return hash(self.id)

    def mark_updated(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(UTC)

    def __repr__(self) -> str:
        """Return detailed string representation."""
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.model_dump().items() if k != "id")
        return f"{self.__class__.__name__}(id={self.id!r}, {attrs})"
