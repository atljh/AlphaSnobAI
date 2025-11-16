import random
import logging
from typing import Optional
from datetime import datetime
from telethon import events
from telethon.tl.types import User

from services.memory import Memory
from services.style import StyleEngine
from services.persona_manager import PersonaManager
from services.owner_learning import OwnerLearningSystem
from services.typing_simulator import TypingSimulator
from services.user_profiler import UserProfiler
from services.decision_engine import DecisionEngine
from utils.language_detector import LanguageDetector
from config.settings import get_settings, Settings

logger = logging.getLogger(__name__)


class MessageHandler:

    def __init__(
        self,
        memory: Memory,
        style_engine: StyleEngine,
        settings: Settings,
        persona_manager: PersonaManager,
        user_profiler: UserProfiler,
        typing_simulator: TypingSimulator,
        decision_engine: DecisionEngine,
        language_detector: LanguageDetector,
        owner_learning: Optional[OwnerLearningSystem] = None,
        interactive_session=None
    ):
        self.memory = memory
        self.style_engine = style_engine
        self.settings = settings
        self.persona_manager = persona_manager
        self.user_profiler = user_profiler
        self.typing_simulator = typing_simulator
        self.decision_engine = decision_engine
        self.language_detector = language_detector
        self.owner_learning = owner_learning
        self.interactive_session = interactive_session
        self.my_user_id: Optional[int] = None
        self.my_username: Optional[str] = None

        logger.info("MessageHandler initialized with full persona system")

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
        """
        Main message handling logic with full persona system integration.

        Flow:
        1. Extract message info and save to memory
        2. Get/create user profile
        3. Detect language
        4. Use DecisionEngine to decide if should respond
        5. If yes: simulate typing, generate response with selected persona, send
        """
        try:
            chat_id = event.chat_id
            user_id = event.sender_id
            message_text = event.message.text

            if not message_text:
                return

            # Get sender info
            sender = await event.get_sender()
            if isinstance(sender, User):
                username = sender.username or sender.first_name or f"User{user_id}"
                first_name = sender.first_name
                last_name = sender.last_name
            else:
                username = f"User{user_id}"
                first_name = None
                last_name = None

            logger.info(f"📨 Message from {username} in chat {chat_id}: {message_text[:50]}...")

            if self.interactive_session:
                self.interactive_session.increment_messages()

            # Save incoming message to memory
            await self.memory.add_message(
                chat_id=chat_id,
                user_id=user_id,
                username=username,
                text=message_text,
                timestamp=datetime.fromtimestamp(event.message.date.timestamp())
            )

            # PHASE 1: User Profiling
            user_profile = await self.user_profiler.get_or_create_profile(
                user_id=user_id,
                username=username
            )
            logger.debug(f"User profile: {user_profile}")

            # Update first/last name if available
            if first_name or last_name:
                update_data = {}
                if first_name and user_profile.first_name != first_name:
                    update_data['first_name'] = first_name
                if last_name and user_profile.last_name != last_name:
                    update_data['last_name'] = last_name
                if update_data:
                    await self.user_profiler.update_profile(user_id, **update_data)

            # PHASE 2: Language Detection
            detected_language = self.language_detector.detect(message_text)
            logger.debug(f"Detected language: {detected_language}")

            # PHASE 3: Decision Engine
            current_time = datetime.now()
            recent_messages = await self.memory.get_context(chat_id, limit=20)

            decision_result = self.decision_engine.should_respond(
                user_profile=user_profile,
                message_text=message_text,
                current_time=current_time,
                recent_bot_messages=recent_messages,
                bot_user_id=self.my_user_id
            )

            logger.info(f"🎲 {decision_result.reasoning}")

            # Check legacy should_respond for backward compatibility
            if not self.should_respond(event):
                logger.debug("Skipping response based on legacy response mode")
                return

            if not decision_result.should_respond:
                logger.info("❌ DecisionEngine decided to SKIP response")
                return

            logger.info(f"✅ DecisionEngine decided to RESPOND (p={decision_result.final_probability:.2f})")

            # PHASE 4: Update user profile
            await self.user_profiler.increment_interaction(user_id)
            await self.user_profiler.analyze_and_adjust_trust(user_id, message_text)

            # PHASE 5: Persona Selection
            persona = self.persona_manager.get_persona_for_context(
                user_id=user_id,
                chat_id=chat_id,
                user_profile=user_profile
            )
            logger.info(f"🎭 Selected persona: {persona.name}")

            # PHASE 6: Get context and prepare prompt
            context_messages = await self.memory.get_context(
                chat_id=chat_id,
                limit=self.settings.bot.context_length
            )

            # Detect tone for response
            tone = self.style_engine._detect_tone(message_text)
            logger.debug(f"Detected tone: {tone}")

            # Get corpus examples or owner samples based on persona
            corpus_examples = None
            owner_samples = None

            if persona.name == 'alphasnob':
                corpus_examples = self.style_engine.corpus.get_adaptive_samples(tone, n=12)
            elif persona.name == 'owner' and self.owner_learning:
                if self.owner_learning.has_sufficient_samples():
                    owner_samples = self.owner_learning.get_samples(n=20)
                    logger.info(f"Using {len(owner_samples)} owner samples for mimicry")
                else:
                    logger.warning("Insufficient owner samples, using conservative style")

            # Generate prompt using PersonaManager
            system_prompt, user_prompt = self.persona_manager.generate_prompt(
                persona=persona,
                incoming_message=message_text,
                context_messages=context_messages,
                sender_name=username,
                tone=tone,
                detected_language=detected_language,
                corpus_examples=corpus_examples,
                owner_samples=owner_samples
            )

            # PHASE 7: Typing Simulation (BEFORE generating response)
            # Simulate reading the message
            await self.typing_simulator.simulate_read(
                client=event.client,
                chat_id=chat_id,
                message=message_text
            )

            # PHASE 8: Generate Response
            logger.info(f"🤖 Generating response with {persona.name} persona...")

            # Use style_engine's LLM client to generate response
            try:
                if self.style_engine.provider == "claude":
                    response_text = await self.style_engine._generate_claude(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        max_tokens=self.settings.llm.max_tokens,
                        temperature=self.settings.llm.temperature
                    )
                else:
                    response_text = await self.style_engine._generate_openai(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        max_tokens=self.settings.llm.max_tokens,
                        temperature=self.settings.llm.temperature
                    )
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                response_text = self.style_engine._fallback_response(tone)

            if not response_text:
                logger.warning("Empty response generated, skipping")
                return

            # PHASE 9: Typing Simulation (WHILE preparing to send)
            timing_data = await self.typing_simulator.simulate_typing(
                client=event.client,
                chat_id=chat_id,
                response=response_text
            )

            # PHASE 10: Send Response
            await event.respond(response_text)
            logger.info(f"📤 Sent response ({len(response_text)} chars): {response_text[:50]}...")

            if self.interactive_session:
                self.interactive_session.increment_responses()

            # PHASE 11: Save bot's response with metadata
            await self.memory.add_message(
                chat_id=chat_id,
                user_id=self.my_user_id,
                username=self.my_username or "AlphaSnob",
                text=response_text,
                persona_mode=persona.name,
                response_delay_ms=timing_data.get('total_delay_ms', 0) if timing_data else 0,
                decision_score=decision_result.final_probability
            )

            logger.info(f"✨ Message handling complete")

        except Exception as e:
            logger.error(f"❌ Error handling message: {e}", exc_info=True)

    async def get_statistics(self, chat_id: int) -> str:
        stats = await self.memory.get_chat_statistics(chat_id)
        return (
            f"📊 Статистика чата {chat_id}:\n"
            f"💬 Сообщений: {stats['total_messages']}\n"
            f"👥 Уникальных пользователей: {stats['unique_users']}"
        )
