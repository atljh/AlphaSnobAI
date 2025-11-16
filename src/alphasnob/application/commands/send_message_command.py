"""Send message command and handler."""

from uuid import UUID

from returns.result import Failure, Result, Success

from alphasnob.application.commands.base import Command, CommandHandler
from alphasnob.domain.messaging.entities.message import Message
from alphasnob.domain.messaging.repositories.message_repository import MessageRepository
from alphasnob.domain.messaging.value_objects.chat_id import ChatId
from alphasnob.domain.messaging.value_objects.message_content import MessageContent
from alphasnob.domain.shared.errors import DomainError
from alphasnob.domain.users.value_objects.user_id import UserId


class SendMessageCommand(Command):
    """Command to send a message.

    This represents the intent to send a message to Telegram.

    Attributes:
        chat_id: Target chat ID
        text: Message text to send
        persona_mode: Persona mode used for generation
        reply_to_message_id: Optional message ID to reply to
        decision_score: Decision score that led to sending
    """

    chat_id: int
    text: str
    persona_mode: str
    reply_to_message_id: int | None = None
    decision_score: float | None = None


class SendMessageCommandHandler(CommandHandler[UUID]):
    """Handler for SendMessageCommand.

    Executes the command by:
    1. Creating Message entity
    2. Persisting to repository
    3. Sending via Telegram (infrastructure concern)
    4. Returning message UUID
    """

    def __init__(
        self,
        message_repository: MessageRepository,
        bot_user_id: UserId,
    ):
        """Initialize handler with dependencies.

        Args:
            message_repository: Message repository
            bot_user_id: Bot's Telegram user ID
        """
        self.message_repository = message_repository
        self.bot_user_id = bot_user_id

    async def handle(
        self, command: SendMessageCommand
    ) -> Result[UUID, Exception]:
        """Handle send message command.

        Args:
            command: SendMessageCommand

        Returns:
            Result with message UUID or error
        """
        try:
            # Create message entity
            message = Message(
                message_id=0,  # Will be set after Telegram API call
                chat_id=ChatId(command.chat_id),
                user_id=self.bot_user_id,
                content=MessageContent(command.text),
                timestamp=datetime.now(),
                is_from_bot=True,
                persona_mode=command.persona_mode,
                decision_score=command.decision_score,
                replied_to_id=command.reply_to_message_id,
            )

            # Save message (will be updated with actual message_id later)
            await self.message_repository.save(message)

            return Success(message.id)

        except DomainError as e:
            return Failure(e)
        except Exception as e:
            return Failure(e)


# Need datetime import
from datetime import datetime
