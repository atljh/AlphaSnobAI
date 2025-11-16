import logging
import random
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

from config.settings import DecisionConfig
from services.user_profiler import UserProfile
from services.memory import Message

logger = logging.getLogger(__name__)


@dataclass
class DecisionResult:
    should_respond: bool
    final_probability: float
    base_probability: float
    relationship_multiplier: float
    time_multiplier: float
    topic_multiplier: float
    cooldown_block: bool
    reasoning: str

    def __repr__(self):
        return f"DecisionResult(respond={self.should_respond}, p={self.final_probability:.2f})"


class DecisionEngine:

    def __init__(self, decision_config: DecisionConfig):
        self.config = decision_config
        logger.info(f"DecisionEngine initialized (base_p={self.config.base_probability})")

    def should_respond(
        self,
        user_profile: UserProfile,
        message_text: str,
        current_time: datetime,
        recent_bot_messages: List[Message],
        bot_user_id: int
    ) -> DecisionResult:
        """
        Main decision function. Analyzes multiple factors to determine if bot should respond.

        Args:
            user_profile: Profile of the user sending the message
            message_text: The incoming message text
            current_time: Current timestamp
            recent_bot_messages: Recent messages from the bot (for cooldown)
            bot_user_id: Bot's user ID for filtering messages

        Returns:
            DecisionResult with decision and detailed reasoning
        """
        base_p = self.config.base_probability
        reasoning_parts = []

        # 1. Relationship multiplier
        relationship_mult = self._get_relationship_multiplier(user_profile.relationship_level)
        reasoning_parts.append(
            f"relationship={user_profile.relationship_level} ({relationship_mult}x)"
        )

        # 2. Time-based multiplier
        time_mult = self._get_time_multiplier(current_time)
        if time_mult < 1.0:
            reasoning_parts.append(f"quiet_hours ({time_mult}x)")
        else:
            reasoning_parts.append("active_hours (1.0x)")

        # 3. Topic-based multiplier
        topic_mult = self._get_topic_multiplier(message_text)
        if topic_mult != 1.0:
            if topic_mult > 1.0:
                reasoning_parts.append(f"interesting_topic ({topic_mult}x)")
            else:
                reasoning_parts.append(f"boring_topic ({topic_mult}x)")
        else:
            reasoning_parts.append("neutral_topic (1.0x)")

        # 4. Cooldown check
        cooldown_blocked = False
        if self.config.cooldown.enabled:
            cooldown_result = self._check_cooldown(recent_bot_messages, current_time, bot_user_id)
            if cooldown_result:
                cooldown_blocked = True
                reasoning_parts.append(f"BLOCKED: {cooldown_result}")

        # Calculate final probability
        final_p = base_p * relationship_mult * time_mult * topic_mult

        # Clamp to 0.0-1.0
        final_p = max(0.0, min(1.0, final_p))

        # Random decision
        random_value = random.random()
        should_respond = (random_value <= final_p) and not cooldown_blocked

        # Build reasoning string
        reasoning = (
            f"base={base_p:.2f} × " + " × ".join(reasoning_parts) +
            f" = {final_p:.2f} | random={random_value:.2f} | "
            f"{'RESPOND' if should_respond else 'SKIP'}"
        )

        logger.info(f"Decision: {reasoning}")

        return DecisionResult(
            should_respond=should_respond,
            final_probability=final_p,
            base_probability=base_p,
            relationship_multiplier=relationship_mult,
            time_multiplier=time_mult,
            topic_multiplier=topic_mult,
            cooldown_block=cooldown_blocked,
            reasoning=reasoning
        )

    def _get_relationship_multiplier(self, relationship_level: str) -> float:
        """Get probability multiplier based on relationship level."""
        multiplier = self.config.relationship_multipliers.get(relationship_level, 0.5)
        logger.debug(f"Relationship multiplier for '{relationship_level}': {multiplier}")
        return multiplier

    def _get_time_multiplier(self, current_time: datetime) -> float:
        """Get probability multiplier based on time of day."""
        current_hour = current_time.hour

        quiet_start = self.config.time_based.quiet_hours_start
        quiet_end = self.config.time_based.quiet_hours_end

        # Handle overnight quiet hours (e.g., 23-8)
        if quiet_start > quiet_end:
            # Overnight span: 23-8 means 23,0,1,2,3,4,5,6,7
            is_quiet = current_hour >= quiet_start or current_hour < quiet_end
        else:
            # Same-day span: 8-23
            is_quiet = quiet_start <= current_hour < quiet_end

        if is_quiet:
            multiplier = self.config.time_based.quiet_hours_multiplier
            logger.debug(f"Quiet hours detected (hour={current_hour}): {multiplier}x")
            return multiplier
        else:
            logger.debug(f"Active hours (hour={current_hour}): 1.0x")
            return 1.0

    def _get_topic_multiplier(self, message_text: str) -> float:
        """Get probability multiplier based on detected topics in message."""
        message_lower = message_text.lower()

        # Check for boring topics
        for boring_topic in self.config.topic_based.boring_topics:
            if boring_topic.lower() in message_lower:
                multiplier = self.config.topic_based.boring_multiplier
                logger.debug(f"Boring topic detected '{boring_topic}': {multiplier}x")
                return multiplier

        # Check for interesting topics
        for interesting_topic in self.config.topic_based.interesting_topics:
            if interesting_topic.lower() in message_lower:
                multiplier = self.config.topic_based.interesting_multiplier
                logger.debug(f"Interesting topic detected '{interesting_topic}': {multiplier}x")
                return multiplier

        # Neutral topic
        logger.debug("Neutral topic: 1.0x")
        return 1.0

    def _check_cooldown(
        self,
        recent_bot_messages: List[Message],
        current_time: datetime,
        bot_user_id: int
    ) -> Optional[str]:
        """
        Check cooldown rules to prevent spamming.

        Returns:
            None if cooldown passed, or string reason if cooldown blocks response
        """
        if not recent_bot_messages:
            return None

        # Filter to only bot's own messages
        bot_messages = [msg for msg in recent_bot_messages if msg.user_id == bot_user_id]

        if not bot_messages:
            return None

        # Get most recent bot message
        last_bot_msg = max(bot_messages, key=lambda m: m.timestamp)

        # Check minimum time between responses
        time_since_last = (current_time - last_bot_msg.timestamp).total_seconds()
        min_seconds = self.config.cooldown.min_seconds_between_responses

        if time_since_last < min_seconds:
            return f"cooldown ({time_since_last:.0f}s < {min_seconds}s required)"

        # Check consecutive response limit
        max_consecutive = self.config.cooldown.max_consecutive_responses
        reset_after = self.config.cooldown.reset_after_seconds

        # Count consecutive bot messages within reset window
        cutoff_time = current_time - timedelta(seconds=reset_after)
        recent_consecutive = [
            msg for msg in bot_messages
            if msg.timestamp >= cutoff_time
        ]

        if len(recent_consecutive) >= max_consecutive:
            return f"consecutive_limit ({len(recent_consecutive)}/{max_consecutive})"

        # All checks passed
        return None

    def get_decision_summary(self, result: DecisionResult) -> str:
        """Generate human-readable summary of decision."""
        return f"""Decision Summary:
- Final Probability: {result.final_probability:.1%}
  - Base: {result.base_probability:.1%}
  - Relationship: {result.relationship_multiplier}x
  - Time: {result.time_multiplier}x
  - Topic: {result.topic_multiplier}x
- Cooldown Block: {result.cooldown_block}
- Decision: {'RESPOND' if result.should_respond else 'SKIP'}
- Reasoning: {result.reasoning}
"""
