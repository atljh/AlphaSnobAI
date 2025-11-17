"""Decision engine domain service.

This is a domain service - it contains business logic that doesn't
naturally belong to any single entity.
"""

import random

from alphasnob.domain.decisions.entities.decision import Decision
from alphasnob.domain.decisions.value_objects.decision_factors import DecisionFactors
from alphasnob.domain.decisions.value_objects.probability import Probability
from alphasnob.domain.messaging.entities.message import Message
from alphasnob.domain.users.entities.user_profile import UserProfile


class DecisionEngine:
    """Domain service for making response decisions.

    This service encapsulates the core business logic for deciding
    whether the bot should respond to a message.

    It's a domain service (not application service) because it contains
    pure business logic with no external dependencies.

    Examples:
        engine = DecisionEngine(base_probability=0.3)
        decision = engine.make_decision(message, user_profile)

    Business rules:
        1. Always respond to owner
        2. Always respond in private chats (unless blocked)
        3. Higher probability for trusted users
        4. Higher probability for direct mentions
        5. Time-based adjustments
        6. Topic-based adjustments
        7. Cooldown prevents spam
    """

    def __init__(self, base_probability: float = 0.3):
        """Initialize decision engine.

        Args:
            base_probability: Base response probability (0.0-1.0)
        """
        self.base_probability = Probability(base_probability)

    def make_decision(
        self,
        message: Message,
        user_profile: UserProfile,
        *,
        bot_username: str | None = None,
        cooldown_active: bool = False,
    ) -> Decision:
        """Make decision on whether to respond to message.

        Args:
            message: Incoming message
            user_profile: User's profile
            bot_username: Bot's username (for mention detection)
            cooldown_active: Whether cooldown is active for this chat

        Returns:
            Decision entity with reasoning
        """
        # Build decision factors
        factors = self._build_factors(
            message=message,
            user_profile=user_profile,
            bot_username=bot_username,
            cooldown_active=cooldown_active,
        )

        # Check for forced responses
        if factors.should_force_response():
            probability = Probability(1.0)
            should_respond = True
            reasoning = self._explain_forced_response(factors)
        # Check for blocked responses
        elif factors.should_block_response():
            probability = Probability(0.0)
            should_respond = False
            reasoning = self._explain_blocked_response(factors)
        # Calculate probability-based decision
        else:
            probability = self._calculate_probability(factors)
            should_respond = self._roll_dice(probability)
            reasoning = self._explain_probability_decision(factors, probability)

        # Select persona mode
        persona_mode = self._select_persona(user_profile)

        # Estimate response delay
        estimated_delay_ms = self._estimate_delay() if should_respond else None

        return Decision(
            message_id=message.id,
            should_respond=should_respond,
            probability=probability,
            factors=factors,
            reasoning=reasoning,
            persona_mode=persona_mode,
            estimated_delay_ms=estimated_delay_ms,
        )

    def _build_factors(
        self,
        message: Message,
        user_profile: UserProfile,
        *,
        bot_username: str | None,
        cooldown_active: bool,
    ) -> DecisionFactors:
        """Build decision factors from message and user profile.

        Args:
            message: Incoming message
            user_profile: User's profile
            bot_username: Bot's username
            cooldown_active: Whether cooldown is active

        Returns:
            DecisionFactors with all multipliers
        """
        # Relationship multiplier
        relationship_multiplier = user_profile.relationship.response_multiplier()

        # Trust multiplier
        trust_multiplier = user_profile.trust_score.multiplier()

        # Mention multiplier
        mention_multiplier = 1.0
        if bot_username and message.mentions_user(bot_username):
            mention_multiplier = 2.0

        # Reply multiplier (embedded in is_reply_to_bot)
        is_reply_to_bot = False
        # TODO: Check if message is reply to bot's message
        # This requires checking replied_to_id against bot's messages

        return DecisionFactors(
            relationship_multiplier=relationship_multiplier,
            trust_multiplier=trust_multiplier,
            mention_multiplier=mention_multiplier,
            is_private_chat=message.is_in_private_chat(),
            is_reply_to_bot=is_reply_to_bot,
            cooldown_active=cooldown_active,
        )

    def _calculate_probability(self, factors: DecisionFactors) -> Probability:
        """Calculate final probability from factors.

        Args:
            factors: Decision factors

        Returns:
            Final probability
        """
        total_multiplier = factors.compute_total_multiplier()
        final_value = self.base_probability.value * total_multiplier

        # Clamp to valid range
        final_value = max(0.0, min(1.0, final_value))

        return Probability(final_value)

    def _roll_dice(self, probability: Probability) -> bool:
        """Roll dice to make random decision based on probability.

        Args:
            probability: Probability of True

        Returns:
            True or False based on random roll
        """
        return random.random() < probability.value  # noqa: S311 # nosec B311

    def _select_persona(self, user_profile: UserProfile) -> str:
        """Select persona mode for response.

        Args:
            user_profile: User's profile

        Returns:
            Persona mode name
        """
        # Use preferred persona if set
        if user_profile.preferred_persona:
            return user_profile.preferred_persona

        # Owner gets owner persona
        if user_profile.is_owner():
            return "owner"

        # Default persona
        return "alphasnob"

    def _estimate_delay(self) -> int:
        """Estimate response delay in milliseconds.

        Returns:
            Random delay between 1000-5000ms
        """
        return random.randint(1000, 5000)  # noqa: S311 # nosec B311

    def _explain_forced_response(self, factors: DecisionFactors) -> str:
        """Explain why response is forced.

        Args:
            factors: Decision factors

        Returns:
            Explanation string
        """
        reasons = []

        if factors.is_private_chat:
            reasons.append("private chat")
        if factors.mention_multiplier > 1.5:  # noqa: PLR2004
            reasons.append("directly mentioned")
        if factors.is_reply_to_bot:
            reasons.append("reply to bot")

        return f"Forced response: {', '.join(reasons)}"

    def _explain_blocked_response(self, factors: DecisionFactors) -> str:
        """Explain why response is blocked.

        Args:
            factors: Decision factors

        Returns:
            Explanation string
        """
        if factors.cooldown_active:
            return "Blocked: cooldown active"
        if factors.relationship_multiplier == 0.0:
            return "Blocked: user is blocked"
        return "Blocked: unknown reason"

    def _explain_probability_decision(
        self,
        factors: DecisionFactors,
        probability: Probability,
    ) -> str:
        """Explain probability-based decision.

        Args:
            factors: Decision factors
            probability: Final probability

        Returns:
            Explanation string
        """
        multiplier = factors.compute_total_multiplier()
        return f"Probability {probability.as_percentage()} (base={self.base_probability.as_percentage()}, multiplier={multiplier:.2f}x)"
