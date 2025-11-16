#!/usr/bin/env python3
"""AlphaSnobAI CLI - Unified command-line interface for bot management."""

import asyncio
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional
from datetime import timedelta, datetime
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_settings
from services.memory import Memory
from services.user_profiler import UserProfiler
from services.persona_manager import PersonaManager
from services.owner_learning import OwnerLearningSystem
from utils.setup_wizard import run_setup_wizard
from utils.log_viewer import LogViewer, LogLevel
from utils.stats_collector import StatsCollector
from utils.db_manager import DatabaseManager
from utils.monitor import BotMonitor
from bot.daemon import DaemonManager
from utils.ui import (
    print_banner,
    create_status_panel,
    show_success,
    show_error,
    show_warning,
    show_info,
    format_uptime,
)

app = typer.Typer(help="AlphaSnobAI - Advanced Telegram UserBot")
console = Console()


# ============================================================================
# SETUP COMMAND
# ============================================================================

@app.command("setup")
def setup():
    """Interactive setup wizard."""
    from pathlib import Path

    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "config.yaml"
    secrets_path = base_dir / "config" / "secrets.yaml"

    try:
        success = run_setup_wizard(config_path, secrets_path)
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Setup failed:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ============================================================================
# BOT CONTROL COMMANDS
# ============================================================================

