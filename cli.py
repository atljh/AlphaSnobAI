#!/usr/bin/env python3
"""AlphaSnobAI CLI - Command-line interface for bot management."""

import asyncio
import sys
from pathlib import Path
from typing import Optional
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

app = typer.Typer(help="AlphaSnobAI - Advanced Telegram UserBot")
console = Console()


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


# ============================================================================
# STATISTICS COMMANDS
# ============================================================================

stats_app = typer.Typer(help="View bot statistics")
app.add_typer(stats_app, name="stats")


@stats_app.command("chat")
def chat_stats(chat_id: int):
    """Show statistics for a specific chat."""
    async def _stats():
        try:
            settings = get_settings()
            memory = Memory(settings.paths.database)
            await memory.initialize()

            stats = await memory.get_chat_statistics(chat_id)

            console.print(f"\n[bold cyan]📊 Chat Statistics for {chat_id}[/bold cyan]")
            console.print(f"[bold]Total Messages:[/bold] {stats['total_messages']}")
            console.print(f"[bold]Unique Users:[/bold] {stats['unique_users']}")

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)

    asyncio.run(_stats())


# ============================================================================
# OWNER LEARNING COMMANDS
# ============================================================================

owner_app = typer.Typer(help="Manage owner learning system")
app.add_typer(owner_app, name="owner")


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

@app.command("config")
def show_config():
    """Show current configuration."""
    try:
        settings = get_settings()

        console.print("\n[bold cyan]⚙️  AlphaSnobAI Configuration[/bold cyan]\n")

        console.print(f"[bold]Bot Mode:[/bold] {settings.bot.response_mode}")
        console.print(f"[bold]Default Persona:[/bold] {settings.persona.default_mode}")
        console.print(f"[bold]LLM Provider:[/bold] {settings.llm.provider} ({settings.llm.model})")
        console.print(f"[bold]Typing Simulation:[/bold] {'Enabled' if settings.typing.enabled else 'Disabled'}")
        console.print(f"[bold]User Profiling:[/bold] {'Enabled' if settings.profiling.enabled else 'Disabled'}")
        console.print(f"[bold]Owner Learning:[/bold] {'Enabled' if settings.owner_learning.enabled else 'Disabled'}")
        console.print(f"[bold]Decision Base Probability:[/bold] {settings.decision.base_probability}")

        console.print(f"\n[bold]Paths:[/bold]")
        console.print(f"  Database: {settings.paths.database}")
        console.print(f"  Corpus: {settings.paths.corpus}")
        console.print(f"  Logs: {settings.paths.logs}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@app.command("version")
def version():
    """Show version information."""
    console.print("[bold cyan]AlphaSnobAI v2.0.0[/bold cyan]")
    console.print("Advanced Telegram UserBot with Multi-Persona System")


if __name__ == "__main__":
    app()
