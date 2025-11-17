"""Integration tests for UserProfileRepository."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from alphasnob.domain.users.entities.user_profile import UserProfile
from alphasnob.domain.users.value_objects.relationship import Relationship, RelationshipLevel
from alphasnob.domain.users.value_objects.trust_score import TrustScore
from alphasnob.domain.users.value_objects.user_id import UserId
from alphasnob.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserProfileRepository,
)


@pytest.mark.asyncio
class TestSQLAlchemyUserProfileRepository:
    """Integration tests for SQLAlchemy user profile repository."""

    async def test_save_and_get_user_profile(self, test_session: AsyncSession) -> None:
        """Test saving and retrieving user profile."""
        repository = SQLAlchemyUserProfileRepository(test_session)

        # Create user profile
        user_id = UserId(123456789)
        profile = UserProfile(
            user_id=user_id,
            username="test_user",
            first_name="Test",
            last_name="User",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
            interaction_count=10,
            positive_interactions=8,
            negative_interactions=2,
            detected_topics=["music", "coding"],
            last_interaction=datetime.now(UTC),
            is_blocked=False,
        )

        # Save
        await repository.save(profile)
        await test_session.commit()

        # Retrieve
        retrieved = await repository.get_by_user_id(user_id)

        assert retrieved is not None
        assert retrieved.user_id == user_id
        assert retrieved.username == "test_user"
        assert retrieved.first_name == "Test"
        assert retrieved.last_name == "User"
        assert retrieved.relationship.level == RelationshipLevel.STRANGER
        assert retrieved.trust_score.value == 0.5
        assert retrieved.interaction_count == 10
        assert retrieved.positive_interactions == 8
        assert retrieved.negative_interactions == 2
        assert "music" in retrieved.detected_topics
        assert "coding" in retrieved.detected_topics
        assert retrieved.is_blocked is False

    async def test_update_user_profile(self, test_session: AsyncSession) -> None:
        """Test updating existing user profile."""
        repository = SQLAlchemyUserProfileRepository(test_session)

        user_id = UserId(987654321)
        profile = UserProfile(
            user_id=user_id,
            username="original",
            first_name="Original",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.3),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        # Save original
        await repository.save(profile)
        await test_session.commit()

        # Modify and save again
        profile.record_interaction(is_positive=True)
        profile.adjust_trust(0.2)
        await repository.save(profile)
        await test_session.commit()

        # Retrieve and verify
        updated = await repository.get_by_user_id(user_id)
        assert updated is not None
        assert updated.interaction_count == 1
        assert updated.positive_interactions == 1
        assert updated.trust_score.value == 0.5

    async def test_get_nonexistent_user(self, test_session: AsyncSession) -> None:
        """Test retrieving non-existent user."""
        repository = SQLAlchemyUserProfileRepository(test_session)

        result = await repository.get_by_user_id(UserId(999999999))
        assert result is None

    async def test_get_or_create_new_user(self, test_session: AsyncSession) -> None:
        """Test get_or_create for new user."""
        repository = SQLAlchemyUserProfileRepository(test_session)

        user_id = UserId(111222333)
        profile = await repository.get_or_create(
            user_id=user_id,
            username="newuser",
            first_name="New",
            last_name="User",
        )

        assert profile is not None
        assert profile.user_id == user_id
        assert profile.username == "newuser"
        assert profile.relationship.level == RelationshipLevel.STRANGER
        assert profile.trust_score.value == 0.5

        # Verify it was saved
        await test_session.commit()
        retrieved = await repository.get_by_user_id(user_id)
        assert retrieved is not None

    async def test_get_or_create_existing_user(self, test_session: AsyncSession) -> None:
        """Test get_or_create for existing user."""
        repository = SQLAlchemyUserProfileRepository(test_session)

        user_id = UserId(444555666)

        # Create first
        first = await repository.get_or_create(
            user_id=user_id,
            username="existing",
            first_name="Existing",
        )
        first.record_interaction(is_positive=True)
        await repository.save(first)
        await test_session.commit()

        # Try to get_or_create again
        second = await repository.get_or_create(
            user_id=user_id,
            username="different",
            first_name="Different",
        )

        # Should return existing with original data
        assert second.username == "existing"
        assert second.first_name == "Existing"
        assert second.interaction_count == 1

    async def test_list_all_profiles(self, test_session: AsyncSession) -> None:
        """Test listing all user profiles."""
        repository = SQLAlchemyUserProfileRepository(test_session)

        # Create multiple profiles
        for i in range(5):
            profile = UserProfile(
                user_id=UserId(100 + i),
                username=f"user{i}",
                first_name=f"User{i}",
                relationship=Relationship(level=RelationshipLevel.STRANGER),
                trust_score=TrustScore(0.5),
                interaction_count=0,
                positive_interactions=0,
                negative_interactions=0,
            )
            await repository.save(profile)

        await test_session.commit()

        # List all
        profiles = await repository.list_all()
        assert len(profiles) >= 5

    async def test_domain_to_model_mapping(self, test_session: AsyncSession) -> None:
        """Test complete domain to model mapping."""
        repository = SQLAlchemyUserProfileRepository(test_session)

        # Create profile with all fields
        profile = UserProfile(
            user_id=UserId(777888999),
            username="complete",
            first_name="Complete",
            last_name="User",
            relationship=Relationship(level=RelationshipLevel.CLOSE_FRIEND),
            trust_score=TrustScore(0.85),
            interaction_count=50,
            positive_interactions=45,
            negative_interactions=5,
            detected_topics=["ai", "music", "code"],
            last_interaction=datetime.now(UTC),
            is_blocked=False,
        )

        await repository.save(profile)
        await test_session.commit()

        # Retrieve and verify all fields
        retrieved = await repository.get_by_user_id(UserId(777888999))
        assert retrieved is not None
        assert retrieved.id == profile.id
        assert retrieved.user_id == profile.user_id
        assert retrieved.username == profile.username
        assert retrieved.first_name == profile.first_name
        assert retrieved.last_name == profile.last_name
        assert retrieved.relationship == profile.relationship
        assert retrieved.trust_score == profile.trust_score
        assert retrieved.interaction_count == profile.interaction_count
        assert retrieved.positive_interactions == profile.positive_interactions
        assert retrieved.negative_interactions == profile.negative_interactions
        assert retrieved.detected_topics == profile.detected_topics
        assert retrieved.is_blocked == profile.is_blocked

    async def test_relationship_upgrade_persistence(
        self,
        test_session: AsyncSession,
    ) -> None:
        """Test that relationship upgrades are persisted correctly."""
        repository = SQLAlchemyUserProfileRepository(test_session)

        profile = UserProfile(
            user_id=UserId(333444555),
            username="upgrader",
            first_name="Upgrader",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.8),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        # Record enough positive interactions to upgrade
        for _ in range(15):
            profile.record_interaction(is_positive=True)

        # Try upgrade
        upgraded = profile.try_upgrade_relationship()
        assert upgraded is True
        assert profile.relationship.level == RelationshipLevel.ACQUAINTANCE

        # Save
        await repository.save(profile)
        await test_session.commit()

        # Verify upgrade was persisted
        retrieved = await repository.get_by_user_id(UserId(333444555))
        assert retrieved is not None
        assert retrieved.relationship.level == RelationshipLevel.ACQUAINTANCE
        assert retrieved.interaction_count == 15
        assert retrieved.positive_interactions == 15