@app.command("start")
def start(
    foreground: bool = typer.Option(False, "--foreground", "-f", help="Run in foreground"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Run in interactive mode")
):
    """Start the bot."""
    print_banner()

    try:
        settings = get_settings()
        daemon = DaemonManager(settings.daemon.pid_file)

        if daemon.is_running():
            pid = daemon.get_pid()
            show_error(f"Bot is already running with PID {pid}")
            show_info("Use 'python cli.py stop' to stop it first")
            sys.exit(1)

        show_info("Starting AlphaSnob bot...")

        if interactive:
            show_info("Starting in interactive mode...")
            subprocess.run([sys.executable, "bot/runner.py"], check=True)
        elif foreground:
            show_info("Running in foreground mode (Ctrl+C to stop)")
            subprocess.run([sys.executable, "main.py"], check=True)
        else:
            pid = daemon.start()

            if pid > 0:
                show_success("Bot started successfully!")
                show_info(f"PID: {pid}")
                show_info("Status: python cli.py status")
                show_info("Logs: python cli.py logs --follow")
            else:
                import main
                main.main()

    except Exception as e:
        show_error(f"Failed to start bot: {e}")
        sys.exit(1)


@app.command("stop")
def stop(
    force: bool = typer.Option(False, "--force", "-f", help="Force kill if graceful shutdown fails")
):
    """Stop the bot."""
    try:
        settings = get_settings()
        daemon = DaemonManager(settings.daemon.pid_file)

        if not daemon.is_running():
            show_warning("Bot is not running")
            sys.exit(0)

        pid = daemon.get_pid()
        show_info(f"Stopping bot (PID: {pid})...")

        timeout = 5 if force else 10
        success = daemon.stop(timeout=timeout)

        if success:
            show_success("Bot stopped successfully")
        else:
            show_error("Failed to stop bot")
            if not force:
                show_info("Try using --force flag to force kill")
            sys.exit(1)

    except Exception as e:
        show_error(f"Failed to stop bot: {e}")
        sys.exit(1)


@app.command("restart")
def restart():
    """Restart the bot."""
    try:
        settings = get_settings()
        daemon = DaemonManager(settings.daemon.pid_file)

        show_info("Restarting bot...")

        pid = daemon.restart(timeout=10)

        if pid > 0:
            show_success("Bot restarted successfully!")
            show_info(f"New PID: {pid}")
        else:
            import main
            main.main()

    except Exception as e:
        show_error(f"Failed to restart bot: {e}")
        sys.exit(1)


@app.command("status")
def status():
    """Show bot status."""
    try:
        settings = get_settings()
        daemon = DaemonManager(settings.daemon.pid_file)
        status_info = daemon.get_status()

        if status_info['running']:
            panel = create_status_panel(
                status="running",
                pid=status_info['pid'],
                uptime=status_info['uptime'],
                messages_processed=0,
                responses_sent=0,
                last_activity="N/A"
            )
            console.print(panel)

            show_info(f"Memory: {status_info['memory_mb']:.1f} MB")
            show_info(f"CPU: {status_info['cpu_percent']:.1f}%")
        else:
            panel = create_status_panel(status="stopped")
            console.print(panel)

    except Exception as e:
        show_error(f"Failed to get status: {e}")
        sys.exit(1)


@app.command("monitor")
def monitor():
    """Real-time monitoring with live panels."""
    try:
        settings = get_settings()

        console.print("[bold]AlphaSnobAI Monitor[/bold]")
        console.print("[dim]Press Ctrl+C to exit[/dim]\n")

        bot_monitor = BotMonitor(
            db_path=settings.paths.database,
            log_path=Path(settings.paths.logs),
            pid_file=settings.daemon.pid_file
        )

        asyncio.run(bot_monitor.run())

    except KeyboardInterrupt:
        console.print("\n[dim]Monitor stopped[/dim]")
    except Exception as e:
        show_error(f"Monitor failed: {e}")
        sys.exit(1)


# ============================================================================
# LOGS COMMANDS
# ============================================================================

logs_app = typer.Typer(help="View and manage logs")
app.add_typer(logs_app, name="logs")


@logs_app.callback(invoke_without_command=True)
def logs_default(
    ctx: typer.Context,
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    level: Optional[str] = typer.Option(None, "--level", "-l", help="Filter by level (DEBUG, INFO, WARNING, ERROR)"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search text in logs"),
    since: Optional[str] = typer.Option(None, "--since", help="Show logs since (e.g., '1h', '30m', '1d')"),
):
    """View logs."""
    if ctx.invoked_subcommand is not None:
        return

    try:
        settings = get_settings()
        log_path = Path(settings.paths.logs)

        if not log_path.exists():
            show_warning(f"Log file not found: {log_path}")
            sys.exit(1)

        viewer = LogViewer(log_path)

        # Parse since duration
        since_delta = None
        if since:
            since_delta = parse_duration(since)

        # Parse level
        log_level = LogLevel(level.upper()) if level else None

        if follow:
            console.print(f"[dim]Following logs (Ctrl+C to stop)[/dim]\n")
            try:
                for entry in viewer.tail_logs(level=log_level, search=search):
                    formatted = LogViewer.format_entry(entry)
                    console.print(formatted)
            except KeyboardInterrupt:
                console.print("\n[dim]Stopped following logs[/dim]")
        else:
            entries = viewer.read_logs(
                lines=lines,
                level=log_level,
                since=since_delta,
                search=search
            )

            if not entries:
                console.print("[dim]No log entries found[/dim]")
            else:
                for entry in entries:
                    formatted = LogViewer.format_entry(entry)
                    console.print(formatted)

    except Exception as e:
        show_error(f"Failed to read logs: {e}")
        sys.exit(1)


@logs_app.command("export")
def logs_export(
    output: str = typer.Argument(..., help="Output file path"),
    level: Optional[str] = typer.Option(None, "--level", "-l", help="Filter by level"),
    since: Optional[str] = typer.Option(None, "--since", help="Export logs since"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search text"),
):
    """Export logs to file."""
    try:
        settings = get_settings()
        log_path = Path(settings.paths.logs)
        output_path = Path(output)

        viewer = LogViewer(log_path)

        since_delta = parse_duration(since) if since else None
        log_level = LogLevel(level.upper()) if level else None

        count = viewer.export_logs(
            output_path=output_path,
            level=log_level,
            since=since_delta,
            search=search
        )

        show_success(f"Exported {count} log entries to {output_path}")

    except Exception as e:
        show_error(f"Failed to export logs: {e}")
        sys.exit(1)


def parse_duration(duration_str: str) -> timedelta:
    """Parse duration string like '1h', '30m', '1d'."""
    import re

    match = re.match(r'^(\d+)([smhd])$', duration_str)
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}")

    value, unit = match.groups()
    value = int(value)

    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)


# ============================================================================
# DATABASE COMMANDS
# ============================================================================

db_app = typer.Typer(help="Database management")
app.add_typer(db_app, name="db")


@db_app.command("backup")
def db_backup(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path")
):
    """Create database backup."""
    async def _backup():
        try:
            settings = get_settings()
            db_manager = DatabaseManager(settings.paths.database)

            output_path = Path(output) if output else None
            backup_path = await db_manager.backup(output_path)

            show_success(f"Database backed up to {backup_path}")

        except Exception as e:
            show_error(f"Backup failed: {e}")
            sys.exit(1)

    asyncio.run(_backup())


@db_app.command("restore")
def db_restore(
    backup: str = typer.Argument(..., help="Backup file path")
):
    """Restore database from backup."""
    async def _restore():
        try:
            settings = get_settings()
            db_manager = DatabaseManager(settings.paths.database)
            backup_path = Path(backup)

            if not backup_path.exists():
                show_error(f"Backup file not found: {backup_path}")
                sys.exit(1)

            show_warning("This will overwrite the current database!")
            if not typer.confirm("Continue?"):
                show_info("Restore cancelled")
                sys.exit(0)

            await db_manager.restore(backup_path)
            show_success("Database restored successfully")

        except Exception as e:
            show_error(f"Restore failed: {e}")
            sys.exit(1)

    asyncio.run(_restore())


@db_app.command("clean")
def db_clean(
    older_than: str = typer.Option("30d", "--older-than", help="Delete messages older than (e.g., '30d', '7d')"),
    chat_id: Optional[int] = typer.Option(None, "--chat-id", help="Only clean specific chat")
):
    """Clean old messages from database."""
    async def _clean():
        try:
            settings = get_settings()
            db_manager = DatabaseManager(settings.paths.database)

            duration = parse_duration(older_than)

            show_warning(f"This will delete messages older than {older_than}")
            if not typer.confirm("Continue?"):
                show_info("Clean cancelled")
                sys.exit(0)

            deleted = await db_manager.clean_old_messages(duration, chat_id)
            show_success(f"Deleted {deleted} messages")

        except Exception as e:
            show_error(f"Clean failed: {e}")
            sys.exit(1)

    asyncio.run(_clean())


@db_app.command("export")
def db_export(
    chat_id: int = typer.Argument(..., help="Chat ID to export"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json or txt)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path")
):
    """Export chat history."""
    async def _export():
        try:
            settings = get_settings()
            db_manager = DatabaseManager(settings.paths.database)

            output_path = Path(output) if output else None
            exported = await db_manager.export_chat_history(chat_id, format, output_path)

            show_success(f"Exported chat {chat_id} to {exported}")

        except Exception as e:
            show_error(f"Export failed: {e}")
            sys.exit(1)

    asyncio.run(_export())


@db_app.command("vacuum")
def db_vacuum():
    """Optimize database."""
    async def _vacuum():
        try:
            settings = get_settings()
            db_manager = DatabaseManager(settings.paths.database)

            show_info("Optimizing database...")
            await db_manager.vacuum()
            show_success("Database optimized")

        except Exception as e:
            show_error(f"Vacuum failed: {e}")
            sys.exit(1)

    asyncio.run(_vacuum())


@db_app.command("stats")
def db_stats():
    """Show database statistics."""
    async def _stats():
        try:
            settings = get_settings()
            db_manager = DatabaseManager(settings.paths.database)

            stats = await db_manager.get_stats()

            console.print("\n[bold]Database Statistics[/bold]\n")

            console.print(f"File size: {stats['file_size_mb']:.2f} MB")
            console.print(f"Database size: {stats['db_size_mb']:.2f} MB")
            console.print(f"Total pages: {stats['total_pages']}")
            console.print(f"Page size: {stats['page_size']} bytes")
            console.print(f"\nMessages: {stats['messages_count']}")
            console.print(f"User profiles: {stats['profiles_count']}")

            if stats['oldest_message']:
                console.print(f"\nOldest message: {stats['oldest_message']}")
            if stats['newest_message']:
                console.print(f"Newest message: {stats['newest_message']}")

            console.print()

        except Exception as e:
            show_error(f"Failed to get stats: {e}")
            sys.exit(1)

    asyncio.run(_stats())


# ============================================================================
# PERSONA COMMANDS
# ============================================================================

persona_app = typer.Typer(help="Manage bot personas")
app.add_typer(persona_app, name="persona")


@persona_app.command("list")
def list_personas():
    """List all available personas."""
    try:
        settings = get_settings()
        persona_manager = PersonaManager(settings)

        table = Table(title="🎭 Available Personas")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Display Name", style="green")
        table.add_column("Description", style="white")

        for name in persona_manager.list_personas():
            persona = persona_manager.get_persona_by_name(name)
            if persona:
                table.add_row(
                    name,
                    persona.display_name,
                    persona.description[:60] + "..." if len(persona.description) > 60 else persona.description
                )

        console.print(table)
        console.print(f"\n[bold]Default persona:[/bold] {settings.persona.default_mode}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@persona_app.command("show")
def show_persona(name: str):
    """Show detailed information about a persona."""
    try:
        settings = get_settings()
        persona_manager = PersonaManager(settings)

        persona = persona_manager.get_persona_by_name(name)
        if not persona:
            console.print(f"[bold red]Error:[/bold red] Persona '{name}' not found")
            sys.exit(1)

        console.print(f"\n[bold cyan]🎭 Persona: {persona.display_name}[/bold cyan]")
        console.print(f"[bold]Name:[/bold] {persona.name}")
        console.print(f"[bold]Description:[/bold] {persona.description}")
        console.print(f"\n[bold]System Prompt:[/bold]")
        console.print(persona.system_prompt[:500] + "..." if len(persona.system_prompt) > 500 else persona.system_prompt)

        if persona.short_templates:
            console.print(f"\n[bold]Short Templates:[/bold]")
            for tone, templates in persona.short_templates.items():
                console.print(f"  [cyan]{tone}:[/cyan] {len(templates)} templates")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@persona_app.command("set-default")
def set_default_persona(name: str):
    """Set the default persona (updates config.yaml)."""
    console.print(f"[yellow]To change default persona, edit config.yaml and set persona.default_mode to '{name}'[/yellow]")


# ============================================================================
# USER PROFILE COMMANDS
# ============================================================================

profile_app = typer.Typer(help="Manage user profiles")
app.add_typer(profile_app, name="profile")


@profile_app.command("list")
def list_profiles():
    """List all user profiles."""
    async def _list():
        try:
            settings = get_settings()
            profiler = UserProfiler(settings.paths.database, settings.profiling)
            await profiler.initialize()

            # Query all profiles from database
            import aiosqlite
            async with aiosqlite.connect(settings.paths.database) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT user_id, username, relationship_level, trust_score, interaction_count FROM user_profiles ORDER BY interaction_count DESC LIMIT 50"
                ) as cursor:
                    rows = await cursor.fetchall()

            if not rows:
                console.print("[yellow]No user profiles found[/yellow]")
                return

            table = Table(title="👥 User Profiles")
            table.add_column("User ID", style="cyan")
            table.add_column("Username", style="green")
            table.add_column("Relationship", style="magenta")
            table.add_column("Trust", style="yellow")
            table.add_column("Interactions", style="blue")

            for row in rows:
                trust_color = "green" if row['trust_score'] > 0 else "red" if row['trust_score'] < 0 else "white"
                table.add_row(
                    str(row['user_id']),
                    row['username'] or "Unknown",
                    row['relationship_level'],
                    f"[{trust_color}]{row['trust_score']:+.2f}[/{trust_color}]",
                    str(row['interaction_count'])
                )

            console.print(table)

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    asyncio.run(_list())


@profile_app.command("show")
def show_profile(user_id: int):
    """Show detailed information about a user profile."""
    async def _show():
        try:
            settings = get_settings()
            profiler = UserProfiler(settings.paths.database, settings.profiling)
            await profiler.initialize()

            profile = await profiler.get_or_create_profile(user_id, "Unknown")

            console.print(f"\n[bold cyan]👤 User Profile: {profile.username}[/bold cyan]")
            console.print(f"[bold]User ID:[/bold] {profile.user_id}")
            console.print(f"[bold]First Name:[/bold] {profile.first_name or 'N/A'}")
            console.print(f"[bold]Last Name:[/bold] {profile.last_name or 'N/A'}")
            console.print(f"[bold]Relationship:[/bold] {profile.relationship_level}")

            trust_color = "green" if profile.trust_score > 0 else "red" if profile.trust_score < 0 else "white"
            console.print(f"[bold]Trust Score:[/bold] [{trust_color}]{profile.trust_score:+.2f}[/{trust_color}]")

            console.print(f"[bold]Interactions:[/bold] {profile.interaction_count}")
            console.print(f"[bold]Detected Topics:[/bold] {', '.join(profile.detected_topics[:10]) if profile.detected_topics else 'None'}")
            console.print(f"[bold]Preferred Persona:[/bold] {profile.preferred_persona or 'Default'}")

            if profile.first_interaction:
                console.print(f"[bold]First Interaction:[/bold] {profile.first_interaction}")
            if profile.last_interaction:
                console.print(f"[bold]Last Interaction:[/bold] {profile.last_interaction}")

            if profile.notes:
                console.print(f"\n[bold]Notes:[/bold]\n{profile.notes}")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)

    asyncio.run(_show())


