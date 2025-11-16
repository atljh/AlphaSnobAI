"""Configuration management for AlphaSnobAI using YAML."""

import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class TelegramConfig:
    """Telegram configuration."""
    session_name: str
    api_id: int
    api_hash: str


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: str
    model: str
    temperature: float
    max_tokens: int
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None


@dataclass
class BotConfig:
    """Bot behavior configuration."""
    response_mode: str
    response_probability: float
    allowed_users: List[int] = field(default_factory=list)
    context_length: int = 50


@dataclass
class PathsConfig:
    """Paths configuration."""
    corpus: Path
    database: Path
    logs: Path


@dataclass
class DaemonConfig:
    """Daemon configuration."""
    pid_file: Path
    log_level: str
    auto_restart: bool = False


class Settings:
    """Application settings loaded from YAML files."""

    def __init__(self, config_path: Optional[Path] = None, secrets_path: Optional[Path] = None):
        """Initialize settings from YAML files.

        Args:
            config_path: Path to config.yaml (defaults to config/config.yaml)
            secrets_path: Path to secrets.yaml (defaults to config/secrets.yaml)
        """
        # Default paths
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"

        if config_path is None:
            config_path = self.config_dir / "config.yaml"
        if secrets_path is None:
            secrets_path = self.config_dir / "secrets.yaml"

        self.config_path = Path(config_path)
        self.secrets_path = Path(secrets_path)

        # Load configuration
        self._load_config()

    def _load_config(self):
        """Load and validate configuration from YAML files."""
        # Load main config
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please copy config/config.yaml.example to config/config.yaml"
            )

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}

        # Load secrets
        if not self.secrets_path.exists():
            raise FileNotFoundError(
                f"Secrets file not found: {self.secrets_path}\n"
                f"Please copy config/secrets.yaml.example to config/secrets.yaml"
            )

        with open(self.secrets_path, 'r', encoding='utf-8') as f:
            secrets_data = yaml.safe_load(f) or {}

        # Parse and validate configuration
        self._parse_telegram_config(config_data, secrets_data)
        self._parse_llm_config(config_data, secrets_data)
        self._parse_bot_config(config_data)
        self._parse_paths_config(config_data)
        self._parse_daemon_config(config_data)

        # Ensure directories exist
        self.paths.database.parent.mkdir(exist_ok=True, parents=True)
        self.paths.logs.parent.mkdir(exist_ok=True, parents=True)

    def _parse_telegram_config(self, config: Dict[str, Any], secrets: Dict[str, Any]):
        """Parse Telegram configuration."""
        tg_config = config.get('telegram', {})
        tg_secrets = secrets.get('telegram', {})

        if 'api_id' not in tg_secrets:
            raise ValueError("telegram.api_id not found in secrets.yaml")
        if 'api_hash' not in tg_secrets:
            raise ValueError("telegram.api_hash not found in secrets.yaml")

        self.telegram = TelegramConfig(
            session_name=tg_config.get('session_name', 'alphasnob_session'),
            api_id=int(tg_secrets['api_id']),
            api_hash=str(tg_secrets['api_hash'])
        )

    def _parse_llm_config(self, config: Dict[str, Any], secrets: Dict[str, Any]):
        """Parse LLM configuration."""
        llm_config = config.get('llm', {})
        llm_secrets = secrets.get('llm', {})

        provider = llm_config.get('provider', 'claude').lower()
        if provider not in ['claude', 'openai']:
            raise ValueError(f"Invalid llm.provider: {provider}. Must be 'claude' or 'openai'")

        # Validate API keys
        anthropic_key = llm_secrets.get('anthropic_api_key')
        openai_key = llm_secrets.get('openai_api_key')

        if provider == 'claude' and not anthropic_key:
            raise ValueError("llm.anthropic_api_key required when provider=claude")
        if provider == 'openai' and not openai_key:
            raise ValueError("llm.openai_api_key required when provider=openai")

        # Default models
        default_model = 'claude-3-5-sonnet-20241022' if provider == 'claude' else 'gpt-4o-mini'

        self.llm = LLMConfig(
            provider=provider,
            model=llm_config.get('model', default_model),
            temperature=float(llm_config.get('temperature', 0.9)),
            max_tokens=int(llm_config.get('max_tokens', 500)),
            anthropic_api_key=anthropic_key,
            openai_api_key=openai_key
        )

        # Validate temperature
        if not 0 <= self.llm.temperature <= 2:
            raise ValueError("llm.temperature must be between 0 and 2")

    def _parse_bot_config(self, config: Dict[str, Any]):
        """Parse bot behavior configuration."""
        bot_config = config.get('bot', {})

        response_mode = bot_config.get('response_mode', 'probability').lower()
        if response_mode not in ['all', 'specific_users', 'probability', 'mentioned']:
            raise ValueError(f"Invalid bot.response_mode: {response_mode}")

        response_probability = float(bot_config.get('response_probability', 0.3))
        if not 0 <= response_probability <= 1:
            raise ValueError("bot.response_probability must be between 0 and 1")

        allowed_users = bot_config.get('allowed_users', [])
        if not isinstance(allowed_users, list):
            raise ValueError("bot.allowed_users must be a list")

        self.bot = BotConfig(
            response_mode=response_mode,
            response_probability=response_probability,
            allowed_users=[int(uid) for uid in allowed_users],
            context_length=int(bot_config.get('context_length', 50))
        )

    def _parse_paths_config(self, config: Dict[str, Any]):
        """Parse paths configuration."""
        paths_config = config.get('paths', {})

        self.paths = PathsConfig(
            corpus=self.base_dir / paths_config.get('corpus', 'olds.txt'),
            database=self.base_dir / paths_config.get('database', 'data/context.db'),
            logs=self.base_dir / paths_config.get('logs', 'logs/alphasnob.log')
        )

    def _parse_daemon_config(self, config: Dict[str, Any]):
        """Parse daemon configuration."""
        daemon_config = config.get('daemon', {})

        self.daemon = DaemonConfig(
            pid_file=self.base_dir / daemon_config.get('pid_file', 'data/alphasnob.pid'),
            log_level=daemon_config.get('log_level', 'INFO').upper(),
            auto_restart=bool(daemon_config.get('auto_restart', False))
        )

        # Validate log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.daemon.log_level not in valid_levels:
            raise ValueError(f"daemon.log_level must be one of {valid_levels}")

    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings.

        Returns:
            List of warning messages (empty if all good)
        """
        warnings = []

        # Check corpus file
        if not self.paths.corpus.exists():
            warnings.append(f"Corpus file not found: {self.paths.corpus}")

        # Check LLM configuration
        if self.llm.temperature > 1.5:
            warnings.append(f"High temperature ({self.llm.temperature}) may produce very random responses")

        # Check bot configuration
        if self.bot.response_mode == 'all':
            warnings.append("Response mode 'all' may be spammy - consider 'probability' mode")

        if self.bot.response_mode == 'specific_users' and not self.bot.allowed_users:
            warnings.append("Response mode is 'specific_users' but allowed_users is empty")

        return warnings

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (for display, without secrets).

        Returns:
            Dictionary representation of settings
        """
        return {
            'telegram': {
                'session_name': self.telegram.session_name,
                'api_id': f"{str(self.telegram.api_id)[:3]}...{str(self.telegram.api_id)[-2:]}",
            },
            'llm': {
                'provider': self.llm.provider,
                'model': self.llm.model,
                'temperature': self.llm.temperature,
                'max_tokens': self.llm.max_tokens,
            },
            'bot': {
                'response_mode': self.bot.response_mode,
                'response_probability': self.bot.response_probability,
                'allowed_users': self.bot.allowed_users,
                'context_length': self.bot.context_length,
            },
            'paths': {
                'corpus': str(self.paths.corpus),
                'database': str(self.paths.database),
                'logs': str(self.paths.logs),
            },
            'daemon': {
                'pid_file': str(self.daemon.pid_file),
                'log_level': self.daemon.log_level,
                'auto_restart': self.daemon.auto_restart,
            }
        }

    def __repr__(self):
        """String representation."""
        return (
            f"Settings(provider={self.llm.provider}, "
            f"mode={self.bot.response_mode}, "
            f"log_level={self.daemon.log_level})"
        )


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
