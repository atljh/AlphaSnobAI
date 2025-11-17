"""Tests for DecisionEngine domain service."""

from datetime import UTC, datetime

from alphasnob.domain.decisions.services.decision_engine import DecisionEngine
from alphasnob.domain.messaging.entities.chat import ChatType
from alphasnob.domain.messaging.entities.message import Message
from alphasnob.domain.messaging.value_objects.chat_id import ChatId
from alphasnob.domain.messaging.value_objects.message_content import MessageContent
from alphasnob.domain.users.entities.user_profile import UserProfile
from alphasnob.domain.users.value_objects.relationship import Relationship, RelationshipLevel
from alphasnob.domain.users.value_objects.trust_score import TrustScore
from alphasnob.domain.users.value_objects.user_id import UserId


class TestDecisionEngine:
    """Tests for DecisionEngine domain service."""

    def test_create_decision_engine(self) -> None:
        """Test creating decision engine."""
        engine = DecisionEngine(base_probability=0.3)
        assert engine.base_probability.value == 0.3

    def test_force_response_for_owner(self) -> None:
        """Test forcing response for owner."""
        engine = DecisionEngine(base_probability=0.3)

        owner_profile = UserProfile(
            user_id=UserId(123),
            username="owner",
            first_name="Owner",
            relationship=Relationship(level=RelationshipLevel.OWNER),
            trust_score=TrustScore(1.0),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        message = Message(
            message_id=1,
            chat_id=ChatId(value=-123, chat_type=ChatType.PRIVATE),
            user_id=UserId(123),
            content=MessageContent("Hello"),
            timestamp=datetime.now(UTC),
        )

        decision = engine.make_decision(message, owner_profile)

        assert decision.should_respond is True
        assert decision.probability.value == 1.0
        assert "owner" in decision.reasoning.lower()

    def test_force_response_for_mention(self) -> None:
        """Test forcing response when bot is mentioned."""
        engine = DecisionEngine(base_probability=0.3)

        user_profile = UserProfile(
            user_id=UserId(123),
            username="user",
            first_name="User",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        message = Message(
            message_id=1,
            chat_id=ChatId(value=-123, chat_type=ChatType.GROUP),
            user_id=UserId(123),
            content=MessageContent("Hey @testbot, how are you?"),
            timestamp=datetime.now(UTC),
        )

        decision = engine.make_decision(
            message,
            user_profile,
            bot_username="testbot",
        )

        assert decision.should_respond is True
        assert decision.probability.value == 1.0
        assert "mentioned" in decision.reasoning.lower()

    def test_force_response_for_private_chat(self) -> None:
        """Test forcing response in private chat."""
        engine = DecisionEngine(base_probability=0.3)

        user_profile = UserProfile(
            user_id=UserId(123),
            username="user",
            first_name="User",
            relationship=Relationship(level=RelationshipLevel.FRIEND),
            trust_score=TrustScore(0.7),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        message = Message(
            message_id=1,
            chat_id=ChatId(value=123, chat_type=ChatType.PRIVATE),
            user_id=UserId(123),
            content=MessageContent("Hello"),
            timestamp=datetime.now(UTC),
        )

        decision = engine.make_decision(message, user_profile)

        assert decision.should_respond is True
        assert decision.probability.value == 1.0
        assert "private" in decision.reasoning.lower()

    def test_block_response_for_blocked_user(self) -> None:
        """Test blocking response for blocked user."""
        engine = DecisionEngine(base_probability=0.3)

        blocked_profile = UserProfile(
            user_id=UserId(123),
            username="blocked",
            first_name="Blocked",
            relationship=Relationship(level=RelationshipLevel.BLOCKED),
            trust_score=TrustScore(0.0),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
            is_blocked=True,
        )

        message = Message(
            message_id=1,
            chat_id=ChatId(value=-123, chat_type=ChatType.GROUP),
            user_id=UserId(123),
            content=MessageContent("Hello"),
            timestamp=datetime.now(UTC),
        )

        decision = engine.make_decision(message, blocked_profile)

        assert decision.should_respond is False
        assert decision.probability.value == 0.0
        assert "blocked" in decision.reasoning.lower()

    def test_block_response_for_cooldown(self) -> None:
        """Test blocking response during cooldown."""
        engine = DecisionEngine(base_probability=0.3)

        user_profile = UserProfile(
            user_id=UserId(123),
            username="user",
            first_name="User",
            relationship=Relationship(level=RelationshipLevel.ACQUAINTANCE),
            trust_score=TrustScore(0.5),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        message = Message(
            message_id=1,
            chat_id=ChatId(value=-123, chat_type=ChatType.GROUP),
            user_id=UserId(123),
            content=MessageContent("Hello"),
            timestamp=datetime.now(UTC),
        )

        decision = engine.make_decision(
            message,
            user_profile,
            cooldown_active=True,
        )

        assert decision.should_respond is False
        assert decision.probability.value == 0.0
        assert "cooldown" in decision.reasoning.lower()

    def test_probability_calculation_with_relationship(self) -> None:
        """Test probability calculation considers relationship."""
        engine = DecisionEngine(base_probability=0.5)

        # Close friend should have high multiplier (0.9)
        close_friend = UserProfile(
            user_id=UserId(123),
            username="friend",
            first_name="Friend",
            relationship=Relationship(level=RelationshipLevel.CLOSE_FRIEND),
            trust_score=TrustScore(0.8),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        message = Message(
            message_id=1,
            chat_id=ChatId(value=-123, chat_type=ChatType.GROUP),
            user_id=UserId(123),
            content=MessageContent("Hello"),
            timestamp=datetime.now(UTC),
        )

        decision = engine.make_decision(message, close_friend)

        # Probability should be influenced by relationship
        # Base 0.5 * relationship_multiplier (0.9) * trust_multiplier
        assert decision.probability.value > 0.3

    def test_probability_calculation_with_trust(self) -> None:
        """Test probability calculation considers trust score."""
        engine = DecisionEngine(base_probability=0.5)

        high_trust = UserProfile(
            user_id=UserId(123),
            username="trusted",
            first_name="Trusted",
            relationship=Relationship(level=RelationshipLevel.ACQUAINTANCE),
            trust_score=TrustScore(0.9),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        low_trust = UserProfile(
            user_id=UserId(456),
            username="untrusted",
            first_name="Untrusted",
            relationship=Relationship(level=RelationshipLevel.ACQUAINTANCE),
            trust_score=TrustScore(0.1),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        message = Message(
            message_id=1,
            chat_id=ChatId(value=-123, chat_type=ChatType.GROUP),
            user_id=UserId(123),
            content=MessageContent("Hello"),
            timestamp=datetime.now(UTC),
        )

        decision_high = engine.make_decision(message, high_trust)
        decision_low = engine.make_decision(message, low_trust)

        # Higher trust should result in higher probability
        assert decision_high.probability.value > decision_low.probability.value

    def test_decision_includes_factors(self) -> None:
        """Test that decision includes all relevant factors."""
        engine = DecisionEngine(base_probability=0.3)

        user_profile = UserProfile(
            user_id=UserId(123),
            username="user",
            first_name="User",
            relationship=Relationship(level=RelationshipLevel.FRIEND),
            trust_score=TrustScore(0.7),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        message = Message(
            message_id=1,
            chat_id=ChatId(value=-123, chat_type=ChatType.GROUP),
            user_id=UserId(123),
            content=MessageContent("Hello"),
            timestamp=datetime.now(UTC),
        )

        decision = engine.make_decision(message, user_profile)

        assert decision.factors is not None
        assert decision.factors.relationship_level == RelationshipLevel.FRIEND
        assert decision.factors.trust_score == 0.7
        assert decision.factors.is_private_chat is False

    def test_reasoning_is_descriptive(self) -> None:
        """Test that decision reasoning is descriptive."""
        engine = DecisionEngine(base_probability=0.3)

        user_profile = UserProfile(
            user_id=UserId(123),
            username="user",
            first_name="User",
            relationship=Relationship(level=RelationshipLevel.ACQUAINTANCE),
            trust_score=TrustScore(0.6),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )

        message = Message(
            message_id=1,
            chat_id=ChatId(value=-123, chat_type=ChatType.GROUP),
            user_id=UserId(123),
            content=MessageContent("Hello everyone"),
            timestamp=datetime.now(UTC),
        )

        decision = engine.make_decision(message, user_profile)

        # Reasoning should be non-empty and descriptive
        assert len(decision.reasoning) > 20
        assert decision.probability.value > 0.0