@profile_app.command("update")
def update_profile(
    user_id: int,
    relationship: Optional[str] = typer.Option(None, "--relationship", "-r", help="New relationship level"),
    trust: Optional[float] = typer.Option(None, "--trust", "-t", help="New trust score (-1.0 to 1.0)"),
    persona: Optional[str] = typer.Option(None, "--persona", "-p", help="Preferred persona"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Add notes")
):
    """Update a user profile."""
    async def _update():
        try:
            settings = get_settings()
            profiler = UserProfiler(settings.paths.database, settings.profiling)
            await profiler.initialize()

            update_data = {}
            if relationship:
                update_data['relationship_level'] = relationship
            if trust is not None:
                update_data['trust_score'] = max(-1.0, min(1.0, trust))
            if persona:
                update_data['preferred_persona'] = persona
            if notes:
                update_data['notes'] = notes

            if not update_data:
                console.print("[yellow]No updates specified[/yellow]")
                return

            await profiler.update_profile(user_id, **update_data)
            console.print(f"[green]✓ Profile updated for user {user_id}[/green]")

            # Show updated profile
            profile = await profiler.get_or_create_profile(user_id, "Unknown")
            console.print(f"\n{await profiler.get_profile_summary(user_id)}")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)

    asyncio.run(_update())


