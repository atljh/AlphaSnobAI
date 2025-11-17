"""Telegram client wrapper using Telethon.

This is an adapter that wraps Telethon client and provides
domain-friendly interface for bot operations.
"""

import logging
from typing import TYPE_CHECKING

from telethon import TelegramClient, events

from alphasnob.application.services.message_handling_service import MessageHandlingService
from alphasnob.domain.users.value_objects.user_id import UserId
from alphasnob.infrastructure.config.settings import Settings

if TYPE_CHECKING:
    from telethon.tl.types import User

logger = logging.getLogger(__name__)


class AlphaSnobTelegramClient:
    """Telegram client wrapper for AlphaSnobAI.

    Wraps Telethon client and handles:
    - Authentication
    - Message receiving
    - Message sending
    - Event handling

    Examples:
        client = AlphaSnobTelegramClient(settings, message_service)
        await client.start()
        await client.run()
    """

    def __init__(
        self,
        settings: Settings,
        message_handling_service: MessageHandlingService,
    ):
        """Initialize Telegram client.

        Args:
            settings: Application settings
            message_handling_service: Message handling service
        """
        self.settings = settings
        self.message_handling_service = message_handling_service

        # Create Telethon client
        self.client = TelegramClient(
            settings.telegram.session_name,
            settings.telegram.api_id,
            settings.telegram.api_hash,
        )

        # Bot info (set after start)
        self.bot_user: User | None = None
        self.bot_user_id: UserId | None = None

    async def start(self) -> None:
        """Start Telegram client and authenticate.

        This will prompt for phone/code if not authenticated yet.
        """
        logger.info("Starting Telegram client...")

        await self.client.start()

        # Get bot's user info
        me = await self.client.get_me()
        self.bot_user = me
        self.bot_user_id = UserId(me.id)

        logger.info(
            "Authenticated as: %s (@%s) [ID: %s]",
            me.first_name,
            me.username or "no username",
            me.id,
        )

        # Register event handlers
        self._register_handlers()

    async def run(self) -> None:
        """Run client until disconnected.

        This keeps the bot running and processing events.
        """
        logger.info("Bot is running. Press Ctrl+C to stop.")
        await self.client.run_until_disconnected()

    async def stop(self) -> None:
        """Stop client and disconnect."""
        logger.info("Stopping Telegram client...")
        await self.client.disconnect()

    def _register_handlers(self) -> None:
        """Register Telegram event handlers."""

        @self.client.on(events.NewMessage(incoming=True, outgoing=False))  # type: ignore[misc]
        async def on_new_message(event: events.NewMessage.Event) -> None:
            """Handle incoming messages."""
            try:
                # Get message info
                message = event.message
                chat = await event.get_chat()
                sender = await event.get_sender()

                # Skip if message is from us
                if sender.id == self.bot_user_id:
                    return

                # Check if private chat
                is_private = hasattr(chat, "first_name")

                logger.info(
                    "Received message from %s (@%s) in chat %s: %s...",
                    sender.first_name,
                    sender.username or "no username",
                    chat.id,
                    message.text[:50] if message.text else "",
                )

                # Process message through application service
                result = await self.message_handling_service.handle_incoming_message(
                    message_id=message.id,
                    chat_id=chat.id,
                    user_id=sender.id,
                    text=message.text or "",
                    username=sender.username,
                    first_name=sender.first_name or "Unknown",
                    last_name=sender.last_name,
                    is_private_chat=is_private,
                )

                # Check result
                match result:
                    case _:
                        # For now, just log success
                        logger.info("Message processed successfully")

            except Exception:
                logger.exception("Error handling message")

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to: int | None = None,
    ) -> None:
        """Send message to chat.

        Args:
            chat_id: Target chat ID
            text: Message text
            reply_to: Optional message ID to reply to
        """
        try:
            await self.client.send_message(
                chat_id,
                text,
                reply_to=reply_to,
            )
            logger.info("Sent message to %s: %s...", chat_id, text[:50])
        except Exception:
            logger.exception("Error sending message")
