"""Beautiful configuration display in Claude Code style."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from pathlib import Path
import yaml

console = Console()


def display_config(config_path: Path, secrets_path: Path):
    """Display configuration in beautiful Claude Code style."""
    
    if not config_path.exists():
        console.print("[red]✗[/red] Configuration not found. Run [cyan]python cli.py setup[/cyan]")
        return
    
    # Load config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    secrets = {}
    if secrets_path.exists():
        with open(secrets_path, 'r', encoding='utf-8') as f:
            secrets = yaml.safe_load(f)
    
    # Header
    console.print()
    title = Text()
    title.append("⚙️  ", style="bold cyan")
    title.append("AlphaSnobAI Configuration", style="bold white")
    console.print(Panel(title, border_style="cyan"))
    console.print()
    
    # Persona Section
    persona = config.get('persona', {})
    persona_table = Table(show_header=False, box=None, padding=(0, 2))
    persona_table.add_column("Key", style="dim")
    persona_table.add_column("Value", style="cyan")
    
    persona_table.add_row("Default Mode", f"🎭 {persona.get('default_mode', 'N/A')}")
    persona_table.add_row("Adaptive Switching", "✓" if persona.get('adaptive_switching') else "✗")
    
    console.print(Panel(
        persona_table,
        title="[bold cyan]Persona System[/bold cyan]",
        border_style="blue",
        padding=(1, 2)
    ))
    console.print()
    
    # LLM Section
    llm = config.get('llm', {})
    llm_secrets = secrets.get('llm', {})
    
    provider = llm.get('provider', 'N/A')
    provider_icon = "🟣" if provider == "claude" else "🟢"
    
    api_key = llm_secrets.get('anthropic_api_key' if provider == 'claude' else 'openai_api_key', '')
    api_key_display = f"{api_key[:10]}...{api_key[-4:]}" if api_key else "Not set"
    
    llm_table = Table(show_header=False, box=None, padding=(0, 2))
    llm_table.add_column("Key", style="dim")
    llm_table.add_column("Value", style="green")
    
    llm_table.add_row("Provider", f"{provider_icon} {provider}")
    llm_table.add_row("Model", llm.get('model', 'N/A'))
    llm_table.add_row("Temperature", str(llm.get('temperature', 'N/A')))
    llm_table.add_row("Max Tokens", str(llm.get('max_tokens', 'N/A')))
    llm_table.add_row("API Key", f"[dim]{api_key_display}[/dim]")
    
    console.print(Panel(
        llm_table,
        title="[bold green]LLM Configuration[/bold green]",
        border_style="green",
        padding=(1, 2)
    ))
    console.print()
    
    # Decision Engine
    decision = config.get('decision', {})
    
    decision_table = Table(show_header=False, box=None, padding=(0, 2))
    decision_table.add_column("Key", style="dim")
    decision_table.add_column("Value", style="yellow")
    
    decision_table.add_row("Base Probability", f"{decision.get('base_probability', 0) * 100:.0f}%")
    
    rel_mults = decision.get('relationship_multipliers', {})
    decision_table.add_row("", "")
    decision_table.add_row("[bold]Relationship Multipliers", "")
    for rel, mult in rel_mults.items():
        decision_table.add_row(f"  {rel}", f"{mult}x")
    
    time_based = decision.get('time_based', {})
    decision_table.add_row("", "")
    decision_table.add_row("[bold]Time-based", "")
    decision_table.add_row("  Quiet hours", f"{time_based.get('quiet_hours_start')}-{time_based.get('quiet_hours_end')}")
    decision_table.add_row("  Quiet multiplier", f"{time_based.get('quiet_hours_multiplier')}x")
    
    cooldown = decision.get('cooldown', {})
    decision_table.add_row("", "")
    decision_table.add_row("[bold]Cooldown", "")
    decision_table.add_row("  Enabled", "✓" if cooldown.get('enabled') else "✗")
    decision_table.add_row("  Min between", f"{cooldown.get('min_seconds_between_responses')}s")
    decision_table.add_row("  Max consecutive", str(cooldown.get('max_consecutive_responses')))
    
    console.print(Panel(
        decision_table,
        title="[bold yellow]Decision Engine[/bold yellow]",
        border_style="yellow",
        padding=(1, 2)
    ))
    console.print()
    
    # Features Grid
    typing_enabled = config.get('typing', {}).get('enabled', False)
    profiling_enabled = config.get('profiling', {}).get('enabled', False)
    owner_learning_enabled = config.get('owner_learning', {}).get('enabled', False)
    auto_upgrade_enabled = config.get('profiling', {}).get('auto_upgrade', {}).get('enabled', False)
    
    features_table = Table(show_header=False, box=None, padding=(0, 2))
    features_table.add_column("Feature", style="dim")
    features_table.add_column("Status", justify="right")
    
    features_table.add_row(
        "⌨️  Typing Simulation",
        "[green]✓ Enabled[/green]" if typing_enabled else "[dim]✗ Disabled[/dim]"
    )
    features_table.add_row(
        "👤 User Profiling",
        "[green]✓ Enabled[/green]" if profiling_enabled else "[dim]✗ Disabled[/dim]"
    )
    features_table.add_row(
        "📈 Auto-upgrade Relationships",
        "[green]✓ Enabled[/green]" if auto_upgrade_enabled else "[dim]✗ Disabled[/dim]"
    )
    features_table.add_row(
        "📚 Owner Learning",
        "[green]✓ Enabled[/green]" if owner_learning_enabled else "[dim]✗ Disabled[/dim]"
    )
    
    console.print(Panel(
        features_table,
        title="[bold magenta]Features[/bold magenta]",
        border_style="magenta",
        padding=(1, 2)
    ))
    console.print()
    
    # Paths
    paths = config.get('paths', {})
    
    paths_table = Table(show_header=False, box=None, padding=(0, 2))
    paths_table.add_column("Type", style="dim")
    paths_table.add_column("Path", style="blue")
    
    paths_table.add_row("Database", paths.get('database', 'N/A'))
    paths_table.add_row("Corpus", paths.get('corpus', 'N/A'))
    paths_table.add_row("Logs", paths.get('logs', 'N/A'))
    
    console.print(Panel(
        paths_table,
        title="[bold blue]Paths[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    ))
    console.print()
    
    # Quick Commands
    console.print("[bold]Quick Commands:[/bold]")
    console.print("  [cyan]python cli.py setup[/cyan]          - Reconfigure settings")
    console.print("  [cyan]python cli.py persona list[/cyan]   - View available personas")
    console.print("  [cyan]python cli.py profile list[/cyan]   - View user profiles")
    console.print("  [cyan]python bot/runner.py[/cyan]         - Start bot (interactive)")
    console.print()