@profile_app.command("export")
def profile_export(
    output: str = typer.Option("profiles_export.json", "--output", "-o", help="Output file path")
):
    """Export all user profiles to JSON."""
    async def _export():
        try:
            settings = get_settings()
            db_manager = DatabaseManager(settings.paths.database)

            output_path = Path(output)
            count = await db_manager.export_profiles(output_path)

            show_success(f"Exported {count} profiles to {output_path}")

        except Exception as e:
            show_error(f"Export failed: {e}")
            sys.exit(1)

    asyncio.run(_export())


@profile_app.command("import")
def profile_import(
    input_file: str = typer.Argument(..., help="Input JSON file")
):
    """Import user profiles from JSON."""
    async def _import():
        try:
            input_path = Path(input_file)

            if not input_path.exists():
                show_error(f"File not found: {input_path}")
                sys.exit(1)

            settings = get_settings()
            db_manager = DatabaseManager(settings.paths.database)

            show_warning("This will overwrite existing profiles with matching user IDs!")
            if not typer.confirm("Continue?"):
                show_info("Import cancelled")
                sys.exit(0)

            count = await db_manager.import_profiles(input_path)
            show_success(f"Imported {count} profiles")

        except Exception as e:
            show_error(f"Import failed: {e}")
            sys.exit(1)

    asyncio.run(_import())


