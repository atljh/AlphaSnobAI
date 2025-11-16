#!/usr/bin/env python3
"""AlphaSnobAI - Telegram UserBot main entry point.

This file is called by the daemon manager. For CLI interface, use cli.py instead.
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_settings
from core.memory import Memory
from core.style_engine import StyleEngine
from core.message_handler import MessageHandler
from core.telegram_client import AlphaSnobClient
from core.daemon import setup_signal_handlers
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

    logger.info("Initializing components...")

    memory = Memory(settings.paths.database)
    await memory.initialize()
    logger.success("Memory initialized")

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
    logger.success("Style engine initialized")

    message_handler = MessageHandler(memory, style_engine)
    logger.success("Message handler initialized")

    client = AlphaSnobClient(message_handler)
    logger.success("Telegram client initialized")

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
