"""SQLAlchemy implementation of UserProfileRepository.

This is an adapter that implements the domain repository interface.
"""

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from alphasnob.domain.users.entities.user_profile import UserProfile
from alphasnob.domain.users.value_objects.relationship import Relationship, RelationshipLevel
from alphasnob.domain.users.value_objects.trust_score import TrustScore
from alphasnob.domain.users.value_objects.user_id import UserId
from alphasnob.infrastructure.persistence.models.user_model import UserProfileModel


class SQLAlchemyUserProfileRepository:
    """SQLAlchemy implementation of UserProfileRepository interface.

    Handles mapping between domain UserProfile entities and
    SQLAlchemy UserProfileModel.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_by_id(self, entity_id: UUID) -> UserProfile | None:
        """Get profile by internal UUID."""
        stmt = select(UserProfileModel).where(UserProfileModel.id == entity_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    async def get_by_user_id(self, user_id: UserId) -> UserProfile | None:
        """Get profile by Telegram user ID."""
        stmt = select(UserProfileModel).where(UserProfileModel.user_id == user_id.value)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    async def get_or_create(self, user_id: UserId, **kwargs: str) -> UserProfile:
        """Get existing profile or create new one."""
        # Try to get existing
        profile = await self.get_by_user_id(user_id)

        if profile is not None:
            return profile

        # Create new profile
        profile = UserProfile(
            user_id=user_id,
            username=kwargs.get("username"),
            first_name=kwargs.get("first_name", "Unknown"),
            last_name=kwargs.get("last_name"),
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
        )

        await self.save(profile)
        return profile

    async def save(self, profile: UserProfile) -> None:
        """Save or update profile."""
        # Check if exists
        stmt = select(UserProfileModel).where(UserProfileModel.id == profile.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            # Create new
            model = self._to_model(profile)
            self.session.add(model)
        else:
            # Update existing
            self._update_model(model, profile)

        await self.session.flush()

    async def delete(self, profile: UserProfile) -> None:
        """Delete profile."""
        stmt = select(UserProfileModel).where(UserProfileModel.id == profile.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is not None:
            await self.session.delete(model)
            await self.session.flush()

    async def find_by_relationship(
        self,
        level: RelationshipLevel,
        limit: int = 100,
    ) -> list[UserProfile]:
        """Find profiles by relationship level."""
        stmt = (
            select(UserProfileModel)
            .where(UserProfileModel.relationship_level == level.value)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def find_by_trust_score(
        self,
        min_score: float,
        max_score: float,
        limit: int = 100,
    ) -> list[UserProfile]:
        """Find profiles by trust score range."""
        stmt = (
            select(UserProfileModel)
            .where(
                UserProfileModel.trust_score >= min_score,
                UserProfileModel.trust_score <= max_score,
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_owner(self) -> UserProfile | None:
        """Get bot owner profile."""
        stmt = select(UserProfileModel).where(
            UserProfileModel.relationship_level == RelationshipLevel.OWNER.value,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    async def count(self) -> int:
        """Get total number of profiles."""
        stmt = select(UserProfileModel)
        result = await self.session.execute(stmt)
        return len(result.scalars().all())

    def _to_entity(self, model: UserProfileModel) -> UserProfile:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: UserProfileModel from database

        Returns:
            UserProfile domain entity
        """
        # Parse JSON array for detected_topics
        detected_topics = json.loads(model.detected_topics) if model.detected_topics else []

        return UserProfile(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            user_id=UserId(model.user_id),
            username=model.username,
            first_name=model.first_name,
            last_name=model.last_name,
            relationship=Relationship(level=RelationshipLevel(model.relationship_level)),
            trust_score=TrustScore(model.trust_score),
            interaction_count=model.interaction_count,
            positive_interactions=model.positive_interactions,
            negative_interactions=model.negative_interactions,
            detected_topics=detected_topics,
            preferred_persona=model.preferred_persona,
            notes=model.notes,
            first_interaction=model.first_interaction,
            last_interaction=model.last_interaction,
        )

    def _to_model(self, entity: UserProfile) -> UserProfileModel:
        """Convert domain entity to SQLAlchemy model.

        Args:
            entity: UserProfile domain entity

        Returns:
            UserProfileModel for database
        """
        return UserProfileModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            user_id=entity.user_id.value,
            username=entity.username,
            first_name=entity.first_name,
            last_name=entity.last_name,
            relationship_level=entity.relationship.level.value,
            trust_score=entity.trust_score.value,
            interaction_count=entity.interaction_count,
            positive_interactions=entity.positive_interactions,
            negative_interactions=entity.negative_interactions,
            detected_topics=json.dumps(entity.detected_topics),
            preferred_persona=entity.preferred_persona,
            notes=entity.notes,
            first_interaction=entity.first_interaction,
            last_interaction=entity.last_interaction,
        )

    def _update_model(self, model: UserProfileModel, entity: UserProfile) -> None:
        """Update existing model from entity.

        Args:
            model: Existing UserProfileModel
            entity: Updated UserProfile entity
        """
        model.updated_at = entity.updated_at
        model.username = entity.username
        model.first_name = entity.first_name
        model.last_name = entity.last_name
        model.relationship_level = entity.relationship.level.value
        model.trust_score = entity.trust_score.value
        model.interaction_count = entity.interaction_count
        model.positive_interactions = entity.positive_interactions
        model.negative_interactions = entity.negative_interactions
        model.detected_topics = json.dumps(entity.detected_topics)
        model.preferred_persona = entity.preferred_persona
        model.notes = entity.notes
        model.first_interaction = entity.first_interaction
        model.last_interaction = entity.last_interaction
