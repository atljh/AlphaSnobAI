import logging
from telethon import TelegramClient, events
from telethon.tl.types import User

from config.settings import get_settings
from bot.handlers import MessageHandler

logger = logging.getLogger(__name__)


class AlphaSnobClient:

    def __init__(self, message_handler: MessageHandler):
        self.message_handler = message_handler
        settings = get_settings()

        self.client = TelegramClient(
            str(settings.base_dir / settings.telegram.session_name),
            settings.telegram.api_id,
            settings.telegram.api_hash
        )

        self._register_handlers()

        logger.info("AlphaSnobClient initialized")

    def _register_handlers(self):
        # Handle incoming messages
        @self.client.on(events.NewMessage(incoming=True))
        async def on_new_message(event):
            await self.message_handler.handle_message(event)

        logger.info("Event handlers registered")

    async def start(self):
        settings = get_settings()
        logger.info("Starting Telegram client...")

        await self.client.start()

        me = await self.client.get_me()
        if isinstance(me, User):
            self.message_handler.set_my_user_info(
                user_id=me.id,
                username=me.username
            )
            logger.info(f"Bot started as @{me.username} (ID: {me.id})")
            logger.info(f"Response mode: {settings.bot.response_mode}")

            if settings.bot.response_mode == "probability":
                logger.info(f"Response probability: {settings.bot.response_probability}")
            elif settings.bot.response_mode == "specific_users":
                logger.info(f"Allowed users: {settings.bot.allowed_users}")

        logger.info("AlphaSnob userbot is running!")
        logger.info("Press Ctrl+C to stop")

    async def run(self):
        try:
            await self.start()
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error running client: {e}", exc_info=True)
        finally:
            await self.stop()

    async def stop(self):
        logger.info("Stopping Telegram client...")
        await self.client.disconnect()
        logger.info("✅ Client stopped")

    def run_sync(self):
        import asyncio

        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            logger.info("Shutting down...")
