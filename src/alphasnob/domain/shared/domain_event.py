"""Domain Events for event-driven architecture.

Domain events represent something that happened in the domain that
domain experts care about. They are immutable facts about the past.
"""

from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DomainEvent(BaseModel):
    """Base class for all domain events.

    Domain Events have:
    - Unique ID
    - Timestamp when event occurred
    - Immutability (facts about the past)
    - Rich domain information

    Examples:
        MessageReceived, UserProfileUpdated, DecisionMade, StyleAnalyzed

    Usage:
        class MessageReceived(DomainEvent):
            message_id: UUID
            chat_id: int
            user_id: int
            text: str
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,  # Events are immutable
        validate_assignment=True,
        arbitrary_types_allowed=True,
        extra="forbid",
    )

    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the event occurred",
    )
    event_version: int = Field(default=1, description="Event schema version")

    def __repr__(self) -> str:
        """Return detailed string representation."""
        attrs = ", ".join(
            f"{k}={v!r}"
            for k, v in self.model_dump().items()
            if k not in ("event_id", "occurred_at", "event_version")
        )
        return (
            f"{self.__class__.__name__}("
            f"event_id={self.event_id!r}, "
            f"occurred_at={self.occurred_at.isoformat()}, "
            f"{attrs})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.__class__.__name__,
            "event_id": str(self.event_id),
            "occurred_at": self.occurred_at.isoformat(),
            "event_version": self.event_version,
            "data": {
                k: v
                for k, v in self.model_dump().items()
                if k not in ("event_id", "occurred_at", "event_version")
            },
        }
