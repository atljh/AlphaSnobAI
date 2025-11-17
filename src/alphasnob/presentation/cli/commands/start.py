"""Start command implementation."""

import asyncio
import logging
import subprocess  # nosec B404
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from alphasnob import __version__
from alphasnob.infrastructure.di.container import create_container
from alphasnob.infrastructure.telegram.client import AlphaSnobTelegramClient

console = Console()


def setup_logging(*, debug: bool = False) -> None:
    """Setup logging configuration.

    Args:
        debug: Enable debug logging
    """
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


async def start_bot() -> None:
    """Start the bot."""
    console.print(f"[bold cyan]AlphaSnobAI v{__version__}[/]")
    console.print("[yellow]Starting bot with DDD architecture...[/]\n")

    # Setup logging
    setup_logging(debug=False)
    logger = logging.getLogger(__name__)

    try:
        # Create DI container
        console.print("[blue]→[/] Creating dependency injection container...")
        container = create_container()

        # Check if config files exist
        config_path = Path("config/config.yaml")
        secrets_path = Path("config/secrets.yaml")

        if not config_path.exists() or not secrets_path.exists():
            console.print(
                "\n[red]✗ Configuration files not found![/]\n"
                "Please create configuration files:\n"
                "  1. cp config/config.yaml.example config/config.yaml\n"
                "  2. cp config/secrets.yaml.example config/secrets.yaml\n"
                "  3. Edit both files with your API keys\n",
            )
            return

        # Get settings
        settings = container.config()

        # Connect to database
        console.print("[blue]→[/] Connecting to database...")
        database = container.database()
        await database.connect()

        # Create tables if they don't exist
        await database.create_tables()
        console.print("[green]✓[/] Database connected")

        # Get message handling service
        console.print("[blue]→[/] Initializing message handling service...")
        message_service = container.message_handling_service()

        # Create Telegram client
        console.print("[blue]→[/] Initializing Telegram client...")
        telegram_client = AlphaSnobTelegramClient(
            settings=settings,
            message_handling_service=message_service,
        )

        # Start Telegram client (will authenticate if needed)
        console.print("[blue]→[/] Connecting to Telegram...")
        await telegram_client.start()
        console.print("[green]✓[/] Connected to Telegram")

        bot_name = telegram_client.bot_user.first_name if telegram_client.bot_user else "Unknown"
        console.print(
            f"\n[bold green]✓ Bot started successfully![/]\n"
            f"Authenticated as: {bot_name}\n"
            f"Press Ctrl+C to stop\n",
        )

        # Run bot
        await telegram_client.run()

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping bot...[/]")
    except Exception as e:
        logger.exception("Error starting bot")
        console.print(f"\n[red]Error: {e}[/]")
    finally:
        # Cleanup
        try:
            await database.disconnect()
            console.print("[green]✓[/] Disconnected from database")
        except Exception as cleanup_error:  # noqa: BLE001
            logger.debug("Failed to disconnect database: %s", cleanup_error)


def run_start_command(*, interactive: bool = False) -> None:
    """Run start command (sync wrapper).

    Args:
        interactive: Run in interactive mode (launches PyQt GUI)
    """
    if interactive:
        # Launch PyQt GUI application
        gui_path = Path("gui/app.py")
        if not gui_path.exists():
            console.print("[red]Error: GUI application not found at gui/app.py[/]")
            console.print(
                "[yellow]Tip: Install GUI dependencies with: pip install 'alphasnob[gui]'[/]",
            )
            return

        try:
            console.print("[blue]→[/] Launching PyQt GUI...")
            subprocess.run([sys.executable, str(gui_path)], check=True)  # noqa: S603 # nosec B603
        except KeyboardInterrupt:
            console.print("\n[yellow]GUI closed[/]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error running GUI: {e}[/]")
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]Failed to launch GUI: {e}[/]")
            console.print("[yellow]Make sure PySide6 is installed: pip install 'alphasnob[gui]'[/]")
    else:
        asyncio.run(start_bot())
