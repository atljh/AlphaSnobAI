"""Get message history query and handler."""

from returns.result import Failure, Result, Success

from alphasnob.application.dto.message_dto import MessageDTO
from alphasnob.application.queries.base import Query, QueryHandler
from alphasnob.domain.messaging.repositories.message_repository import MessageRepository
from alphasnob.domain.messaging.value_objects.chat_id import ChatId
from alphasnob.domain.shared.errors import DomainError


class GetMessageHistoryQuery(Query):
    """Query to get message history for a chat.

    Attributes:
        chat_id: Chat ID
        limit: Maximum number of messages to return
    """

    chat_id: int
    limit: int = 50


class GetMessageHistoryQueryHandler(QueryHandler["GetMessageHistoryQuery", list[MessageDTO]]):
    """Handler for GetMessageHistoryQuery."""

    def __init__(self, message_repository: MessageRepository):
        """Initialize handler.

        Args:
            message_repository: Message repository
        """
        self.message_repository = message_repository

    async def handle(
        self,
        query: GetMessageHistoryQuery,
    ) -> Result[list[MessageDTO], Exception]:
        """Handle get message history query.

        Args:
            query: GetMessageHistoryQuery

        Returns:
            Result with list of MessageDTO or error
        """
        try:
            # Get messages from repository
            messages = await self.message_repository.find_recent_in_chat(
                chat_id=ChatId(query.chat_id),
                limit=query.limit,
            )

            # Convert to DTOs
            message_dtos = [
                MessageDTO(
                    id=str(msg.id),
                    message_id=msg.message_id,
                    chat_id=msg.chat_id.value,
                    user_id=msg.user_id.value,
                    text=msg.content.text,
                    username=msg.username,
                    timestamp=msg.timestamp,
                    is_from_bot=msg.is_from_bot,
                    persona_mode=msg.persona_mode,
                )
                for msg in messages
            ]

            return Success(message_dtos)

        except DomainError as e:
            return Failure(e)
        except Exception as e:  # noqa: BLE001
            return Failure(e)
