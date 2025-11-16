"""Relationship level value object."""

from enum import Enum

from alphasnob.domain.shared.base_value_object import ValueObject


class RelationshipLevel(str, Enum):
    """Relationship levels between bot and users.

    These levels determine how the bot interacts with different users:
    - OWNER: Bot owner, full access and control
    - CLOSE_FRIEND: Trusted user, high response rate
    - FRIEND: Known user, moderate response rate
    - ACQUAINTANCE: Occasional contact, low response rate
    - STRANGER: Unknown user, minimal interaction
    - BLOCKED: User is blocked, no interaction

    The relationship level can be upgraded automatically based on interaction patterns.
    """

    OWNER = "owner"
    CLOSE_FRIEND = "close_friend"
    FRIEND = "friend"
    ACQUAINTANCE = "acquaintance"
    STRANGER = "stranger"
    BLOCKED = "blocked"

    def __str__(self) -> str:
        """Return human-readable name."""
        return self.value.replace("_", " ").title()

    @property
    def priority(self) -> int:
        """Return priority level (higher = more important).

        Used for decision making and sorting.
        """
        priorities = {
            RelationshipLevel.OWNER: 100,
            RelationshipLevel.CLOSE_FRIEND: 90,
            RelationshipLevel.FRIEND: 70,
            RelationshipLevel.ACQUAINTANCE: 50,
            RelationshipLevel.STRANGER: 30,
            RelationshipLevel.BLOCKED: 0,
        }
        return priorities[self]


class Relationship(ValueObject):
    """Relationship with user.

    Encapsulates the relationship level and provides business logic
    for relationship management.

    Examples:
        rel = Relationship(level=RelationshipLevel.FRIEND)
        rel.can_interact()  # True
        rel.response_multiplier()  # 0.7

    Business Rules:
        - OWNER always gets responses
        - BLOCKED never gets responses
        - Other levels have different response multipliers
    """

    level: RelationshipLevel

    def can_interact(self) -> bool:
        """Check if bot should interact with this relationship level.

        Returns:
            True if interaction is allowed, False otherwise
        """
        return self.level != RelationshipLevel.BLOCKED

    def response_multiplier(self) -> float:
        """Get response probability multiplier for this relationship.

        Returns:
            Multiplier between 0.0 and 1.0
        """
        multipliers = {
            RelationshipLevel.OWNER: 1.0,
            RelationshipLevel.CLOSE_FRIEND: 0.9,
            RelationshipLevel.FRIEND: 0.7,
            RelationshipLevel.ACQUAINTANCE: 0.5,
            RelationshipLevel.STRANGER: 0.3,
            RelationshipLevel.BLOCKED: 0.0,
        }
        return multipliers[self.level]

    def can_upgrade_to(self, new_level: RelationshipLevel) -> bool:
        """Check if relationship can be upgraded to new level.

        Args:
            new_level: Target relationship level

        Returns:
            True if upgrade is allowed, False otherwise

        Business Rules:
            - Cannot downgrade from OWNER
            - Cannot upgrade from/to BLOCKED without manual intervention
            - Can only upgrade one level at a time (except from STRANGER)
        """
        if self.level == RelationshipLevel.OWNER:
            return False  # Cannot change owner status

        if self.level == RelationshipLevel.BLOCKED or new_level == RelationshipLevel.BLOCKED:
            return False  # Blocked status requires manual intervention

        if new_level == RelationshipLevel.OWNER:
            return False  # Cannot auto-upgrade to owner

        # Allow any upgrade from stranger
        if self.level == RelationshipLevel.STRANGER:
            return new_level in (
                RelationshipLevel.ACQUAINTANCE,
                RelationshipLevel.FRIEND,
                RelationshipLevel.CLOSE_FRIEND,
            )

        # For other levels, check priority difference
        current_priority = self.level.priority
        new_priority = new_level.priority

        # Allow upgrade by one level
        return 0 < (new_priority - current_priority) <= 20

    def __str__(self) -> str:
        """Return string representation."""
        return str(self.level)
