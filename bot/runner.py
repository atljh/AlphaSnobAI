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
from services.persona_manager import PersonaManager
from services.owner_learning import OwnerLearningSystem
from services.typing_simulator import TypingSimulator
from services.user_profiler import UserProfiler
from services.decision_engine import DecisionEngine
from utils.language_detector import LanguageDetector
from bot.handlers import MessageHandler
from bot.client import AlphaSnobClient
from bot.interactive import InteractiveSession
from utils.interactive_logger import setup_interactive_logging

console = Console()


async def run_interactive():
    session = InteractiveSession()
    setup_interactive_logging(session)

    settings = get_settings()

    session.add_log("INFO", "Initializing components with full persona system...")

    # Memory
    memory = Memory(settings.paths.database)
    await memory.initialize()
    session.add_log("SUCCESS", "Memory initialized")

    # LLM API
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
    session.add_log("SUCCESS", f"Style engine initialized ({settings.llm.provider})")

    # Persona Manager
    persona_manager = PersonaManager(settings)
    session.add_log("SUCCESS", f"Persona manager initialized ({len(persona_manager.personas)} personas)")

    # Owner Learning (optional)
    owner_learning = None
    if settings.owner_learning.enabled:
        try:
            owner_learning = OwnerLearningSystem(
                manual_samples_path=settings.owner_learning.manual_samples_path,
                min_samples=settings.owner_learning.min_samples
            )
            if owner_learning.has_sufficient_samples():
                session.add_log("SUCCESS", f"Owner learning initialized ({len(owner_learning.samples)} samples)")
            else:
                session.add_log("WARNING", f"Owner learning: insufficient samples ({len(owner_learning.samples)})")
        except Exception as e:
            session.add_log("WARNING", f"Owner learning failed: {e}")

    # Language Detector
    language_detector = LanguageDetector(
        supported_languages=settings.language.supported,
        default_language=settings.language.default
    )
    session.add_log("SUCCESS", f"Language detector initialized")

    # Typing Simulator
    typing_simulator = TypingSimulator(settings.typing)
    session.add_log("SUCCESS", f"Typing simulator initialized")

    # User Profiler
    user_profiler = UserProfiler(settings.paths.database, settings.profiling)
    await user_profiler.initialize()
    session.add_log("SUCCESS", f"User profiler initialized")

    # Decision Engine
    decision_engine = DecisionEngine(settings.decision)
    session.add_log("SUCCESS", f"Decision engine initialized")

    # Message Handler (integrated)
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
        interactive_session=session
    )
    session.add_log("SUCCESS", "Message handler initialized")

    # Telegram Client
    client = AlphaSnobClient(message_handler)
    session.add_log("SUCCESS", "Telegram client initialized")
    session.add_log("INFO", f"Default persona: {settings.persona.default_mode}")

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
