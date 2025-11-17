"""Application settings using Pydantic Settings V2.

Configuration is loaded from:
1. Environment variables
2. YAML files (config.yaml, secrets.yaml)
3. Default values
"""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramSettings(BaseSettings):  # type: ignore[misc]
    """Telegram configuration."""

    model_config = SettingsConfigDict(env_prefix="TELEGRAM_", extra="ignore")

    session_name: str = "alphasnob_session"
    api_id: int
    api_hash: str


class LLMSettings(BaseSettings):  # type: ignore[misc]
    """LLM configuration."""

    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")

    provider: Literal["claude", "openai"] = "claude"
    model: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.9
    max_tokens: int = 500
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None


class BotSettings(BaseSettings):  # type: ignore[misc]
    """Bot behavior configuration."""

    model_config = SettingsConfigDict(env_prefix="BOT_", extra="ignore")

    response_mode: Literal["all", "specific_users", "probability", "mentioned"] = "probability"
    response_probability: float = 0.3
    context_length: int = 50


class PathsSettings(BaseSettings):  # type: ignore[misc]
    """File paths configuration."""

    model_config = SettingsConfigDict(env_prefix="PATHS_", extra="ignore")

    database: str = "data/context.db"
    logs: str = "logs/alphasnob.log"
    corpus: str = "olds.txt"


class Settings(BaseSettings):  # type: ignore[misc]
    """Main application settings.

    Loads configuration from environment variables and config files.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from YAML
    )

    # Sub-settings
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    bot: BotSettings = Field(default_factory=BotSettings)
    paths: PathsSettings = Field(default_factory=PathsSettings)

    # Top-level settings
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


def load_yaml_config() -> dict[str, Any]:
    """Load configuration from YAML files.

    Loads and merges config.yaml and secrets.yaml.

    Returns:
        Merged configuration dictionary
    """
    config_dir = Path("config")
    config_data: dict[str, Any] = {}

    # Load config.yaml
    config_file = config_dir / "config.yaml"
    if config_file.exists():
        with config_file.open() as f:
            file_config = yaml.safe_load(f) or {}
            config_data.update(file_config)

    # Load secrets.yaml (overrides config.yaml)
    secrets_file = config_dir / "secrets.yaml"
    if secrets_file.exists():
        with secrets_file.open() as f:
            secrets_config = yaml.safe_load(f) or {}
            # Merge nested dictionaries
            for key, value in secrets_config.items():
                if (
                    key in config_data
                    and isinstance(config_data[key], dict)
                    and isinstance(value, dict)
                ):
                    config_data[key].update(value)
                else:
                    config_data[key] = value

    return config_data


def get_settings(*args: Any, **kwargs: Any) -> Settings:  # noqa: ARG001
    """Get application settings singleton.

    Args:
        *args: Ignored (for dependency-injector compatibility)
        **kwargs: Ignored (for dependency-injector compatibility)

    Returns:
        Settings instance with loaded configuration
    """
    # Load YAML config
    yaml_config = load_yaml_config()

    # Create Settings with YAML data
    return Settings(**yaml_config)
