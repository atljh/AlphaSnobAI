"""Minimal configuration display."""

from rich.console import Console
from pathlib import Path
import yaml

console = Console()


def display_config(config_path: Path, secrets_path: Path):
    """Display configuration in minimal style."""

    if not config_path.exists():
        console.print("Configuration not found")
        console.print("Run: python cli.py setup")
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
    console.print("[bold]AlphaSnobAI Configuration[/bold]")
    console.print()
    
    # Persona Section
    persona = config.get('persona', {})
    console.print("[bold]Persona[/bold]")
    console.print(f"  Default mode: {persona.get('default_mode', 'N/A')}")
    console.print(f"  Adaptive switching: {'yes' if persona.get('adaptive_switching') else 'no'}")
    console.print()
    
    # LLM Section
    llm = config.get('llm', {})
    llm_secrets = secrets.get('llm', {})

    provider = llm.get('provider', 'N/A')
    api_key = llm_secrets.get('anthropic_api_key' if provider == 'claude' else 'openai_api_key', '')
    api_key_display = f"{api_key[:10]}...{api_key[-4:]}" if api_key else "Not set"

    console.print("[bold]LLM[/bold]")
    console.print(f"  Provider: {provider}")
    console.print(f"  Model: {llm.get('model', 'N/A')}")
    console.print(f"  Temperature: {llm.get('temperature', 'N/A')}")
    console.print(f"  Max tokens: {llm.get('max_tokens', 'N/A')}")
    console.print(f"  API key: [dim]{api_key_display}[/dim]")
    console.print()
    
    # Decision Engine
    decision = config.get('decision', {})
    console.print("[bold]Decision Engine[/bold]")
    console.print(f"  Base probability: {decision.get('base_probability', 0) * 100:.0f}%")

    cooldown = decision.get('cooldown', {})
    console.print(f"  Cooldown: {'enabled' if cooldown.get('enabled') else 'disabled'}")
    console.print(f"  Min between responses: {cooldown.get('min_seconds_between_responses', 0)}s")
    console.print()
    
    # Features
    typing_enabled = config.get('typing', {}).get('enabled', False)
    profiling_enabled = config.get('profiling', {}).get('enabled', False)
    owner_learning_enabled = config.get('owner_learning', {}).get('enabled', False)

    console.print("[bold]Features[/bold]")
    console.print(f"  Typing simulation: {'enabled' if typing_enabled else 'disabled'}")
    console.print(f"  User profiling: {'enabled' if profiling_enabled else 'disabled'}")
    console.print(f"  Owner learning: {'enabled' if owner_learning_enabled else 'disabled'}")
    console.print()
    
    # Paths
    paths = config.get('paths', {})
    console.print("[bold]Paths[/bold]")
    console.print(f"  Database: {paths.get('database', 'N/A')}")
    console.print(f"  Corpus: {paths.get('corpus', 'N/A')}")
    console.print(f"  Logs: {paths.get('logs', 'N/A')}")
    console.print()

    # Quick Commands
    console.print("[bold]Commands[/bold]")
    console.print("  python cli.py setup")
    console.print("  python cli.py persona list")
    console.print("  python cli.py profile list")
    console.print("  python bot/runner.py")
    console.print()
