"""SQLAlchemy models for Message and Chat."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from alphasnob.infrastructure.persistence.database import Base


class MessageModel(Base):
    """SQLAlchemy model for Message table."""

    __tablename__ = "messages"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Telegram message info
    message_id: Mapped[int] = mapped_column(Integer, index=True)
    chat_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(index=True)

    # Bot-specific fields
    is_from_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    persona_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    response_delay_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    decision_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Reply chain
    replied_to_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        """String representation."""
        return f"<MessageModel(message_id={self.message_id}, chat_id={self.chat_id})>"


class ChatModel(Base):
    """SQLAlchemy model for Chat table."""

    __tablename__ = "chats"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Telegram chat info
    chat_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chat_type: Mapped[str] = mapped_column(String(50))
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Statistics
    member_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    last_message_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ChatModel(chat_id={self.chat_id}, title={self.title})>"
