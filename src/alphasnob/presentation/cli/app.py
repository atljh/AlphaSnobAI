"""CLI application entry point.

This is the main entry point for the command-line interface.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from alphasnob import __version__

app = typer.Typer(
    name="alphasnob",
    help="AlphaSnobAI - Elite AI-Powered Telegram UserBot with DDD Architecture",
    add_completion=False,
)

console = Console()


@app.command()  # type: ignore[misc]
def version() -> None:
    """Show version information."""
    console.print(Panel(f"[bold cyan]AlphaSnobAI v{__version__}[/]"))
    console.print("[green]DDD Architecture with modern Python practices[/]")


@app.command()  # type: ignore[misc]
def start(
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Run in interactive mode"),  # noqa: FBT001, FBT003
) -> None:
    """Start the Telegram bot."""
    from alphasnob.presentation.cli.commands.start import run_start_command  # noqa: PLC0415

    run_start_command(interactive=interactive)


@app.command()  # type: ignore[misc]
def daemon(
    action: str = typer.Argument(..., help="Action: start, stop, status, restart"),
) -> None:
    """Manage bot daemon."""
    console.print(f"[yellow]Daemon {action}...[/]")
    console.print("[dim]Daemon mode is under development[/]")


@app.command()  # type: ignore[misc]
def logs(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),  # noqa: FBT001, FBT003
    lines: int = typer.Option(100, "--lines", "-n", help="Number of lines to show"),
) -> None:
    """View bot logs."""
    console.print(f"[yellow]Showing last {lines} log lines...[/]")

    if follow:
        console.print("[blue]Following logs (Ctrl+C to stop)...[/]")

    console.print("[dim]Log viewing is under development[/]")


@app.command()  # type: ignore[misc]
def db(
    action: str = typer.Argument(..., help="Action: backup, restore, vacuum, integrity"),
) -> None:
    """Database management."""
    console.print(f"[yellow]Database {action}...[/]")
    console.print("[dim]Database management is under development[/]")


@app.command()  # type: ignore[misc]
def init() -> None:
    """Initialize project configuration and database."""
    console.print("[yellow]Initializing AlphaSnobAI...[/]")

    # Create directories
    directories = ["data", "logs", "config", "data/owner_samples"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/] Created directory: {directory}")

    console.print("\n[bold green]Initialization complete![/]")
    console.print("\n[yellow]Next steps:[/]")
    console.print("1. Copy config/config.yaml.example to config/config.yaml")
    console.print("2. Copy config/secrets.yaml.example to config/secrets.yaml")
    console.print("3. Edit configuration files with your API keys")
    console.print("4. Run: alphasnob start")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
