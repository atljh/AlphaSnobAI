"""Interactive setup wizard for AlphaSnobAI configuration."""

import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from pathlib import Path
import yaml

console = Console()

# Claude Code style theme
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),       # Purple question mark
    ('question', 'bold'),                # Bold questions
    ('answer', 'fg:#2196f3 bold'),      # Blue answers
    ('pointer', 'fg:#673ab7 bold'),     # Purple pointer
    ('highlighted', 'fg:#673ab7 bold'), # Purple highlight
    ('selected', 'fg:#2196f3'),         # Blue selected
    ('separator', 'fg:#666666'),        # Gray separator
    ('instruction', 'fg:#888888'),      # Gray instructions
    ('text', ''),                        # Normal text
])


def print_header():
    """Print beautiful header."""
    header = Text()
    header.append("🎭 ", style="bold magenta")
    header.append("AlphaSnobAI Setup Wizard", style="bold cyan")
    
    console.print()
    console.print(Panel(
        header,
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()


def print_section(title: str, description: str = None):
    """Print section header."""
    console.print()
    console.print(f"[bold cyan]▸ {title}[/bold cyan]")
    if description:
        console.print(f"[dim]{description}[/dim]")
    console.print()


def setup_persona():
    """Configure persona settings."""
    print_section(
        "🎭 Persona Configuration",
        "Choose which personality the bot should use by default"
    )
    
    persona_choice = questionary.select(
        "Default persona mode:",
        choices=[
            questionary.Choice("👑 Owner Style - Mimic your writing (recommended)", value="owner"),
            questionary.Choice("😈 AlphaSnob - Aggressive troll mode", value="alphasnob"),
            questionary.Choice("😊 Normal User - Friendly and casual", value="normal"),
        ],
        style=custom_style
    ).ask()
    
    return {
        'default_mode': persona_choice,
        'user_overrides': {},
        'chat_overrides': {},
        'adaptive_switching': True
    }


def setup_llm():
    """Configure LLM provider."""
    print_section(
        "🤖 AI Provider Configuration",
        "Choose which AI service to use for generating responses"
    )
    
    provider = questionary.select(
        "Select LLM provider:",
        choices=[
            questionary.Choice("🟣 Claude (Anthropic) - High quality, best for complex responses", value="claude"),
            questionary.Choice("🟢 OpenAI (GPT-4) - Fast and reliable", value="openai"),
        ],
        style=custom_style
    ).ask()
    
    # Ask for API key
    console.print()
    if provider == "claude":
        api_key = questionary.password(
            "Enter your Anthropic API key (starts with sk-ant-):",
            style=custom_style
        ).ask()
        model = "claude-3-5-sonnet-20241022"
    else:
        api_key = questionary.password(
            "Enter your OpenAI API key (starts with sk-):",
            style=custom_style
        ).ask()
        model = questionary.select(
            "Select OpenAI model:",
            choices=[
                questionary.Choice("gpt-4o-mini - Fast and cheap", value="gpt-4o-mini"),
                questionary.Choice("gpt-4o - Most capable", value="gpt-4o"),
            ],
            style=custom_style
        ).ask()
    
    temperature_choices = [
        questionary.Choice("0.7 - Conservative", value=0.7),
        questionary.Choice("0.9 - Balanced (recommended)", value=0.9),
        questionary.Choice("1.2 - Very creative", value=1.2),
    ]

    temperature = questionary.select(
        "Response creativity (temperature):",
        choices=temperature_choices,
        style=custom_style,
        default=temperature_choices[1]  # 0.9 - Balanced
    ).ask()
    
    return {
        'provider': provider,
        'model': model,
        'temperature': temperature,
        'max_tokens': 500
    }, api_key


def setup_behavior():
    """Configure bot behavior."""
    print_section(
        "⚙️ Response Behavior",
        "Configure how often and when the bot responds"
    )
    
    response_mode = questionary.select(
        "Response mode:",
        choices=[
            questionary.Choice("🎲 Probability - Smart decision based on context (recommended)", value="probability"),
            questionary.Choice("✅ All - Respond to every message", value="all"),
            questionary.Choice("👤 Specific users - Only respond to certain people", value="specific_users"),
            questionary.Choice("@️ Mentioned - Only when tagged or replied to", value="mentioned"),
        ],
        style=custom_style
    ).ask()
    
    base_probability = 0.8
    if response_mode == "probability":
        base_probability = questionary.select(
            "Base response probability:",
            choices=[
                questionary.Choice("30% - Rare responses", value=0.3),
                questionary.Choice("50% - Moderate", value=0.5),
                questionary.Choice("80% - Frequent (recommended)", value=0.8),
                questionary.Choice("100% - Always (if conditions met)", value=1.0),
            ],
            style=custom_style,
            default="80% - Frequent (recommended)"
        ).ask()
    
    typing_enabled = questionary.confirm(
        "Enable realistic typing simulation? (shows 'typing...' action)",
        default=True,
        style=custom_style
    ).ask()
    
    return {
        'response_mode': response_mode,
        'base_probability': base_probability,
        'typing_enabled': typing_enabled
    }


def setup_owner_learning():
    """Configure owner learning."""
    print_section(
        "📚 Owner Style Learning",
        "Learn from your message samples to perfectly mimic your writing"
    )
    
    enable_learning = questionary.confirm(
        "Enable owner style learning?",
        default=False,
        style=custom_style
    ).ask()
    
    if enable_learning:
        console.print()
        console.print("[yellow]ℹ️  You'll need to add 50+ message samples to:[/yellow]")
        console.print("[cyan]   data/owner_samples/messages.txt[/cyan]")
        console.print()
        console.print("[dim]Run 'python cli.py owner analyze' after adding samples[/dim]")
    
    return {
        'enabled': enable_learning,
        'min_samples': 50
    }


def setup_telegram():
    """Configure Telegram credentials."""
    print_section(
        "📱 Telegram Configuration",
        "Get these from https://my.telegram.org/apps"
    )
    
    console.print("[yellow]ℹ️  Create a Telegram app at: https://my.telegram.org/apps[/yellow]")
    console.print()
    
    api_id = questionary.text(
        "Enter your Telegram API ID:",
        validate=lambda x: x.isdigit() or "Must be a number",
        style=custom_style
    ).ask()
    
    api_hash = questionary.password(
        "Enter your Telegram API Hash:",
        validate=lambda x: len(x) > 0 or "Cannot be empty",
        style=custom_style
    ).ask()
    
    phone = questionary.text(
        "Enter your phone number (with country code, e.g., +79991234567):",
        validate=lambda x: x.startswith('+') or "Must start with +",
        style=custom_style
    ).ask()
    
    return {
        'api_id': int(api_id),
        'api_hash': api_hash,
        'phone': phone
    }


def show_current_config(config_path: Path, secrets_path: Path):
    """Show current configuration if it exists."""
    if not config_path.exists():
        return None, None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        secrets = None
        if secrets_path.exists():
            with open(secrets_path, 'r', encoding='utf-8') as f:
                secrets = yaml.safe_load(f)

        # Show current settings
        console.print()
        console.print(Panel(
            "[bold cyan]Current Configuration[/bold cyan]\n\n"
            f"[dim]Persona:[/dim] {config.get('persona', {}).get('default_mode', 'N/A')}\n"
            f"[dim]LLM Provider:[/dim] {config.get('llm', {}).get('provider', 'N/A')}\n"
            f"[dim]Response Mode:[/dim] {config.get('bot', {}).get('response_mode', 'N/A')}\n"
            f"[dim]Typing Simulation:[/dim] {config.get('typing', {}).get('enabled', False)}\n"
            f"[dim]Owner Learning:[/dim] {config.get('owner_learning', {}).get('enabled', False)}",
            border_style="cyan",
            padding=(1, 2)
        ))
        console.print()

        return config, secrets
    except Exception as e:
        console.print(f"[yellow]⚠️  Could not read existing config: {e}[/yellow]")
        return None, None


def run_setup_wizard(config_path: Path, secrets_path: Path):
    """Run the interactive setup wizard."""
    print_header()

    console.print("[bold green]Welcome to AlphaSnobAI! Let's set up your bot.[/bold green]")

    # Show current config if exists
    existing_config, existing_secrets = show_current_config(config_path, secrets_path)

    # Check if already configured
    if config_path.exists():
        reconfigure = questionary.confirm(
            "Reconfigure settings?",
            default=False,
            style=custom_style
        ).ask()

        if not reconfigure:
            console.print()
            console.print("[yellow]✓ Keeping current configuration[/yellow]")
            return False
    
    # Persona
    persona_config = setup_persona()
    
    # LLM
    llm_config, api_key = setup_llm()
    
    # Behavior
    behavior_config = setup_behavior()
    
    # Owner learning
    owner_config = setup_owner_learning()
    
    # Telegram (only ask if secrets don't exist)
    telegram_config = None
    if not secrets_path.exists():
        telegram_config = setup_telegram()
    
    # Build configuration
    print_section("💾 Saving Configuration", "Writing configuration files...")
    
    config = {
        'telegram': {
            'session_name': 'alphasnob_session'
        },
        'llm': llm_config,
        'bot': {
            'response_mode': behavior_config['response_mode'],
            'response_probability': 0.3,
            'allowed_users': [],
            'context_length': 50
        },
        'paths': {
            'corpus': 'olds.txt',
            'database': 'data/context.db',
            'logs': 'logs/alphasnob.log'
        },
        'daemon': {
            'pid_file': 'data/alphasnob.pid',
            'log_level': 'INFO',
            'auto_restart': False
        },
        'persona': persona_config,
        'typing': {
            'enabled': behavior_config['typing_enabled'],
            'read_delay': {'min_ms': 500, 'max_ms': 3000, 'per_word_ms': 150},
            'typing_action': {
                'enabled': True,
                'base_delay_ms': 1000,
                'per_character_ms': 50,
                'min_ms': 1000,
                'max_ms': 20000,
                'randomness': 0.3
            },
            'thinking_delay': {'min_ms': 500, 'max_ms': 2500}
        },
        'decision': {
            'base_probability': behavior_config['base_probability'],
            'relationship_multipliers': {
                'owner': 1.0,
                'close_friend': 0.9,
                'friend': 0.7,
                'acquaintance': 0.5,
                'stranger': 0.3
            },
            'time_based': {
                'enabled': True,
                'quiet_hours_start': 23,
                'quiet_hours_end': 8,
                'quiet_hours_multiplier': 0.2
            },
            'topic_based': {
                'enabled': True,
                'boring_topics': ['weather', 'погода', 'sports', 'спорт'],
                'boring_topic_multiplier': 0.4,
                'interesting_topics': ['music', 'музыка', 'philosophy', 'философия'],
                'interesting_topic_multiplier': 1.5
            },
            'context_aware': {
                'enabled': True,
                'recent_response_cooldown_seconds': 60,
                'max_consecutive_responses': 3,
                'consecutive_response_multiplier': 0.5
            },
            'cooldown': {
                'enabled': True,
                'min_seconds_between_responses': 30,
                'max_consecutive_responses': 3,
                'reset_after_seconds': 300
            }
        },
        'profiling': {
            'enabled': True,
            'auto_upgrade': {
                'enabled': True,
                'stranger_to_acquaintance': 5,
                'acquaintance_to_friend': 20,
                'friend_to_close_friend': 100
            },
            'trust_adjustment': {
                'positive_markers': ['спасибо', 'thanks', 'круто', 'cool'],
                'negative_markers': ['тупой', 'stupid', 'идиот'],
                'adjustment_amount': 0.1
            }
        },
        'owner_learning': {
            'enabled': owner_config['enabled'],
            'owner_user_ids': [],
            'auto_collect': False,
            'collection_path': 'data/owner_collection/',
            'manual_samples_path': 'data/owner_samples/messages.txt',
            'analyze_on_startup': False,
            'min_samples': owner_config['min_samples']
        },
        'language': {
            'auto_detect': True,
            'supported': ['ru', 'en'],
            'default': 'ru'
        }
    }
    
    secrets = {
        'llm': {}
    }
    
    if llm_config['provider'] == 'claude':
        secrets['llm']['anthropic_api_key'] = api_key
        secrets['llm']['openai_api_key'] = None
    else:
        secrets['llm']['anthropic_api_key'] = None
        secrets['llm']['openai_api_key'] = api_key
    
    if telegram_config:
        secrets['telegram'] = telegram_config
    
    # Save files
    config_path.parent.mkdir(parents=True, exist_ok=True)
    secrets_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    with open(secrets_path, 'w', encoding='utf-8') as f:
        yaml.dump(secrets, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    # Success message
    console.print()
    console.print(Panel(
        "[bold green]✨ Configuration saved successfully![/bold green]\n\n"
        f"[cyan]Persona:[/cyan] {persona_config['default_mode']}\n"
        f"[cyan]LLM:[/cyan] {llm_config['provider']} ({llm_config['model']})\n"
        f"[cyan]Response mode:[/cyan] {behavior_config['response_mode']}\n"
        f"[cyan]Typing simulation:[/cyan] {'Enabled' if behavior_config['typing_enabled'] else 'Disabled'}\n"
        f"[cyan]Owner learning:[/cyan] {'Enabled' if owner_config['enabled'] else 'Disabled'}",
        title="Setup Complete",
        border_style="green"
    ))
    
    console.print()
    console.print("[bold cyan]Next steps:[/bold cyan]")
    console.print("  1. Run: [cyan]python bot/runner.py[/cyan]")
    console.print("  2. Authenticate with Telegram when prompted")
    console.print("  3. Start chatting!")
    
    if owner_config['enabled']:
        console.print()
        console.print("[yellow]⚠️  Don't forget to add message samples to:[/yellow]")
        console.print("[cyan]   data/owner_samples/messages.txt[/cyan]")
    
    console.print()
    
    return True
