"""Tests for UserProfile entity."""

from alphasnob.domain.users.entities.user_profile import UserProfile
from alphasnob.domain.users.value_objects.relationship import Relationship, RelationshipLevel
from alphasnob.domain.users.value_objects.trust_score import TrustScore
from alphasnob.domain.users.value_objects.user_id import UserId


class TestUserProfile:
    """Tests for UserProfile entity."""

    def test_create_user_profile(self) -> None:
        """Test creating user profile."""
        user_id = UserId(123456789)
        profile = UserProfile(
            user_id=user_id,
            username="test_user",
            first_name="Test",
            last_name="User",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
            detected_topics=[],
            last_interaction=None,
            is_blocked=False,
        )

        assert profile.user_id == user_id
        assert profile.username == "test_user"
        assert profile.relationship.level == RelationshipLevel.STRANGER
        assert profile.trust_score.value == 0.5
        assert profile.interaction_count == 0

    def test_record_positive_interaction(self) -> None:
        """Test recording positive interaction."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        profile.record_interaction(is_positive=True)

        assert profile.interaction_count == 1
        assert profile.positive_interactions == 1
        assert profile.negative_interactions == 0
        assert profile.last_interaction is not None

    def test_record_negative_interaction(self) -> None:
        """Test recording negative interaction."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.FRIEND),
            trust_score=TrustScore(0.7),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        profile.record_interaction(is_positive=False)

        assert profile.interaction_count == 1
        assert profile.positive_interactions == 0
        assert profile.negative_interactions == 1

    def test_adjust_trust_positive(self) -> None:
        """Test adjusting trust positively."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        old_score = profile.trust_score.value
        profile.adjust_trust(0.2)

        assert profile.trust_score.value == old_score + 0.2

    def test_adjust_trust_negative(self) -> None:
        """Test adjusting trust negatively."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.FRIEND),
            trust_score=TrustScore(0.7),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        old_score = profile.trust_score.value
        profile.adjust_trust(-0.3)

        assert profile.trust_score.value == old_score - 0.3

    def test_try_upgrade_relationship_not_enough_interactions(self) -> None:
        """Test relationship upgrade with insufficient interactions."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.9),
            interaction_count=5,  # Less than 10 required
            positive_interactions=5,
            negative_interactions=0,
        )

        upgraded = profile.try_upgrade_relationship()
        assert upgraded is False
        assert profile.relationship.level == RelationshipLevel.STRANGER

    def test_try_upgrade_relationship_low_positive_rate(self) -> None:
        """Test relationship upgrade with low positive interaction rate."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.9),
            interaction_count=20,
            positive_interactions=10,  # Only 50%, need 80%
            negative_interactions=10,
        )

        upgraded = profile.try_upgrade_relationship()
        assert upgraded is False
        assert profile.relationship.level == RelationshipLevel.STRANGER

    def test_try_upgrade_relationship_low_trust(self) -> None:
        """Test relationship upgrade with low trust score."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.4),  # Below 0.6 threshold
            interaction_count=20,
            positive_interactions=18,
            negative_interactions=2,
        )

        upgraded = profile.try_upgrade_relationship()
        assert upgraded is False
        assert profile.relationship.level == RelationshipLevel.STRANGER

    def test_try_upgrade_relationship_success(self) -> None:
        """Test successful relationship upgrade."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.8),
            interaction_count=15,
            positive_interactions=14,  # 93% positive
            negative_interactions=1,
        )

        upgraded = profile.try_upgrade_relationship()
        assert upgraded is True
        assert profile.relationship.level == RelationshipLevel.ACQUAINTANCE

    def test_block_user(self) -> None:
        """Test blocking user."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.FRIEND),
            trust_score=TrustScore(0.7),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        profile.block()

        assert profile.is_blocked is True
        assert profile.relationship.level == RelationshipLevel.BLOCKED

    def test_unblock_user(self) -> None:
        """Test unblocking user."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.BLOCKED),
            trust_score=TrustScore(0.3),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
            is_blocked=True,
        )

        profile.unblock()

        assert profile.is_blocked is False
        assert profile.relationship.level == RelationshipLevel.STRANGER

    def test_add_detected_topic(self) -> None:
        """Test adding detected topic."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
            detected_topics=[],
        )

        profile.add_detected_topic("music")
        assert "music" in profile.detected_topics

        # Should not add duplicates
        profile.add_detected_topic("music")
        assert profile.detected_topics.count("music") == 1

    def test_get_positive_interaction_rate(self) -> None:
        """Test getting positive interaction rate."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
            interaction_count=10,
            positive_interactions=8,
            negative_interactions=2,
        )

        rate = profile.get_positive_interaction_rate()
        assert rate == 0.8

    def test_get_positive_interaction_rate_no_interactions(self) -> None:
        """Test getting positive rate with no interactions."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        rate = profile.get_positive_interaction_rate()
        assert rate == 0.0

    def test_entity_identity(self) -> None:
        """Test entity identity based on ID."""
        user_id = UserId(123)
        profile1 = UserProfile(
            user_id=user_id,
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        # Create another profile with same UUID
        profile2 = UserProfile(
            id=profile1.id,  # Same ID
            user_id=UserId(456),  # Different user_id
            username="different",
            first_name="Different",
            relationship=Relationship(level=RelationshipLevel.FRIEND),
            trust_score=TrustScore(0.8),
            interaction_count=10,
            positive_interactions=10,
            negative_interactions=0,
        )

        # Should be equal based on entity ID
        assert profile1 == profile2

    def test_mark_updated(self) -> None:
        """Test marking entity as updated."""
        profile = UserProfile(
            user_id=UserId(123),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        original_updated_at = profile.updated_at
        profile.mark_updated()

        assert profile.updated_at > original_updated_at
