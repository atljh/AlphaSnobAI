"""Tests for application layer commands."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from returns.result import Failure, Success

from alphasnob.application.commands.process_incoming_message_command import (
    ProcessIncomingMessageCommand,
    ProcessIncomingMessageCommandHandler,
)
from alphasnob.domain.messaging.entities.message import Message
from alphasnob.domain.users.entities.user_profile import UserProfile
from alphasnob.domain.users.value_objects.relationship import Relationship, RelationshipLevel
from alphasnob.domain.users.value_objects.trust_score import TrustScore
from alphasnob.domain.users.value_objects.user_id import UserId


@pytest.mark.asyncio
class TestProcessIncomingMessageCommand:
    """Tests for ProcessIncomingMessageCommand."""

    async def test_process_message_from_new_user(self) -> None:
        """Test processing message from new user."""
        # Setup mocks
        message_repo = AsyncMock()
        user_repo = AsyncMock()

        # Mock get_or_create to return new user profile
        new_profile = UserProfile(
            user_id=UserId(123),
            username="newuser",
            first_name="New",
            last_name="User",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )
        user_repo.get_or_create.return_value = new_profile
        user_repo.save.return_value = None
        message_repo.save.return_value = None

        # Create handler
        handler = ProcessIncomingMessageCommandHandler(
            message_repository=message_repo,
            user_profile_repository=user_repo,
        )

        # Create command
        command = ProcessIncomingMessageCommand(
            message_id=1,
            chat_id=-123456,
            user_id=123,
            text="Hello bot!",
            username="newuser",
            first_name="New",
            last_name="User",
            is_private_chat=True,
        )

        # Execute
        result = await handler.handle(command)

        # Verify
        assert isinstance(result, Success)
        assert user_repo.get_or_create.called
        assert user_repo.save.called
        assert message_repo.save.called

    async def test_process_message_from_existing_user(self) -> None:
        """Test processing message from existing user."""
        # Setup mocks
        message_repo = AsyncMock()
        user_repo = AsyncMock()

        # Mock existing user with some history
        existing_profile = UserProfile(
            user_id=UserId(456),
            username="existing",
            first_name="Existing",
            relationship=Relationship(level=RelationshipLevel.ACQUAINTANCE),
            trust_score=TrustScore(0.7),
            interaction_count=5,
            positive_interactions=4,
            negative_interactions=1,
        )
        user_repo.get_or_create.return_value = existing_profile
        user_repo.save.return_value = None
        message_repo.save.return_value = None

        handler = ProcessIncomingMessageCommandHandler(
            message_repository=message_repo,
            user_profile_repository=user_repo,
        )

        command = ProcessIncomingMessageCommand(
            message_id=2,
            chat_id=-789,
            user_id=456,
            text="Another message",
            username="existing",
            first_name="Existing",
            is_private_chat=False,
        )

        result = await handler.handle(command)

        # Verify
        assert isinstance(result, Success)
        # Interaction count should increase
        assert existing_profile.interaction_count == 6
        assert existing_profile.positive_interactions == 5

    async def test_process_message_triggers_relationship_upgrade(self) -> None:
        """Test that processing messages can trigger relationship upgrades."""
        message_repo = AsyncMock()
        user_repo = AsyncMock()

        # Create user profile that's ready to upgrade
        profile = UserProfile(
            user_id=UserId(789),
            username="upgrader",
            first_name="Upgrader",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.8),
            interaction_count=9,  # One more needed
            positive_interactions=8,
            negative_interactions=1,
        )
        user_repo.get_or_create.return_value = profile
        user_repo.save.return_value = None
        message_repo.save.return_value = None

        handler = ProcessIncomingMessageCommandHandler(
            message_repository=message_repo,
            user_profile_repository=user_repo,
        )

        command = ProcessIncomingMessageCommand(
            message_id=3,
            chat_id=-999,
            user_id=789,
            text="This should trigger upgrade",
            username="upgrader",
            first_name="Upgrader",
            is_private_chat=False,
        )

        result = await handler.handle(command)

        # Verify upgrade happened
        assert isinstance(result, Success)
        assert profile.interaction_count == 10
        assert profile.relationship.level == RelationshipLevel.ACQUAINTANCE

    async def test_command_immutability(self) -> None:
        """Test that commands are immutable."""
        command = ProcessIncomingMessageCommand(
            message_id=1,
            chat_id=-123,
            user_id=456,
            text="Test",
            username="test",
            first_name="Test",
            is_private_chat=True,
        )

        # Should not be able to modify
        with pytest.raises(Exception):  # Pydantic ValidationError or AttributeError
            command.text = "Modified"  # type: ignore

    async def test_handle_repository_error(self) -> None:
        """Test handling repository errors."""
        message_repo = AsyncMock()
        user_repo = AsyncMock()

        # Mock repository error
        user_repo.get_or_create.side_effect = Exception("Database error")

        handler = ProcessIncomingMessageCommandHandler(
            message_repository=message_repo,
            user_profile_repository=user_repo,
        )

        command = ProcessIncomingMessageCommand(
            message_id=1,
            chat_id=-123,
            user_id=123,
            text="Test",
            username="test",
            first_name="Test",
            is_private_chat=True,
        )

        result = await handler.handle(command)

        # Should return Failure
        assert isinstance(result, Failure)

    async def test_process_message_with_optional_fields(self) -> None:
        """Test processing message with all optional fields."""
        message_repo = AsyncMock()
        user_repo = AsyncMock()

        profile = UserProfile(
            user_id=UserId(111),
            username="complete",
            first_name="Complete",
            last_name="User",
            relationship=Relationship(level=RelationshipLevel.FRIEND),
            trust_score=TrustScore(0.8),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )
        user_repo.get_or_create.return_value = profile
        user_repo.save.return_value = None
        message_repo.save.return_value = None

        handler = ProcessIncomingMessageCommandHandler(
            message_repository=message_repo,
            user_profile_repository=user_repo,
        )

        command = ProcessIncomingMessageCommand(
            message_id=10,
            chat_id=-555,
            user_id=111,
            text="Complete message with all fields",
            username="complete",
            first_name="Complete",
            last_name="User",
            is_private_chat=True,
        )

        result = await handler.handle(command)

        assert isinstance(result, Success)
        assert message_repo.save.called

    async def test_message_saved_with_correct_attributes(self) -> None:
        """Test that message is saved with correct attributes."""
        message_repo = AsyncMock()
        user_repo = AsyncMock()

        profile = UserProfile(
            user_id=UserId(222),
            username="test",
            first_name="Test",
            relationship=Relationship(level=RelationshipLevel.STRANGER),
            trust_score=TrustScore(0.5),
            interaction_count=0,
            positive_interactions=0,
            negative_interactions=0,
        )
        user_repo.get_or_create.return_value = profile
        user_repo.save.return_value = None

        saved_message = None

        async def capture_message(msg: Message) -> None:
            nonlocal saved_message
            saved_message = msg

        message_repo.save.side_effect = capture_message

        handler = ProcessIncomingMessageCommandHandler(
            message_repository=message_repo,
            user_profile_repository=user_repo,
        )

        command = ProcessIncomingMessageCommand(
            message_id=42,
            chat_id=-888,
            user_id=222,
            text="Test message content",
            username="test",
            first_name="Test",
            is_private_chat=False,
        )

        await handler.handle(command)

        # Verify message attributes
        assert saved_message is not None
        assert saved_message.message_id == 42
        assert saved_message.chat_id.value == -888
        assert saved_message.user_id.value == 222
        assert saved_message.content.text == "Test message content"
