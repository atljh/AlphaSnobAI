"""Decision factors value object."""

from typing import Optional

from alphasnob.domain.shared.base_value_object import ValueObject


class DecisionFactors(ValueObject):
    """Factors that influence response decision.

    Encapsulates all factors considered when deciding whether to respond
    to a message and how.

    Examples:
        factors = DecisionFactors(
            relationship_multiplier=0.9,  # close friend
            trust_multiplier=1.2,         # high trust
            time_multiplier=0.8,          # late night
            topic_multiplier=1.1,         # interesting topic
            mention_multiplier=2.0,       # directly mentioned
            is_private_chat=False,
            is_reply_to_bot=False,
        )

    Attributes:
        relationship_multiplier: Based on user relationship (0.0-1.0)
        trust_multiplier: Based on trust score (0.5-1.5)
        time_multiplier: Based on time of day (0.5-1.2)
        topic_multiplier: Based on conversation topic (0.8-1.5)
        mention_multiplier: Multiplier if bot is mentioned (1.0-2.0)
        is_private_chat: Whether message is in private chat
        is_reply_to_bot: Whether message replies to bot
        cooldown_active: Whether cooldown is active for this chat
    """

    relationship_multiplier: float
    trust_multiplier: float
    time_multiplier: float = 1.0
    topic_multiplier: float = 1.0
    mention_multiplier: float = 1.0
    is_private_chat: bool = False
    is_reply_to_bot: bool = False
    cooldown_active: bool = False

    def compute_total_multiplier(self) -> float:
        """Compute total multiplier from all factors.

        Returns:
            Total multiplier (product of all factors)

        Business rules:
            - If cooldown active, return 0.0 (no response)
            - Otherwise, multiply all factors together
        """
        if self.cooldown_active:
            return 0.0

        return (
            self.relationship_multiplier
            * self.trust_multiplier
            * self.time_multiplier
            * self.topic_multiplier
            * self.mention_multiplier
        )

    def should_force_response(self) -> bool:
        """Check if factors should force a response.

        Returns:
            True if bot should definitely respond, False otherwise

        Business rules:
            - Always respond in private chats
            - Always respond to direct mentions
            - Always respond to replies
        """
        if self.cooldown_active:
            return False

        return (
            self.is_private_chat or self.mention_multiplier > 1.5 or self.is_reply_to_bot
        )

    def should_block_response(self) -> bool:
        """Check if factors should block response.

        Returns:
            True if bot should definitely not respond, False otherwise

        Business rules:
            - Block if cooldown is active
            - Block if relationship multiplier is 0.0 (blocked user)
        """
        return self.cooldown_active or self.relationship_multiplier == 0.0

    def get_explanation(self) -> str:
        """Get human-readable explanation of factors.

        Returns:
            Multi-line explanation of decision factors
        """
        lines = [
            f"Relationship: {self.relationship_multiplier:.2f}x",
            f"Trust: {self.trust_multiplier:.2f}x",
            f"Time: {self.time_multiplier:.2f}x",
            f"Topic: {self.topic_multiplier:.2f}x",
            f"Mention: {self.mention_multiplier:.2f}x",
        ]

        if self.is_private_chat:
            lines.append("Private chat: Yes (force response)")
        if self.is_reply_to_bot:
            lines.append("Reply to bot: Yes (force response)")
        if self.cooldown_active:
            lines.append("Cooldown: Active (block response)")

        lines.append(f"Total multiplier: {self.compute_total_multiplier():.2f}x")

        return "\n".join(lines)

    def __str__(self) -> str:
        """String representation with total multiplier."""
        total = self.compute_total_multiplier()
        return f"DecisionFactors(total={total:.2f}x)"
