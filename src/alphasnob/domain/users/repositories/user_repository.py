"""User repository interface (port).

This is a domain interface that defines how to interact with user storage.
Infrastructure layer will provide concrete implementations.
"""

from typing import Protocol
from uuid import UUID

from alphasnob.domain.users.entities.user import User
from alphasnob.domain.users.entities.user_profile import UserProfile
from alphasnob.domain.users.value_objects.relationship import RelationshipLevel
from alphasnob.domain.users.value_objects.user_id import UserId


class UserRepository(Protocol):
    """Repository interface for user persistence.

    This is a port (interface) in hexagonal architecture.
    Infrastructure layer provides adapters (implementations).

    All methods are async because database operations are I/O bound.

    Examples:
        # In domain/application layer, use interface:
        async def get_user(repo: UserRepository, user_id: UserId) -> User:
            return await repo.get_by_user_id(user_id)

        # In infrastructure layer, provide implementation:
        class SQLAlchemyUserRepository:
            async def get_by_user_id(self, user_id: UserId) -> User:
                # Database query implementation
                ...
    """

    async def get_by_id(self, entity_id: UUID) -> User | None:
        """Get user by internal UUID.

        Args:
            entity_id: Internal entity UUID

        Returns:
            User if found, None otherwise
        """
        ...

    async def get_by_user_id(self, user_id: UserId) -> User | None:
        """Get user by Telegram user ID.

        Args:
            user_id: Telegram user ID

        Returns:
            User if found, None otherwise
        """
        ...

    async def save(self, user: User) -> None:
        """Save or update user.

        Args:
            user: User entity to save
        """
        ...

    async def delete(self, user: User) -> None:
        """Delete user.

        Args:
            user: User entity to delete
        """
        ...

    async def exists(self, user_id: UserId) -> bool:
        """Check if user exists.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user exists, False otherwise
        """
        ...


class UserProfileRepository(Protocol):
    """Repository interface for user profile persistence.

    User profiles are richer than basic users and include
    relationship, trust, and interaction history.

    This is the main repository for user management.
    """

    async def get_by_id(self, entity_id: UUID) -> UserProfile | None:
        """Get profile by internal UUID.

        Args:
            entity_id: Internal entity UUID

        Returns:
            UserProfile if found, None otherwise
        """
        ...

    async def get_by_user_id(self, user_id: UserId) -> UserProfile | None:
        """Get profile by Telegram user ID.

        Args:
            user_id: Telegram user ID

        Returns:
            UserProfile if found, None otherwise
        """
        ...

    async def get_or_create(self, user_id: UserId, **kwargs: str) -> UserProfile:
        """Get existing profile or create new one.

        Args:
            user_id: Telegram user ID
            **kwargs: Additional user info (username, first_name, etc.)

        Returns:
            UserProfile (existing or newly created)

        Note:
            New profiles start as STRANGER with 0.5 trust score.
        """
        ...

    async def save(self, profile: UserProfile) -> None:
        """Save or update profile.

        Args:
            profile: UserProfile entity to save
        """
        ...

    async def delete(self, profile: UserProfile) -> None:
        """Delete profile.

        Args:
            profile: UserProfile entity to delete
        """
        ...

    async def find_by_relationship(
        self,
        level: RelationshipLevel,
        limit: int = 100,
    ) -> list[UserProfile]:
        """Find profiles by relationship level.

        Args:
            level: Relationship level to filter by
            limit: Maximum number of profiles to return

        Returns:
            List of UserProfile entities
        """
        ...

    async def find_by_trust_score(
        self,
        min_score: float,
        max_score: float,
        limit: int = 100,
    ) -> list[UserProfile]:
        """Find profiles by trust score range.

        Args:
            min_score: Minimum trust score (0.0-1.0)
            max_score: Maximum trust score (0.0-1.0)
            limit: Maximum number of profiles to return

        Returns:
            List of UserProfile entities
        """
        ...

    async def get_owner(self) -> UserProfile | None:
        """Get bot owner profile.

        Returns:
            Owner UserProfile if exists, None otherwise

        Note:
            There should only be one owner. If multiple exist,
            returns the first one found.
        """
        ...

    async def count(self) -> int:
        """Get total number of profiles.

        Returns:
            Total profile count
        """
        ...
