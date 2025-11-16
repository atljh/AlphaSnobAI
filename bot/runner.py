import sys
import asyncio
import signal
from pathlib import Path
from rich.live import Live
from rich.console import Console

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings
from services.memory import Memory
from services.style import StyleEngine
from bot.handlers import MessageHandler
from bot.client import AlphaSnobClient
from bot.interactive import InteractiveSession
from utils.interactive_logger import setup_interactive_logging

console = Console()


async def run_interactive():
    session = InteractiveSession()
    setup_interactive_logging(session)

    settings = get_settings()

    session.add_log("INFO", "Initializing components...")

    memory = Memory(settings.paths.database)
    await memory.initialize()
    session.add_log("SUCCESS", "Memory initialized")

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
    session.add_log("SUCCESS", "Style engine initialized")

    message_handler = MessageHandler(memory, style_engine, interactive_session=session)
    session.add_log("SUCCESS", "Message handler initialized")

    client = AlphaSnobClient(message_handler)
    session.add_log("SUCCESS", "Telegram client initialized")

    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        session.add_log("WARNING", "Received shutdown signal")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    bot_task = asyncio.create_task(client.run())

    try:
        with Live(session.get_layout(), console=console, refresh_per_second=4) as live:
            while not shutdown_event.is_set():
                live.update(session.get_layout())
                await asyncio.sleep(0.25)

    except KeyboardInterrupt:
        session.add_log("INFO", "Shutting down...")

    shutdown_event.set()

    session.add_log("INFO", "Stopping client...")
    await client.stop()

    if not bot_task.done():
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass

    session.add_log("SUCCESS", "Bot stopped successfully")


def main():
    try:
        asyncio.run(run_interactive())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[bold red]Fatal error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
