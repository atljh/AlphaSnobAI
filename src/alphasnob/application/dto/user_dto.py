"""User DTOs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserProfileDTO(BaseModel):
    """Data transfer object for UserProfile entity."""

    model_config = ConfigDict(frozen=True)

    id: str  # UUID as string
    user_id: int
    username: str | None = None
    first_name: str
    last_name: str | None = None
    relationship_level: str
    trust_score: float
    interaction_count: int
    positive_interactions: int
    negative_interactions: int
    detected_topics: list[str] = []
    preferred_persona: str | None = None
    notes: str = ""
    first_interaction: datetime | None = None
    last_interaction: datetime | None = None
