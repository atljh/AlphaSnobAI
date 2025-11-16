"""User DTOs."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserProfileDTO(BaseModel):
    """Data transfer object for UserProfile entity."""

    model_config = ConfigDict(frozen=True)

    id: str  # UUID as string
    user_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    relationship_level: str
    trust_score: float
    interaction_count: int
    positive_interactions: int
    negative_interactions: int
    detected_topics: list[str] = []
    preferred_persona: Optional[str] = None
    notes: str = ""
    first_interaction: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
