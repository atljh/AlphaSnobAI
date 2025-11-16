#!/usr/bin/env python3
"""AlphaSnobAI - Telegram UserBot with LLM-powered responses.

A Telegram userbot that responds in a unique style combining:
- Aggressive trolling ("бордовый треш")
- American Psycho aestheticism
- Absurd hyperboles
- Narcissistic snobism
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from core.memory import Memory
from core.style_engine import StyleEngine
from core.message_handler import MessageHandler
from core.telegram_client import AlphaSnobClient


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('alphasnob.log')
        ]
    )


def print_banner():
    """Print startup banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              🎭 ALPHASNOB AI USERBOT 🎭                   ║
║                                                           ║
║  Элитарный эстет-псих с AI-интеллектом                   ║
║  Стиль: Бордовый треш × American Psycho × Гиперболы      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def validate_setup():
    logger = logging.getLogger(__name__)

    if not settings.corpus_path.exists():
        logger.warning(f"⚠️  Corpus file not found at {settings.corpus_path}")
        logger.warning("⚠️  Please create olds.txt with style examples")
        logger.warning("⚠️  Bot will use fallback responses if corpus is missing")

    logger.info(f"📁 Database: {settings.db_path}")
    logger.info(f"📚 Corpus: {settings.corpus_path}")
    logger.info(f"🤖 LLM Provider: {settings.llm_provider}")
    logger.info(f"🎯 Response Mode: {settings.response_mode}")


async def initialize_components():
    logger = logging.getLogger(__name__)
    logger.info("Initializing components...")

    memory = Memory(settings.db_path)
    await memory.initialize()
    logger.info("✅ Memory initialized")

    api_key = settings.anthropic_api_key if settings.llm_provider == "claude" else settings.openai_api_key

    style_engine = StyleEngine(
        corpus_path=settings.corpus_path,
        provider=settings.llm_provider,
        api_key=api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens
    )
    logger.info("✅ Style engine initialized")

    message_handler = MessageHandler(memory, style_engine)
    logger.info("✅ Message handler initialized")

    client = AlphaSnobClient(message_handler)
    logger.info("✅ Telegram client initialized")

    return memory, style_engine, message_handler, client


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    print_banner()

    try:
        validate_setup()

        logger.info("🚀 Starting AlphaSnob AI...")

        import asyncio

        async def run():
            memory, style_engine, message_handler, client = await initialize_components()
            await client.run()

        asyncio.run(run())

    except KeyboardInterrupt:
        logger.info("👋 Shutting down gracefully...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
