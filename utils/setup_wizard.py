"""Interactive setup wizard for AlphaSnobAI configuration - Claude Code style."""

import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import yaml
import time

console = Console()

# Claude Code style theme
custom_style = Style([
    ('qmark', 'fg:#7c3aed bold'),       # Purple question mark
    ('question', 'bold'),                # Bold questions
    ('answer', 'fg:#7c3aed bold'),      # Purple answers
    ('pointer', 'fg:#7c3aed bold'),     # Purple pointer
    ('highlighted', 'fg:#7c3aed bold'), # Purple highlight
    ('selected', 'fg:#7c3aed'),         # Purple selected
    ('separator', 'fg:#666666'),        # Gray separator
    ('instruction', 'fg:#888888'),      # Gray instructions
    ('text', ''),                        # Normal text
])


def print_header():
    """Print minimal header."""
    console.print()
    console.print("[bold]AlphaSnobAI Setup[/bold]")
    console.print()


def print_step(number: int, total: int, title: str):
    """Print step header."""
    console.print()
    console.print(f"[dim]{number}/{total}[/dim] [bold]{title}[/bold]")
    console.print()


def setup_persona():
    """Configure persona settings."""
    print_step(1, 5, "Bot Personality")

    persona_choice = questionary.select(
        "Select personality:",
        choices=[
            questionary.Choice("Owner Mode — Mimics your writing style", value="owner"),
            questionary.Choice("AlphaSnob — Aggressive troll", value="alphasnob"),
            questionary.Choice("Normal — Friendly assistant", value="normal"),
        ],
        style=custom_style
    ).ask()
    
    if persona_choice is None:
        raise KeyboardInterrupt
    
    return {
        'default_mode': persona_choice,
        'user_overrides': {},
        'chat_overrides': {},
        'adaptive_switching': True
    }


def setup_llm():
    """Configure LLM provider."""
    print_step(2, 5, "AI Provider")

    provider = questionary.select(
        "Select AI provider:",
        choices=[
            questionary.Choice("Anthropic Claude", value="claude"),
            questionary.Choice("OpenAI", value="openai"),
        ],
        style=custom_style
    ).ask()
    
    if provider is None:
        raise KeyboardInterrupt
    
    console.print()
    if provider == "claude":
        api_key = questionary.password(
            "Anthropic API key:",
            style=custom_style
        ).ask()
        if api_key is None:
            raise KeyboardInterrupt
        model = "claude-3-5-sonnet-20241022"
    else:
        api_key = questionary.password(
            "OpenAI API key:",
            style=custom_style
        ).ask()
        if api_key is None:
            raise KeyboardInterrupt
        model = questionary.select(
            "Select model:",
            choices=[
                questionary.Choice("gpt-4o-mini", value="gpt-4o-mini"),
                questionary.Choice("gpt-4o", value="gpt-4o"),
            ],
            style=custom_style
        ).ask()
        if model is None:
            raise KeyboardInterrupt
    
    temperature_choices = [
        questionary.Choice("Conservative (0.7)", value=0.7),
        questionary.Choice("Balanced (0.9)", value=0.9),
        questionary.Choice("Creative (1.2)", value=1.2),
    ]

    temperature = questionary.select(
        "Temperature:",
        choices=temperature_choices,
        style=custom_style,
        default=temperature_choices[1]
    ).ask()
    
    if temperature is None:
        raise KeyboardInterrupt
    
    return {
        'provider': provider,
        'model': model,
        'temperature': temperature,
        'max_tokens': 500
    }, api_key


def setup_behavior():
    """Configure bot behavior."""
    print_step(3, 5, "Response Behavior")

    response_mode = questionary.select(
        "When should the bot respond:",
        choices=[
            questionary.Choice("Smart decisions (recommended)", value="probability"),
            questionary.Choice("Every message", value="all"),
            questionary.Choice("Specific users only", value="specific_users"),
            questionary.Choice("When mentioned", value="mentioned"),
        ],
        style=custom_style
    ).ask()
    
    if response_mode is None:
        raise KeyboardInterrupt
    
    base_probability = 0.8
    if response_mode == "probability":
        prob_choices = [
            questionary.Choice("Rare (30%)", value=0.3),
            questionary.Choice("Moderate (50%)", value=0.5),
            questionary.Choice("Frequent (80%)", value=0.8),
            questionary.Choice("Always (100%)", value=1.0),
        ]
        base_probability = questionary.select(
            "Response probability:",
            choices=prob_choices,
            style=custom_style,
            default=prob_choices[2]
        ).ask()
        if base_probability is None:
            raise KeyboardInterrupt

    typing_enabled = questionary.confirm(
        "Enable typing simulation:",
        default=True,
        style=custom_style
    ).ask()
    
    if typing_enabled is None:
        raise KeyboardInterrupt
    
    return {
        'response_mode': response_mode,
        'base_probability': base_probability,
        'typing_enabled': typing_enabled
    }