# ============================================================================
# STATISTICS COMMANDS
# ============================================================================

stats_app = typer.Typer(help="View bot statistics")
app.add_typer(stats_app, name="stats")


@stats_app.callback(invoke_without_command=True)
def stats_default(ctx: typer.Context):
    """Show general statistics dashboard."""
    if ctx.invoked_subcommand is not None:
        return

    async def _dashboard():
        try:
            settings = get_settings()
            collector = StatsCollector(settings.paths.database)

            general = await collector.get_general_stats()
            top_chats = await collector.get_top_chats(5)
            top_users = await collector.get_top_users(5)
            personas = await collector.get_persona_stats()

            console.print("\n[bold]Bot Statistics Dashboard[/bold]\n")

            # General stats
            console.print("[bold]General[/bold]")
            console.print(f"  Total messages: {general.total_messages}")
            console.print(f"  Bot responses: {general.bot_messages}")
            console.print(f"  Response rate: {general.response_rate:.1f}%")
            console.print(f"  Unique users: {general.unique_users}")
            console.print(f"  Unique chats: {general.unique_chats}")
            console.print(f"  Avg decision score: {general.avg_decision_score:.2f}")
            console.print(f"\n  Today: {general.messages_today} messages, {general.responses_today} responses")
            console.print()

            # Top chats
            if top_chats:
                console.print("[bold]Top Chats[/bold]")
                for i, chat in enumerate(top_chats, 1):
                    console.print(f"  {i}. Chat {chat['chat_id']}: {chat['message_count']} messages")
                console.print()

            # Top users
            if top_users:
                console.print("[bold]Top Users[/bold]")
                for i, user in enumerate(top_users, 1):
                    console.print(f"  {i}. {user['username']}: {user['message_count']} messages")
                console.print()

            # Personas
            if personas:
                console.print("[bold]Persona Usage[/bold]")
                for persona in personas:
                    console.print(f"  {persona.persona_name}: {persona.usage_count} ({persona.percentage:.1f}%)")
                console.print()

        except Exception as e:
            show_error(f"Failed to get statistics: {e}")
            sys.exit(1)

    asyncio.run(_dashboard())


