"""Message DTOs."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MessageDTO(BaseModel):
    """Data transfer object for Message entity.

    Used to transfer message data between layers without exposing
    domain entity internals.
    """

    model_config = ConfigDict(frozen=True)

    id: str  # UUID as string
    message_id: int
    chat_id: int
    user_id: int
    text: str
    username: Optional[str] = None
    timestamp: datetime
    is_from_bot: bool = False
    persona_mode: Optional[str] = None


class ChatDTO(BaseModel):
    """Data transfer object for Chat entity."""

    model_config = ConfigDict(frozen=True)

    id: str  # UUID as string
    chat_id: int
    title: Optional[str] = None
    chat_type: str
    username: Optional[str] = None
    is_active: bool = True