def setup_owner_learning():
    """Configure owner learning."""
    print_step(4, 5, "Owner Learning")

    console.print("[dim]Learn from your messages to mimic your style[/dim]")
    console.print()

    enable_learning = questionary.confirm(
        "Enable owner learning:",
        default=False,
        style=custom_style
    ).ask()

    if enable_learning is None:
        raise KeyboardInterrupt

    if enable_learning:
        console.print()
        console.print("[dim]→ Add 50+ messages to data/owner_samples/messages.txt[/dim]")
        console.print("[dim]→ Run python cli.py owner analyze[/dim]")
    
    return {
        'enabled': enable_learning,
        'min_samples': 50
    }


def setup_telegram(existing_telegram=None):
    """Configure Telegram credentials."""
    print_step(5, 5, "Telegram")

    if existing_telegram:
        console.print("[dim]Found existing credentials[/dim]")
        console.print()
        use_existing = questionary.confirm(
            "Keep existing settings:",
            default=True,
            style=custom_style
        ).ask()

        if use_existing is None:
            raise KeyboardInterrupt

        if use_existing:
            return existing_telegram

    console.print("[dim]Get your credentials at https://my.telegram.org/apps[/dim]")
    console.print()
    
    api_id = questionary.text(
        "API ID:",
        validate=lambda x: x.isdigit() or "Must be a number",
        style=custom_style
    ).ask()
    
    if api_id is None:
        raise KeyboardInterrupt
    
    api_hash = questionary.password(
        "API Hash:",
        validate=lambda x: len(x) > 0 or "Cannot be empty",
        style=custom_style
    ).ask()
    
    if api_hash is None:
        raise KeyboardInterrupt
    
    phone = questionary.text(
        "Phone number (with +):",
        validate=lambda x: x.startswith('+') or "Must start with +",
        style=custom_style
    ).ask()
    
    if phone is None:
        raise KeyboardInterrupt
    
    return {
        'api_id': int(api_id),
        'api_hash': api_hash,
        'phone': phone
    }


def run_setup_wizard(config_path: Path, secrets_path: Path):
    """Run the interactive setup wizard."""
    print_header()
    
    # Load existing configs
    existing_config = None
    existing_secrets = None
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                existing_config = yaml.safe_load(f)
        except:
            pass
    
    if secrets_path.exists():
        try:
            with open(secrets_path, 'r', encoding='utf-8') as f:
                existing_secrets = yaml.safe_load(f)
        except:
            pass
    
    # Show existing config
    if existing_config:
        console.print("[bold]Current configuration[/bold]")
        console.print(f"  Persona: {existing_config.get('persona', {}).get('default_mode', 'N/A')}")
        console.print(f"  Provider: {existing_config.get('llm', {}).get('provider', 'N/A')}")
        console.print(f"  Response: {existing_config.get('bot', {}).get('response_mode', 'N/A')}")
        console.print()

        reconfigure = questionary.confirm(
            "Reconfigure:",
            default=False,
            style=custom_style
        ).ask()

        if reconfigure is None:
            raise KeyboardInterrupt

        if not reconfigure:
            console.print()
            console.print("Keeping current configuration")
            return False
    
    console.print()
    
    # Run setup steps
    persona_config = setup_persona()
    llm_config, api_key = setup_llm()
    behavior_config = setup_behavior()
    owner_config = setup_owner_learning()
    
    # Get existing telegram config
    existing_telegram = None
    if existing_secrets and 'telegram' in existing_secrets:
        existing_telegram = existing_secrets['telegram']
    
    telegram_config = setup_telegram(existing_telegram)
    
    # Build configuration
    console.print()
    console.print("Saving configuration...")

    with Progress(
        SpinnerColumn(spinner_name="dots", style="magenta"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("", total=None)
        
        config = {
            'telegram': {'session_name': 'alphasnob_session'},
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
                    'boring_topics': ['weather', 'погода'],
                    'boring_topic_multiplier': 0.4,
                    'interesting_topics': ['music', 'музыка'],
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
                    'positive_markers': ['спасибо', 'thanks'],
                    'negative_markers': ['тупой', 'stupid'],
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
            'telegram': telegram_config,
            'llm': {
                'anthropic_api_key': api_key if llm_config['provider'] == 'claude' else None,
                'openai_api_key': api_key if llm_config['provider'] == 'openai' else None
            }
        }
        
        # Save files
        config_path.parent.mkdir(parents=True, exist_ok=True)
        secrets_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        with open(secrets_path, 'w', encoding='utf-8') as f:
            yaml.dump(secrets, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        time.sleep(0.3)
    
    # Success
    console.print()
    console.print("[bold]Setup complete[/bold]")
    console.print()

    console.print(f"Persona: {persona_config['default_mode']}")
    console.print(f"Provider: {llm_config['provider']} ({llm_config['model']})")
    console.print(f"Response: {behavior_config['response_mode']}")
    console.print(f"Typing: {'enabled' if behavior_config['typing_enabled'] else 'disabled'}")
    console.print()

    console.print("[bold]Next steps[/bold]")
    console.print("  python bot/runner.py")
    console.print()

    if owner_config['enabled']:
        console.print("[dim]Add samples to data/owner_samples/messages.txt[/dim]")
        console.print()
    
    return True
