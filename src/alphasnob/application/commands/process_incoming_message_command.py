"""Process incoming message command and handler."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from returns.result import Failure, Result, Success

from alphasnob.application.commands.base import Command, CommandHandler
from alphasnob.domain.decisions.services.decision_engine import DecisionEngine
from alphasnob.domain.messaging.entities.message import Message
from alphasnob.domain.messaging.repositories.message_repository import MessageRepository
from alphasnob.domain.messaging.value_objects.chat_id import ChatId
from alphasnob.domain.messaging.value_objects.message_content import MessageContent
from alphasnob.domain.shared.errors import DomainError
from alphasnob.domain.users.repositories.user_repository import UserProfileRepository
from alphasnob.domain.users.value_objects.relationship import Relationship, RelationshipLevel
from alphasnob.domain.users.value_objects.trust_score import TrustScore
from alphasnob.domain.users.value_objects.user_id import UserId


class ProcessIncomingMessageCommand(Command):
    """Command to process an incoming message.

    This is the main command for handling new messages from Telegram.

    Attributes:
        message_id: Telegram message ID
        chat_id: Chat ID
        user_id: User ID
        text: Message text
        username: Username (optional)
        first_name: User's first name
        last_name: User's last name (optional)
        is_private_chat: Whether this is a private chat
    """

    message_id: int
    chat_id: int
    user_id: int
    text: str
    username: str | None = None
    first_name: str = "Unknown"
    last_name: str | None = None
    is_private_chat: bool = False


class ProcessIncomingMessageCommandHandler(CommandHandler[UUID]):
    """Handler for ProcessIncomingMessageCommand.

    This is the main application service that orchestrates:
    1. Save incoming message
    2. Get/create user profile
    3. Record interaction
    4. Make decision on whether to respond
    5. Return decision for further processing
    """

    def __init__(
        self,
        message_repository: MessageRepository,
        user_profile_repository: UserProfileRepository,
        decision_engine: DecisionEngine,
        bot_username: Optional[str] = None,
    ):
        """Initialize handler with dependencies.

        Args:
            message_repository: Message repository
            user_profile_repository: User profile repository
            decision_engine: Decision engine domain service
            bot_username: Bot's username for mention detection
        """
        self.message_repository = message_repository
        self.user_profile_repository = user_profile_repository
        self.decision_engine = decision_engine
        self.bot_username = bot_username

    async def handle(
        self, command: ProcessIncomingMessageCommand
    ) -> Result[UUID, Exception]:
        """Handle process incoming message command.

        Args:
            command: ProcessIncomingMessageCommand

        Returns:
            Result with message UUID or error
        """
        try:
            # 1. Create and save message entity
            message = Message(
                message_id=command.message_id,
                chat_id=ChatId(command.chat_id),
                user_id=UserId(command.user_id),
                content=MessageContent(command.text),
                username=command.username,
                timestamp=datetime.now(),
                is_from_bot=False,
            )
            await self.message_repository.save(message)

            # 2. Get or create user profile
            user_profile = await self.user_profile_repository.get_or_create(
                user_id=UserId(command.user_id),
                username=command.username or "",
                first_name=command.first_name,
                last_name=command.last_name or "",
            )

            # 3. Record interaction
            user_profile.record_interaction(is_positive=True)

            # 4. Try auto-upgrade relationship
            if user_profile.try_upgrade_relationship():
                # Profile was upgraded
                pass

            # 5. Save updated profile
            await self.user_profile_repository.save(user_profile)

            # 6. Make decision (this is done in separate handler/service)
            # For now, just return message ID
            # The response generation will be handled by a separate service

            return Success(message.id)

        except DomainError as e:
            return Failure(e)
        except Exception as e:
            return Failure(e)
