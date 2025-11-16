#!/usr/bin/env python3
"""AlphaSnobAI - Telegram UserBot main entry point.

This file is called by the daemon manager. For CLI interface, use cli.py instead.
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_settings
from services.memory import Memory
from services.style import StyleEngine
from services.persona_manager import PersonaManager
from services.owner_learning import OwnerLearningSystem
from services.typing_simulator import TypingSimulator
from services.user_profiler import UserProfiler
from services.decision_engine import DecisionEngine
from utils.language_detector import LanguageDetector
from bot.handlers import MessageHandler
from bot.client import AlphaSnobClient
from bot.daemon import setup_signal_handlers
from utils.rich_logger import setup_rich_logging


async def initialize_components():
    """Initialize all bot components.

    Returns:
        Tuple of (memory, style_engine, message_handler, client)
    """
    settings = get_settings()
    logger = setup_rich_logging(
        level=settings.daemon.log_level,
        log_file=settings.paths.logs
    )

    logger.info("🚀 Initializing AlphaSnobAI with full persona system...")

    # 1. Memory System
    memory = Memory(settings.paths.database)
    await memory.initialize()
    logger.success("✓ Memory initialized")

    # 2. LLM API Client
    api_key = (
        settings.llm.anthropic_api_key
        if settings.llm.provider == "claude"
        else settings.llm.openai_api_key
    )

    style_engine = StyleEngine(
        corpus_path=settings.paths.corpus,
        provider=settings.llm.provider,
        api_key=api_key,
        model=settings.llm.model,
        temperature=settings.llm.temperature,
        max_tokens=settings.llm.max_tokens
    )
    logger.success(f"✓ Style engine initialized ({settings.llm.provider})")

    # 3. Persona Manager
    persona_manager = PersonaManager(settings)
    logger.success(f"✓ Persona manager initialized ({len(persona_manager.personas)} personas)")

    # 4. Owner Learning System (optional)
    owner_learning = None
    owner_collector = None
    if settings.owner_learning.enabled:
        try:
            owner_learning = OwnerLearningSystem(
                manual_samples_path=settings.owner_learning.manual_samples_path,
                min_samples=settings.owner_learning.min_samples
            )
            if owner_learning.has_sufficient_samples():
                logger.success(f"✓ Owner learning initialized ({len(owner_learning.samples)} samples)")
            else:
                logger.warning(f"⚠ Owner learning initialized with insufficient samples ({len(owner_learning.samples)}/{settings.owner_learning.min_samples})")

            # Initialize owner collector for auto-collection
            from services.owner_collector import OwnerMessageCollector
            owner_collector = OwnerMessageCollector(settings.owner_learning)
            if settings.owner_learning.auto_collect:
                logger.success(f"✓ Owner collector initialized (auto_collect enabled)")
            else:
                logger.info("○ Owner collector initialized (auto_collect disabled)")

        except Exception as e:
            logger.warning(f"⚠ Owner learning failed to initialize: {e}")
    else:
        logger.info("○ Owner learning disabled")

    # 5. Language Detector
    language_detector = LanguageDetector(
        supported_languages=settings.language.supported,
        default_language=settings.language.default
    )
    logger.success(f"✓ Language detector initialized ({', '.join(settings.language.supported)})")

    # 6. Typing Simulator
    typing_simulator = TypingSimulator(settings.typing)
    logger.success(f"✓ Typing simulator initialized (enabled: {settings.typing.enabled})")

    # 7. User Profiler
    user_profiler = UserProfiler(settings.paths.database, settings.profiling)
    await user_profiler.initialize()
    logger.success(f"✓ User profiler initialized (enabled: {settings.profiling.enabled})")

    # 8. Decision Engine
    decision_engine = DecisionEngine(settings.decision)
    logger.success(f"✓ Decision engine initialized (base_p={settings.decision.base_probability})")

    # 9. Message Handler (integrated system)
    message_handler = MessageHandler(
        memory=memory,
        style_engine=style_engine,
        settings=settings,
        persona_manager=persona_manager,
        user_profiler=user_profiler,
        typing_simulator=typing_simulator,
        decision_engine=decision_engine,
        language_detector=language_detector,
        owner_learning=owner_learning,
        owner_collector=owner_collector
    )
    logger.success("✓ Message handler initialized with full persona system")

    # 10. Telegram Client
    client = AlphaSnobClient(message_handler)
    logger.success("✓ Telegram client initialized")

    logger.info(f"🎭 Default persona: {settings.persona.default_mode}")
    logger.info("✨ All systems ready!")

    return memory, style_engine, message_handler, client


async def run_bot():
    logger = setup_rich_logging()

    try:
        # Validate configuration
        settings = get_settings()
        warnings = settings.validate()

        if warnings:
            logger.warning("Configuration warnings:")
            for warning in warnings:
                logger.warning(f"  {warning}")

        memory, style_engine, message_handler, client = await initialize_components()

        shutdown_event = asyncio.Event()

        def shutdown_callback():
            logger.info("Received shutdown signal")
            shutdown_event.set()

        setup_signal_handlers(shutdown_callback)

        logger.info("Starting AlphaSnob bot...")
        bot_task = asyncio.create_task(client.run())

        await shutdown_event.wait()

        logger.info("Shutting down gracefully...")
        await client.stop()

        if not bot_task.done():
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                pass

        logger.success("Bot stopped successfully")

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.exception("Exception details:")
        sys.exit(1)


def main():
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