@stats_app.command("chat")
def stats_chat(chat_id: int):
    """Show statistics for a specific chat."""
    async def _stats():
        try:
            settings = get_settings()
            collector = StatsCollector(settings.paths.database)

            stats = await collector.get_chat_stats(chat_id)

            if not stats:
                show_warning(f"No data found for chat {chat_id}")
                sys.exit(1)

            console.print(f"\n[bold]Chat Statistics: {chat_id}[/bold]\n")
            console.print(f"Total messages: {stats.total_messages}")
            console.print(f"Unique users: {stats.unique_users}")
            console.print(f"Bot messages: {stats.bot_messages}")

            if stats.first_message:
                console.print(f"First message: {stats.first_message}")
            if stats.last_message:
                console.print(f"Last message: {stats.last_message}")

            console.print()

        except Exception as e:
            show_error(f"Failed to get chat stats: {e}")
            sys.exit(1)

    asyncio.run(_stats())


@stats_app.command("user")
def stats_user(user_id: int):
    """Show statistics for a specific user."""
    async def _stats():
        try:
            settings = get_settings()
            collector = StatsCollector(settings.paths.database)

            stats = await collector.get_user_stats(user_id)

            if not stats:
                show_warning(f"No data found for user {user_id}")
                sys.exit(1)

            console.print(f"\n[bold]User Statistics: {stats.username}[/bold]\n")
            console.print(f"User ID: {stats.user_id}")
            console.print(f"Total messages: {stats.total_messages}")
            console.print(f"Chats active in: {stats.total_chats}")
            console.print(f"Relationship: {stats.relationship_level}")
            console.print(f"Trust score: {stats.trust_score:+.2f}")
            console.print(f"Interactions: {stats.interaction_count}")

            if stats.first_interaction:
                console.print(f"First interaction: {stats.first_interaction}")
            if stats.last_interaction:
                console.print(f"Last interaction: {stats.last_interaction}")

            console.print()

        except Exception as e:
            show_error(f"Failed to get user stats: {e}")
            sys.exit(1)

    asyncio.run(_stats())


@stats_app.command("persona")
def stats_persona():
    """Show persona usage statistics."""
    async def _stats():
        try:
            settings = get_settings()
            collector = StatsCollector(settings.paths.database)

            personas = await collector.get_persona_stats()

            if not personas:
                console.print("[dim]No persona usage data found[/dim]")
                sys.exit(0)

            console.print("\n[bold]Persona Usage Statistics[/bold]\n")

            table = Table(show_header=True)
            table.add_column("Persona", style="cyan")
            table.add_column("Uses", style="green", justify="right")
            table.add_column("Percentage", style="yellow", justify="right")

            for persona in personas:
                table.add_row(
                    persona.persona_name,
                    str(persona.usage_count),
                    f"{persona.percentage:.1f}%"
                )

            console.print(table)
            console.print()

        except Exception as e:
            show_error(f"Failed to get persona stats: {e}")
            sys.exit(1)

    asyncio.run(_stats())


@stats_app.command("decision")
def stats_decision():
    """Show decision engine statistics."""
    async def _stats():
        try:
            settings = get_settings()
            collector = StatsCollector(settings.paths.database)

            decision_stats = await collector.get_decision_stats()

            console.print("\n[bold]Decision Engine Statistics[/bold]\n")

            console.print(f"Average score: {decision_stats['avg_score']:.3f}")
            console.print(f"Min score: {decision_stats['min_score']:.3f}")
            console.print(f"Max score: {decision_stats['max_score']:.3f}")
            console.print()

            console.print("[bold]Score Distribution[/bold]")
            for range_name, count in decision_stats['distribution'].items():
                console.print(f"  {range_name}: {count}")

            console.print()

        except Exception as e:
            show_error(f"Failed to get decision stats: {e}")
            sys.exit(1)

    asyncio.run(_stats())


@stats_app.command("export")
def stats_export(
    format: str = typer.Option("json", "--format", "-f", help="Export format (json)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path")
):
    """Export all statistics."""
    async def _export():
        try:
            settings = get_settings()
            collector = StatsCollector(settings.paths.database)

            stats_data = await collector.export_stats(format)

            if output:
                output_path = Path(output)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = Path(f"stats_export_{timestamp}.{format}")

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, indent=2, ensure_ascii=False, default=str)

            show_success(f"Exported statistics to {output_path}")

        except Exception as e:
            show_error(f"Failed to export stats: {e}")
            sys.exit(1)

    asyncio.run(_export())


