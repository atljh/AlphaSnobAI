"""User profile entity - complete user information with relationships."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import Field

from alphasnob.domain.shared.base_entity import Entity
from alphasnob.domain.shared.errors import InvalidOperationError
from alphasnob.domain.users.value_objects.relationship import Relationship, RelationshipLevel
from alphasnob.domain.users.value_objects.trust_score import TrustScore

if TYPE_CHECKING:
    from alphasnob.domain.users.value_objects.user_id import UserId


class UserProfile(Entity):
    """Complete user profile with relationship and interaction history.

    This is an aggregate root that manages:
    - User relationship with bot
    - Trust score
    - Interaction statistics
    - Conversation topics
    - Preferences

    Business rules are enforced through methods, not direct property access.

    Examples:
        profile = UserProfile(
            user_id=UserId(123456789),
            username="johndoe",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
        )
        profile.record_interaction()
        profile.adjust_trust(0.1)
        profile.try_upgrade_relationship()

    Attributes:
        user_id: Telegram user ID
        username: Telegram username
        first_name: First name
        last_name: Last name (optional)
        relationship: Current relationship level
        trust_score: Trust score (0.0-1.0)
        interaction_count: Total interactions
        positive_interactions: Count of positive interactions
        negative_interactions: Count of negative interactions
        detected_topics: Topics discussed with user
        preferred_persona: Preferred bot persona mode
        notes: Admin notes about user
        first_interaction: When user first interacted
        last_interaction: When user last interacted
    """

    user_id: UserId
    username: str | None = None
    first_name: str = "Unknown"
    last_name: str | None = None

    # Relationship & Trust
    relationship: Relationship
    trust_score: TrustScore

    # Statistics
    interaction_count: int = 0
    positive_interactions: int = 0
    negative_interactions: int = 0

    # Context
    detected_topics: list[str] = Field(default_factory=list)
    preferred_persona: str | None = None
    notes: str = ""

    # Timestamps
    first_interaction: datetime | None = None
    last_interaction: datetime | None = None

    def record_interaction(self, *, is_positive: bool = True) -> None:
        """Record an interaction with this user.

        Args:
            is_positive: Whether interaction was positive (True) or negative (False)

        Side effects:
            - Increments interaction count
            - Updates positive/negative counters
            - Updates last_interaction timestamp
            - Sets first_interaction if this is first time
        """
        self.interaction_count += 1

        if is_positive:
            self.positive_interactions += 1
        else:
            self.negative_interactions += 1

        now = datetime.now(UTC)
        if self.first_interaction is None:
            self.first_interaction = now
        self.last_interaction = now

        self.mark_updated()

    def adjust_trust(self, delta: float) -> None:
        """Adjust trust score.

        Args:
            delta: Amount to adjust (-1.0 to 1.0)

        Side effects:
            - Updates trust_score
            - Marks entity as updated
        """
        self.trust_score = self.trust_score.adjust(delta)
        self.mark_updated()

    def try_upgrade_relationship(self) -> bool:
        """Attempt to upgrade relationship based on interaction history.

        Business rules:
            - Requires >= 10 interactions
            - Positive interaction rate >= 80%
            - Trust score >= 0.6
            - Current relationship allows upgrade

        Returns:
            True if relationship was upgraded, False otherwise

        Side effects:
            - May upgrade relationship level
            - Marks entity as updated if upgraded
        """
        # Check if eligible for upgrade
        if self.interaction_count < 10:  # noqa: PLR2004
            return False

        positive_rate = self.positive_interactions / self.interaction_count
        if positive_rate < 0.8:  # noqa: PLR2004
            return False

        if self.trust_score.value < 0.6:  # noqa: PLR2004
            return False

        # Determine target level
        current_level = self.relationship.level
        target_level: RelationshipLevel | None = None

        if current_level == RelationshipLevel.STRANGER:
            target_level = RelationshipLevel.ACQUAINTANCE
        elif current_level == RelationshipLevel.ACQUAINTANCE:
            target_level = RelationshipLevel.FRIEND
        elif current_level == RelationshipLevel.FRIEND:
            target_level = RelationshipLevel.CLOSE_FRIEND

        if target_level is None:
            return False  # Already at max level

        # Check if upgrade is allowed
        if not self.relationship.can_upgrade_to(target_level):
            return False

        # Perform upgrade
        self.relationship = Relationship(level=target_level)
        self.mark_updated()
        return True

    def set_relationship(self, level: RelationshipLevel) -> None:
        """Manually set relationship level (admin action).

        Args:
            level: New relationship level

        Raises:
            InvalidOperationError: If trying to set OWNER for non-owner

        Side effects:
            - Updates relationship
            - Marks entity as updated
        """
        # Validate owner status (should be set through special method)
        if level == RelationshipLevel.OWNER:
            msg = "Cannot manually set OWNER status, use promote_to_owner()"
            raise InvalidOperationError(
                msg,
                user_id=str(self.user_id),
            )

        self.relationship = Relationship(level=level)
        self.mark_updated()

    def promote_to_owner(self) -> None:
        """Promote user to OWNER (special admin action).

        This should only be called after proper authorization checks.

        Side effects:
            - Sets relationship to OWNER
            - Sets trust to 1.0
            - Marks entity as updated
        """
        self.relationship = Relationship(level=RelationshipLevel.OWNER)
        self.trust_score = TrustScore(1.0)
        self.mark_updated()

    def block(self, reason: str = "") -> None:
        """Block this user.

        Args:
            reason: Reason for blocking

        Side effects:
            - Sets relationship to BLOCKED
            - Sets trust to 0.0
            - Adds reason to notes
            - Marks entity as updated
        """
        self.relationship = Relationship(level=RelationshipLevel.BLOCKED)
        self.trust_score = TrustScore(0.0)
        if reason:
            self.notes = f"Blocked: {reason}\n{self.notes}"
        self.mark_updated()

    def unblock(self) -> None:
        """Unblock this user.

        Side effects:
            - Resets to STRANGER relationship
            - Resets trust to 0.5 (neutral)
            - Marks entity as updated
        """
        if self.relationship.level != RelationshipLevel.BLOCKED:
            msg = "Cannot unblock user that is not blocked"
            raise InvalidOperationError(
                msg,
                user_id=str(self.user_id),
            )

        self.relationship = Relationship(level=RelationshipLevel.STRANGER)
        self.trust_score = TrustScore(0.5)
        self.mark_updated()

    def add_topic(self, topic: str) -> None:
        """Add detected conversation topic.

        Args:
            topic: Topic name

        Side effects:
            - Adds topic if not already present
            - Marks entity as updated
        """
        if topic not in self.detected_topics:
            self.detected_topics.append(topic)
            self.mark_updated()

    def set_preferred_persona(self, persona: str) -> None:
        """Set user's preferred bot persona.

        Args:
            persona: Persona mode name

        Side effects:
            - Updates preferred_persona
            - Marks entity as updated
        """
        self.preferred_persona = persona
        self.mark_updated()

    def is_owner(self) -> bool:
        """Check if user is bot owner.

        Returns:
            True if relationship is OWNER, False otherwise
        """
        return self.relationship.level == RelationshipLevel.OWNER

    def is_blocked(self) -> bool:
        """Check if user is blocked.

        Returns:
            True if relationship is BLOCKED, False otherwise
        """
        return self.relationship.level == RelationshipLevel.BLOCKED

    def can_interact(self) -> bool:
        """Check if bot can interact with this user.

        Returns:
            True if not blocked, False otherwise
        """
        return self.relationship.can_interact()

    def add_detected_topic(self, topic: str) -> None:
        """Add a detected conversation topic.

        Args:
            topic: Topic name to add

        Side effects:
            - Adds topic to detected_topics if not already present
        """
        if topic not in self.detected_topics:
            self.detected_topics.append(topic)
            self.mark_updated()

    def get_positive_interaction_rate(self) -> float:
        """Get rate of positive interactions.

        Returns:
            Ratio of positive to total interactions (0.0-1.0), or 0.0 if no interactions
        """
        if self.interaction_count == 0:
            return 0.0
        return self.positive_interactions / self.interaction_count

    def __str__(self) -> str:
        """Return human-readable string."""
        name = f"@{self.username}" if self.username else self.first_name
        return f"UserProfile({name}, {self.relationship.level.value})"
