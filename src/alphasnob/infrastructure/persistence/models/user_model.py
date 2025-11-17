"""SQLAlchemy model for User and UserProfile."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from alphasnob.infrastructure.persistence.database import Base


class UserProfileModel(Base):
    """SQLAlchemy model for UserProfile table.

    Maps to domain UserProfile entity.
    """

    __tablename__ = "user_profiles"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Telegram user info
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationship & Trust
    relationship_level: Mapped[str] = mapped_column(String(50))
    trust_score: Mapped[float] = mapped_column(Float)

    # Statistics
    interaction_count: Mapped[int] = mapped_column(Integer, default=0)
    positive_interactions: Mapped[int] = mapped_column(Integer, default=0)
    negative_interactions: Mapped[int] = mapped_column(Integer, default=0)

    # Context
    detected_topics: Mapped[str] = mapped_column(Text, default="")  # JSON array as string
    preferred_persona: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    # Timestamps
    first_interaction: Mapped[datetime | None] = mapped_column(nullable=True)
    last_interaction: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserProfileModel(user_id={self.user_id}, username={self.username})>"
