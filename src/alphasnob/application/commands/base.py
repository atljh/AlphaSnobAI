"""Base command and command handler interfaces.

Commands represent write operations (state changes) in CQRS pattern.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel
from returns.result import Result

# Command type
TCommand = TypeVar("TCommand", bound="Command")
# Command result type (success value)
TResult = TypeVar("TResult")


class Command(BaseModel):
    """Base class for all commands.

    Commands are write operations that change system state.
    They should be immutable (Pydantic models with frozen=True).

    Examples:
        class SendMessageCommand(Command):
            chat_id: int
            text: str
            persona_mode: str
    """

    class Config:
        frozen = True  # Commands are immutable


class CommandHandler(ABC, Generic[TCommand, TResult]):
    """Base class for command handlers.

    Each command has exactly one handler that executes the command.

    Handlers return Result monads (from returns library) for railway-oriented
    programming instead of raising exceptions.

    Examples:
        class SendMessageCommandHandler(CommandHandler[SendMessageCommand, UUID]):
            async def handle(self, command: SendMessageCommand) -> Result[UUID, Error]:
                # Execute command logic
                ...
                return Success(message_id)
    """

    @abstractmethod
    async def handle(self, command: TCommand) -> Result[TResult, Exception]:
        """Handle the command.

        Args:
            command: Command to execute

        Returns:
            Result with success value or error
        """
        ...
