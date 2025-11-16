"""Get user profile query and handler."""

from returns.result import Failure, Result, Success

from alphasnob.application.dto.user_dto import UserProfileDTO
from alphasnob.application.queries.base import Query, QueryHandler
from alphasnob.domain.shared.errors import DomainError, EntityNotFoundError
from alphasnob.domain.users.repositories.user_repository import UserProfileRepository
from alphasnob.domain.users.value_objects.user_id import UserId


class GetUserProfileQuery(Query):
    """Query to get user profile by user ID.

    Attributes:
        user_id: Telegram user ID
    """

    user_id: int


class GetUserProfileQueryHandler(QueryHandler[UserProfileDTO]):
    """Handler for GetUserProfileQuery."""

    def __init__(self, user_profile_repository: UserProfileRepository):
        """Initialize handler.

        Args:
            user_profile_repository: User profile repository
        """
        self.user_profile_repository = user_profile_repository

    async def handle(
        self, query: GetUserProfileQuery
    ) -> Result[UserProfileDTO, Exception]:
        """Handle get user profile query.

        Args:
            query: GetUserProfileQuery

        Returns:
            Result with UserProfileDTO or error
        """
        try:
            # Get profile from repository
            profile = await self.user_profile_repository.get_by_user_id(
                user_id=UserId(query.user_id)
            )

            if profile is None:
                return Failure(
                    EntityNotFoundError(
                        "User profile not found", user_id=query.user_id
                    )
                )

            # Convert to DTO
            profile_dto = UserProfileDTO(
                id=str(profile.id),
                user_id=profile.user_id.value,
                username=profile.username,
                first_name=profile.first_name,
                last_name=profile.last_name,
                relationship_level=profile.relationship.level.value,
                trust_score=profile.trust_score.value,
                interaction_count=profile.interaction_count,
                positive_interactions=profile.positive_interactions,
                negative_interactions=profile.negative_interactions,
                detected_topics=profile.detected_topics,
                preferred_persona=profile.preferred_persona,
                notes=profile.notes,
                first_interaction=profile.first_interaction,
                last_interaction=profile.last_interaction,
            )

            return Success(profile_dto)

        except DomainError as e:
            return Failure(e)
        except Exception as e:
            return Failure(e)
