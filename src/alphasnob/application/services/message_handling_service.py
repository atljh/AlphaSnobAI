"""Message handling application service.

This service orchestrates the complete message handling flow:
1. Process incoming message
2. Make decision on whether to respond
3. Generate response if needed
4. Send response
"""

from typing import Optional
from uuid import UUID

from returns.result import Failure, Result, Success

from alphasnob.application.commands.process_incoming_message_command import (
    ProcessIncomingMessageCommand,
    ProcessIncomingMessageCommandHandler,
)
from alphasnob.application.commands.send_message_command import (
    SendMessageCommand,
    SendMessageCommandHandler,
)
from alphasnob.domain.decisions.services.decision_engine import DecisionEngine
from alphasnob.domain.messaging.repositories.message_repository import MessageRepository
from alphasnob.domain.shared.errors import DomainError
from alphasnob.domain.users.repositories.user_repository import UserProfileRepository
from alphasnob.domain.users.value_objects.user_id import UserId


class MessageHandlingService:
    """Application service for complete message handling flow.

    This is the main service that coordinates:
    - Processing incoming messages
    - Making response decisions
    - Generating responses
    - Sending responses

    Dependencies are injected via constructor.
    """

    def __init__(
        self,
        message_repository: MessageRepository,
        user_profile_repository: UserProfileRepository,
        decision_engine: DecisionEngine,
        bot_user_id: UserId,
        bot_username: Optional[str] = None,
    ):
        """Initialize service with dependencies.

        Args:
            message_repository: Message repository
            user_profile_repository: User profile repository
            decision_engine: Decision engine
            bot_user_id: Bot's Telegram user ID
            bot_username: Bot's username
        """
        self.message_repository = message_repository
        self.user_profile_repository = user_profile_repository
        self.decision_engine = decision_engine
        self.bot_user_id = bot_user_id
        self.bot_username = bot_username

        # Create command handlers
        self.process_message_handler = ProcessIncomingMessageCommandHandler(
            message_repository=message_repository,
            user_profile_repository=user_profile_repository,
            decision_engine=decision_engine,
            bot_username=bot_username,
        )

        self.send_message_handler = SendMessageCommandHandler(
            message_repository=message_repository,
            bot_user_id=bot_user_id,
        )

    async def handle_incoming_message(
        self,
        message_id: int,
        chat_id: int,
        user_id: int,
        text: str,
        username: Optional[str] = None,
        first_name: str = "Unknown",
        last_name: Optional[str] = None,
        is_private_chat: bool = False,
    ) -> Result[Optional[UUID], Exception]:
        """Handle incoming message.

        This is the main entry point for processing Telegram messages.

        Args:
            message_id: Telegram message ID
            chat_id: Chat ID
            user_id: User ID
            text: Message text
            username: Username
            first_name: First name
            last_name: Last name
            is_private_chat: Whether private chat

        Returns:
            Result with sent message UUID if responded, None if not responded, or error
        """
        try:
            # 1. Process incoming message
            command = ProcessIncomingMessageCommand(
                message_id=message_id,
                chat_id=chat_id,
                user_id=user_id,
                text=text,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_private_chat=is_private_chat,
            )

            result = await self.process_message_handler.handle(command)

            # Check if processing succeeded
            if isinstance(result, Failure):
                return result

            # 2. For now, return None (no response)
            # In full implementation, this would:
            # - Make decision using DecisionEngine
            # - Generate response using LLM
            # - Send response using SendMessageCommand

            return Success(None)

        except DomainError as e:
            return Failure(e)
        except Exception as e:
            return Failure(e)

    async def send_response(
        self, chat_id: int, text: str, persona_mode: str, decision_score: Optional[float] = None
    ) -> Result[UUID, Exception]:
        """Send bot response to chat.

        Args:
            chat_id: Target chat ID
            text: Response text
            persona_mode: Persona used
            decision_score: Decision score

        Returns:
            Result with message UUID or error
        """
        command = SendMessageCommand(
            chat_id=chat_id,
            text=text,
            persona_mode=persona_mode,
            decision_score=decision_score,
        )

        return await self.send_message_handler.handle(command)
