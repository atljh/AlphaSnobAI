import random
import logging
from typing import Optional
from datetime import datetime
from telethon import events
from telethon.tl.types import User

from core.memory import Memory
from core.style_engine import StyleEngine
from config.settings import get_settings

logger = logging.getLogger(__name__)


class MessageHandler:

    def __init__(self, memory: Memory, style_engine: StyleEngine):
        self.memory = memory
        self.style_engine = style_engine
        self.my_user_id: Optional[int] = None
        self.my_username: Optional[str] = None

    def set_my_user_info(self, user_id: int, username: Optional[str]):
        """Set the bot's own user info to filter out own messages.

        Args:
            user_id: Bot's user ID
            username: Bot's username
        """
        self.my_user_id = user_id
        self.my_username = username
        logger.info(f"Bot user info set: {username} ({user_id})")

    def should_respond(self, event: events.NewMessage.Event) -> bool:
        """Determine if bot should respond to this message.

        Args:
            event: Telegram message event

        Returns:
            True if should respond, False otherwise
        """
        if event.sender_id == self.my_user_id:
            return False

        settings = get_settings()
        mode = settings.bot.response_mode

        if mode == "all":
            return True

        elif mode == "specific_users":
            return event.sender_id in settings.bot.allowed_users

        elif mode == "probability":
            return random.random() < settings.bot.response_probability

        elif mode == "mentioned":
            message_text = event.message.text.lower()
            if self.my_username:
                username_lower = self.my_username.lower()
                if f"@{username_lower}" in message_text or username_lower in message_text:
                    return True

            if event.message.reply_to:
                return True

            return False

        else:
            logger.warning(f"Unknown response mode: {mode}")
            return False

    async def handle_message(self, event: events.NewMessage.Event):
        try:
            chat_id = event.chat_id
            user_id = event.sender_id
            message_text = event.message.text

            if not message_text:
                return

            sender = await event.get_sender()
            if isinstance(sender, User):
                username = sender.username or sender.first_name or f"User{user_id}"
            else:
                username = f"User{user_id}"

            logger.info(f"Message from {username} in chat {chat_id}: {message_text[:50]}...")

            await self.memory.add_message(
                chat_id=chat_id,
                user_id=user_id,
                username=username,
                text=message_text,
                timestamp=datetime.fromtimestamp(event.message.date.timestamp())
            )

            if not self.should_respond(event):
                logger.debug("Skipping response based on response mode")
                return

            logger.info(f"Generating response for message from {username}")

            settings = get_settings()
            context_messages = await self.memory.get_context(
                chat_id=chat_id,
                limit=settings.bot.context_length
            )

            response_text = await self.style_engine.generate_response(
                incoming_message=message_text,
                context_messages=context_messages,
                sender_name=username
            )

            if response_text:
                await event.respond(response_text)
                logger.info(f"Sent response: {response_text[:50]}...")

                await self.memory.add_message(
                    chat_id=chat_id,
                    user_id=self.my_user_id,
                    username=self.my_username or "AlphaSnob",
                    text=response_text
                )

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)

    async def get_statistics(self, chat_id: int) -> str:
        stats = await self.memory.get_chat_statistics(chat_id)
        return (
            f"📊 Статистика чата {chat_id}:\n"
            f"💬 Сообщений: {stats['total_messages']}\n"
            f"👥 Уникальных пользователей: {stats['unique_users']}"
        )
