"""Tests for user domain value objects."""

import pytest
from pydantic import ValidationError as PydanticValidationError

from alphasnob.domain.shared.errors import ValidationError
from alphasnob.domain.users.value_objects.relationship import Relationship, RelationshipLevel
from alphasnob.domain.users.value_objects.trust_score import TrustScore
from alphasnob.domain.users.value_objects.user_id import UserId


class TestUserId:
    """Tests for UserId value object."""

    def test_create_valid_user_id(self) -> None:
        """Test creating valid user ID."""
        user_id = UserId(123456789)
        assert user_id.value == 123456789

    def test_reject_negative_user_id(self) -> None:
        """Test rejecting negative user ID."""
        with pytest.raises(ValidationError, match="must be positive"):
            UserId(-1)

    def test_reject_zero_user_id(self) -> None:
        """Test rejecting zero user ID."""
        with pytest.raises(ValidationError, match="must be positive"):
            UserId(0)

    def test_reject_too_large_user_id(self) -> None:
        """Test rejecting too large user ID."""
        with pytest.raises(ValidationError, match="exceeds maximum"):
            UserId(99_999_999_999)

    def test_user_id_equality(self) -> None:
        """Test user ID equality."""
        user_id1 = UserId(123)
        user_id2 = UserId(123)
        user_id3 = UserId(456)

        assert user_id1 == user_id2
        assert user_id1 != user_id3

    def test_user_id_immutability(self) -> None:
        """Test that user ID is immutable."""
        user_id = UserId(123)
        with pytest.raises((PydanticValidationError, AttributeError)):
            user_id.value = 456  # type: ignore

    def test_user_id_hashable(self) -> None:
        """Test that user ID is hashable."""
        user_id1 = UserId(123)
        user_id2 = UserId(123)
        user_id3 = UserId(456)

        assert hash(user_id1) == hash(user_id2)
        assert hash(user_id1) != hash(user_id3)

        # Can be used in sets
        user_ids = {user_id1, user_id2, user_id3}
        assert len(user_ids) == 2


class TestTrustScore:
    """Tests for TrustScore value object."""

    def test_create_valid_trust_score(self) -> None:
        """Test creating valid trust score."""
        trust_score = TrustScore(0.5)
        assert trust_score.value == 0.5

    def test_create_minimum_trust_score(self) -> None:
        """Test creating minimum trust score."""
        trust_score = TrustScore(0.0)
        assert trust_score.value == 0.0

    def test_create_maximum_trust_score(self) -> None:
        """Test creating maximum trust score."""
        trust_score = TrustScore(1.0)
        assert trust_score.value == 1.0

    def test_reject_negative_trust_score(self) -> None:
        """Test rejecting negative trust score."""
        with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
            TrustScore(-0.1)

    def test_reject_too_high_trust_score(self) -> None:
        """Test rejecting trust score above 1.0."""
        with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
            TrustScore(1.1)

    def test_trust_score_adjustment(self) -> None:
        """Test adjusting trust score."""
        trust_score = TrustScore(0.5)

        increased = trust_score.adjust(0.2)
        assert increased.value == 0.7

        decreased = trust_score.adjust(-0.3)
        assert decreased.value == 0.2

    def test_trust_score_clamping(self) -> None:
        """Test trust score clamping to valid range."""
        trust_score = TrustScore(0.9)

        # Should clamp to 1.0
        clamped_high = trust_score.adjust(0.5)
        assert clamped_high.value == 1.0

        # Should clamp to 0.0
        low_score = TrustScore(0.1)
        clamped_low = low_score.adjust(-0.5)
        assert clamped_low.value == 0.0

    def test_trust_score_immutability(self) -> None:
        """Test that trust score is immutable."""
        trust_score = TrustScore(0.5)
        with pytest.raises((PydanticValidationError, AttributeError)):
            trust_score.value = 0.8  # type: ignore


class TestRelationship:
    """Tests for Relationship value object."""

    def test_create_relationship(self) -> None:
        """Test creating relationship."""
        relationship = Relationship(level=RelationshipLevel.FRIEND)
        assert relationship.level == RelationshipLevel.FRIEND

    def test_all_relationship_levels(self) -> None:
        """Test all relationship levels can be created."""
        levels = [
            RelationshipLevel.OWNER,
            RelationshipLevel.CLOSE_FRIEND,
            RelationshipLevel.FRIEND,
            RelationshipLevel.ACQUAINTANCE,
            RelationshipLevel.STRANGER,
            RelationshipLevel.BLOCKED,
        ]

        for level in levels:
            relationship = Relationship(level=level)
            assert relationship.level == level

    def test_response_multipliers(self) -> None:
        """Test response multipliers for each relationship level."""
        multipliers = {
            RelationshipLevel.OWNER: 1.0,
            RelationshipLevel.CLOSE_FRIEND: 0.9,
            RelationshipLevel.FRIEND: 0.7,
            RelationshipLevel.ACQUAINTANCE: 0.5,
            RelationshipLevel.STRANGER: 0.3,
            RelationshipLevel.BLOCKED: 0.0,
        }

        for level, expected_multiplier in multipliers.items():
            relationship = Relationship(level=level)
            assert relationship.response_multiplier() == expected_multiplier

    def test_can_upgrade_to(self) -> None:
        """Test relationship upgrade validation."""
        stranger = Relationship(level=RelationshipLevel.STRANGER)

        # Can upgrade from stranger to acquaintance
        assert stranger.can_upgrade_to(RelationshipLevel.ACQUAINTANCE) is True

        # Cannot upgrade from stranger to friend (must go through acquaintance)
        assert stranger.can_upgrade_to(RelationshipLevel.FRIEND) is False

        # Cannot upgrade to owner
        assert stranger.can_upgrade_to(RelationshipLevel.OWNER) is False

    def test_upgrade_to(self) -> None:
        """Test upgrading relationship."""
        relationship = Relationship(level=RelationshipLevel.STRANGER)

        # Valid upgrade
        upgraded = relationship.upgrade_to(RelationshipLevel.ACQUAINTANCE)
        assert upgraded.level == RelationshipLevel.ACQUAINTANCE

        # Original is unchanged (immutable)
        assert relationship.level == RelationshipLevel.STRANGER

    def test_upgrade_to_invalid_level(self) -> None:
        """Test upgrading to invalid level."""
        relationship = Relationship(level=RelationshipLevel.STRANGER)

        with pytest.raises(ValidationError, match="Cannot upgrade"):
            relationship.upgrade_to(RelationshipLevel.FRIEND)

    def test_is_blocked(self) -> None:
        """Test checking if relationship is blocked."""
        blocked = Relationship(level=RelationshipLevel.BLOCKED)
        friend = Relationship(level=RelationshipLevel.FRIEND)

        assert blocked.is_blocked() is True
        assert friend.is_blocked() is False

    def test_is_owner(self) -> None:
        """Test checking if relationship is owner."""
        owner = Relationship(level=RelationshipLevel.OWNER)
        friend = Relationship(level=RelationshipLevel.FRIEND)

        assert owner.is_owner() is True
        assert friend.is_owner() is False

    def test_relationship_immutability(self) -> None:
        """Test that relationship is immutable."""
        relationship = Relationship(level=RelationshipLevel.FRIEND)
        with pytest.raises((PydanticValidationError, AttributeError)):
            relationship.level = RelationshipLevel.CLOSE_FRIEND  # type: ignore