# ============================================================================
# OWNER LEARNING COMMANDS
# ============================================================================

owner_app = typer.Typer(help="Manage owner learning system")
app.add_typer(owner_app, name="owner")


@owner_app.command("setup")
def owner_setup():
    """Interactive setup for owner learning."""
    import questionary
    from questionary import Style

    custom_style = Style([
        ('qmark', 'fg:#7c3aed bold'),
        ('question', 'bold'),
        ('answer', 'fg:#7c3aed bold'),
    ])

    console.print("\n[bold]Owner Learning Setup[/bold]\n")

    try:
        settings = get_settings()
        base_dir = Path(__file__).parent
        config_path = base_dir / "config" / "config.yaml"

        # Get owner user ID
        console.print("[dim]Enter your Telegram user ID (you can find it by messaging @userinfobot)[/dim]\n")

        user_id_str = questionary.text(
            "Your Telegram user ID:",
            validate=lambda x: x.isdigit() or "Must be a number",
            style=custom_style
        ).ask()

        if not user_id_str:
            show_warning("Setup cancelled")
            sys.exit(0)

        owner_id = int(user_id_str)

        # Ask about auto-collect
        auto_collect = questionary.confirm(
            "Enable auto-collection of your messages?",
            default=True,
            style=custom_style
        ).ask()

        if auto_collect is None:
            show_warning("Setup cancelled")
            sys.exit(0)

        # Update config
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if 'owner_learning' not in config:
            config['owner_learning'] = {}

        config['owner_learning']['owner_user_ids'] = [owner_id]
        config['owner_learning']['auto_collect'] = auto_collect
        config['owner_learning']['enabled'] = True

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        show_success("Owner learning configured!")
        console.print(f"\nOwner user ID: {owner_id}")
        console.print(f"Auto-collect: {'enabled' if auto_collect else 'disabled'}\n")

        if auto_collect:
            console.print("[dim]Your messages in group chats will be automatically collected[/dim]")
        else:
            console.print("[dim]Add samples manually to data/owner_samples/messages.txt[/dim]")

        console.print("\n[bold]Next steps:[/bold]")
        console.print("  python3 cli.py owner collect --from-db --limit 100")
        console.print("  python3 cli.py owner analyze")
        console.print()

    except Exception as e:
        show_error(f"Setup failed: {e}")
        sys.exit(1)


@owner_app.command("collect")
def owner_collect(
    from_db: bool = typer.Option(False, "--from-db", help="Collect from database"),
    user_id: Optional[int] = typer.Option(None, "--user-id", help="User ID to collect from"),
    limit: int = typer.Option(100, "--limit", "-n", help="Number of messages to collect")
):
    """Collect owner messages from database."""
    async def _collect():
        try:
            settings = get_settings()

            if not from_db:
                show_warning("Only --from-db mode is currently supported")
                show_info("Usage: python3 cli.py owner collect --from-db --user-id YOUR_ID --limit 100")
                sys.exit(1)

            # Determine user ID
            if user_id is None:
                if settings.owner_learning.owner_user_ids:
                    user_id_to_use = settings.owner_learning.owner_user_ids[0]
                    show_info(f"Using configured owner ID: {user_id_to_use}")
                else:
                    show_error("No owner user ID configured")
                    show_info("Run: python3 cli.py owner setup")
                    sys.exit(1)
            else:
                user_id_to_use = user_id

            # Collect from database
            import aiosqlite
            async with aiosqlite.connect(settings.paths.database) as db:
                cursor = await db.execute(
                    """
                    SELECT text FROM messages
                    WHERE user_id = ? AND persona_mode IS NULL
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (user_id_to_use, limit)
                )
                messages = [row[0] for row in await cursor.fetchall()]

            if not messages:
                show_warning(f"No messages found for user {user_id_to_use}")
                sys.exit(0)

            # Save to manual samples file
            samples_path = Path(settings.owner_learning.manual_samples_path)
            samples_path.parent.mkdir(parents=True, exist_ok=True)

            # Read existing samples
            existing = set()
            if samples_path.exists():
                with open(samples_path, 'r', encoding='utf-8') as f:
                    existing = set(line.strip() for line in f if line.strip() and not line.startswith('#'))

            # Add new unique messages
            new_messages = [msg for msg in messages if msg not in existing]

            if not new_messages:
                show_info("No new messages to add (all already collected)")
                sys.exit(0)

            with open(samples_path, 'a', encoding='utf-8') as f:
                f.write(f"\n# Collected from database on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                for msg in new_messages:
                    f.write(f"{msg}\n")

            show_success(f"Collected {len(new_messages)} new messages")
            show_info(f"Total in file: {len(existing) + len(new_messages)}")
            show_info(f"Saved to: {samples_path}\n")

            if len(existing) + len(new_messages) >= settings.owner_learning.min_samples:
                console.print("[bold]Ready to analyze![/bold]")
                console.print("  python3 cli.py owner analyze\n")
            else:
                needed = settings.owner_learning.min_samples - len(existing) - len(new_messages)
                console.print(f"[dim]Need {needed} more samples for analysis[/dim]\n")

        except Exception as e:
            show_error(f"Collection failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    asyncio.run(_collect())


@owner_app.command("analyze")
def analyze_owner_style():
    """Analyze owner's writing style from samples."""
    try:
        settings = get_settings()

        if not settings.owner_learning.enabled:
            console.print("[yellow]Owner learning is disabled in config[/yellow]")
            return

        owner_learning = OwnerLearningSystem(
            manual_samples_path=settings.owner_learning.manual_samples_path,
            min_samples=settings.owner_learning.min_samples
        )

        if not owner_learning.has_sufficient_samples():
            console.print(f"[yellow]Insufficient samples: {len(owner_learning.samples)}/{settings.owner_learning.min_samples}[/yellow]")
            console.print("[yellow]Add more samples to data/owner_samples/messages.txt[/yellow]")
            return

        analysis = owner_learning.get_analysis()
        if not analysis:
            console.print("[red]No analysis available[/red]")
            return

        console.print(owner_learning.get_style_description())
        console.print(f"\n[bold]Style Instructions:[/bold]")
        console.print(owner_learning.generate_style_instructions())

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@owner_app.command("samples")
def show_owner_samples(n: int = 10):
    """Show random owner message samples."""
    try:
        settings = get_settings()
        owner_learning = OwnerLearningSystem(
            manual_samples_path=settings.owner_learning.manual_samples_path,
            min_samples=settings.owner_learning.min_samples
        )

        samples = owner_learning.get_samples(n)

        console.print(f"\n[bold cyan]📝 Owner Message Samples ({len(samples)} of {len(owner_learning.samples)})[/bold cyan]\n")
        for i, sample in enumerate(samples, 1):
            console.print(f"{i}. {sample}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


# ============================================================================
# MAIN COMMANDS
# ============================================================================

# Config commands group
config_cmd_app = typer.Typer(help="Manage configuration")
app.add_typer(config_cmd_app, name="config")


@config_cmd_app.callback(invoke_without_command=True)
def config_default(ctx: typer.Context):
    """Show current configuration."""
    if ctx.invoked_subcommand is not None:
        return

    from utils.config_display import display_config

    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "config.yaml"
    secrets_path = base_dir / "config" / "secrets.yaml"

    try:
        display_config(config_path, secrets_path)
    except Exception as e:
        show_error(f"Configuration error: {e}")
        sys.exit(1)


@config_cmd_app.command("show")
def config_show():
    """Show current configuration."""
    from utils.config_display import display_config

    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "config.yaml"
    secrets_path = base_dir / "config" / "secrets.yaml"

    try:
        display_config(config_path, secrets_path)
    except Exception as e:
        show_error(f"Configuration error: {e}")
        sys.exit(1)


@config_cmd_app.command("validate")
def config_validate():
    """Validate configuration."""
    try:
        settings = get_settings()

        show_info("Validating configuration...")

        warnings = settings.validate() if hasattr(settings, 'validate') else []

        if not warnings:
            show_success("Configuration is valid!")
        else:
            show_warning("Configuration has warnings:")
            for warning in warnings:
                console.print(f"  ⚠️  {warning}")

    except Exception as e:
        show_error(f"Validation failed: {e}")
        sys.exit(1)


@config_cmd_app.command("edit")
def config_edit():
    """Open config file in editor."""
    import os

    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "config.yaml"

    editor = os.environ.get('EDITOR', 'nano')

    try:
        subprocess.run([editor, str(config_path)])
        show_success("Configuration may have been modified")
        show_info("Run 'python cli.py config validate' to check")
    except Exception as e:
        show_error(f"Failed to open editor: {e}")
        sys.exit(1)


@app.command("version")
def version():
    """Show version information."""
    console.print("[bold cyan]AlphaSnobAI v2.0.0[/bold cyan]")
    console.print("Advanced Telegram UserBot with Multi-Persona System")


if __name__ == "__main__":
    app()
