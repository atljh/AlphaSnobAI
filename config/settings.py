import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class TelegramConfig:
    session_name: str
    api_id: int
    api_hash: str


@dataclass
class LLMConfig:
    provider: str
    model: str
    temperature: float
    max_tokens: int
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None


@dataclass
class BotConfig:
    response_mode: str
    response_probability: float
    allowed_users: List[int] = field(default_factory=list)
    context_length: int = 50


@dataclass
class PathsConfig:
    corpus: Path
    database: Path
    logs: Path


@dataclass
class DaemonConfig:
    pid_file: Path
    log_level: str
    auto_restart: bool = False


@dataclass
class PersonaSettings:
    intensity: float = 0.8
    use_corpus: bool = True
    friendliness: float = 0.7
    emoji_probability: float = 0.3
    corpus_path: Optional[Path] = None
    match_style_strength: float = 0.9


@dataclass
class PersonaConfig:
    default_mode: str
    user_overrides: Dict[int, str] = field(default_factory=dict)
    chat_overrides: Dict[int, str] = field(default_factory=dict)
    adaptive_switching: bool = True
    alphasnob: PersonaSettings = field(default_factory=PersonaSettings)
    normal: PersonaSettings = field(default_factory=PersonaSettings)
    owner: PersonaSettings = field(default_factory=PersonaSettings)


@dataclass
class ReadDelayConfig:
    min_ms: int
    max_ms: int
    per_word_ms: int


@dataclass
class TypingActionConfig:
    enabled: bool
    base_delay_ms: int
    per_character_ms: int
    randomness: float
    min_ms: int
    max_ms: int


@dataclass
class ThinkingDelayConfig:
    min_ms: int
    max_ms: int


@dataclass
class TypingConfig:
    enabled: bool
    read_delay: ReadDelayConfig
    typing_action: TypingActionConfig
    thinking_delay: ThinkingDelayConfig


@dataclass
class TimeBasedConfig:
    enabled: bool
    quiet_hours_start: int
    quiet_hours_end: int
    quiet_hours_multiplier: float


@dataclass
class TopicBasedConfig:
    enabled: bool
    boring_topics: List[str]
    boring_topic_multiplier: float
    interesting_topics: List[str]
    interesting_topic_multiplier: float


@dataclass
class ContextAwareConfig:
    enabled: bool
    recent_response_cooldown_seconds: int
    max_consecutive_responses: int
    consecutive_response_multiplier: float


@dataclass
class DecisionConfig:
    relationship_multipliers: Dict[str, float]
    time_based: TimeBasedConfig
    topic_based: TopicBasedConfig
    context_aware: ContextAwareConfig


@dataclass
class AutoUpgradeConfig:
    enabled: bool
    stranger_to_acquaintance: int
    acquaintance_to_friend: int
    friend_to_close_friend: int


@dataclass
class TrustAdjustmentConfig:
    positive_markers: List[str]
    negative_markers: List[str]
    adjustment_amount: float


@dataclass
class ProfilingConfig:
    enabled: bool
    auto_upgrade: AutoUpgradeConfig
    trust_adjustment: TrustAdjustmentConfig


@dataclass
class OwnerLearningConfig:
    enabled: bool
    owner_user_ids: List[int]
    auto_collect: bool
    collection_path: Path
    manual_samples_path: Path
    analyze_on_startup: bool
    min_samples: int


@dataclass
class LanguageConfig:
    auto_detect: bool
    supported: List[str]
    default: str


class Settings:

    def __init__(self, config_path: Optional[Path] = None, secrets_path: Optional[Path] = None):
        """Initialize settings from YAML files.

        Args:
            config_path: Path to config.yaml (defaults to config/config.yaml)
            secrets_path: Path to secrets.yaml (defaults to config/secrets.yaml)
        """
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"

        if config_path is None:
            config_path = self.config_dir / "config.yaml"
        if secrets_path is None:
            secrets_path = self.config_dir / "secrets.yaml"

        self.config_path = Path(config_path)
        self.secrets_path = Path(secrets_path)

        self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please copy config/config.yaml.example to config/config.yaml"
            )

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}

        if not self.secrets_path.exists():
            raise FileNotFoundError(
                f"Secrets file not found: {self.secrets_path}\n"
                f"Please copy config/secrets.yaml.example to config/secrets.yaml"
            )

        with open(self.secrets_path, 'r', encoding='utf-8') as f:
            secrets_data = yaml.safe_load(f) or {}

        self._parse_telegram_config(config_data, secrets_data)
        self._parse_llm_config(config_data, secrets_data)
        self._parse_bot_config(config_data)
        self._parse_paths_config(config_data)
        self._parse_daemon_config(config_data)
        self._parse_persona_config(config_data)
        self._parse_typing_config(config_data)
        self._parse_decision_config(config_data)
        self._parse_profiling_config(config_data)
        self._parse_owner_learning_config(config_data)
        self._parse_language_config(config_data)

        self.paths.database.parent.mkdir(exist_ok=True, parents=True)
        self.paths.logs.parent.mkdir(exist_ok=True, parents=True)

    def _parse_telegram_config(self, config: Dict[str, Any], secrets: Dict[str, Any]):
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
        llm_config = config.get('llm', {})
        llm_secrets = secrets.get('llm', {})

        provider = llm_config.get('provider', 'claude').lower()
        if provider not in ['claude', 'openai']:
            raise ValueError(f"Invalid llm.provider: {provider}. Must be 'claude' or 'openai'")

        anthropic_key = llm_secrets.get('anthropic_api_key')
        openai_key = llm_secrets.get('openai_api_key')

        if provider == 'claude' and not anthropic_key:
            raise ValueError("llm.anthropic_api_key required when provider=claude")
        if provider == 'openai' and not openai_key:
            raise ValueError("llm.openai_api_key required when provider=openai")

        default_model = 'claude-3-5-sonnet-20241022' if provider == 'claude' else 'gpt-4o-mini'

        self.llm = LLMConfig(
            provider=provider,
            model=llm_config.get('model', default_model),
            temperature=float(llm_config.get('temperature', 0.9)),
            max_tokens=int(llm_config.get('max_tokens', 500)),
            anthropic_api_key=anthropic_key,
            openai_api_key=openai_key
        )

        if not 0 <= self.llm.temperature <= 2:
            raise ValueError("llm.temperature must be between 0 and 2")

    def _parse_bot_config(self, config: Dict[str, Any]):
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
        paths_config = config.get('paths', {})

        self.paths = PathsConfig(
            corpus=self.base_dir / paths_config.get('corpus', 'olds.txt'),
            database=self.base_dir / paths_config.get('database', 'data/context.db'),
            logs=self.base_dir / paths_config.get('logs', 'logs/alphasnob.log')
        )

    def _parse_daemon_config(self, config: Dict[str, Any]):
        daemon_config = config.get('daemon', {})

        self.daemon = DaemonConfig(
            pid_file=self.base_dir / daemon_config.get('pid_file', 'data/alphasnob.pid'),
            log_level=daemon_config.get('log_level', 'INFO').upper(),
            auto_restart=bool(daemon_config.get('auto_restart', False))
        )

        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.daemon.log_level not in valid_levels:
            raise ValueError(f"daemon.log_level must be one of {valid_levels}")

    def _parse_persona_config(self, config: Dict[str, Any]):
        persona_config = config.get('persona', {})

        default_mode = persona_config.get('default_mode', 'alphasnob')
        if default_mode not in ['alphasnob', 'normal', 'owner']:
            raise ValueError(f"Invalid persona.default_mode: {default_mode}")

        alphasnob_cfg = persona_config.get('alphasnob', {})
        normal_cfg = persona_config.get('normal', {})
        owner_cfg = persona_config.get('owner', {})

        self.persona = PersonaConfig(
            default_mode=default_mode,
            user_overrides=persona_config.get('user_overrides', {}),
            chat_overrides=persona_config.get('chat_overrides', {}),
            adaptive_switching=bool(persona_config.get('adaptive_switching', True)),
            alphasnob=PersonaSettings(
                intensity=float(alphasnob_cfg.get('intensity', 0.8)),
                use_corpus=bool(alphasnob_cfg.get('use_corpus', True))
            ),
            normal=PersonaSettings(
                friendliness=float(normal_cfg.get('friendliness', 0.7)),
                emoji_probability=float(normal_cfg.get('emoji_probability', 0.3))
            ),
            owner=PersonaSettings(
                corpus_path=self.base_dir / owner_cfg.get('corpus_path', 'data/owner_samples/messages.txt'),
                match_style_strength=float(owner_cfg.get('match_style_strength', 0.9))
            )
        )

    def _parse_typing_config(self, config: Dict[str, Any]):
        typing_config = config.get('typing', {})

        read_delay_cfg = typing_config.get('read_delay', {})
        typing_action_cfg = typing_config.get('typing_action', {})
        thinking_delay_cfg = typing_config.get('thinking_delay', {})

        self.typing = TypingConfig(
            enabled=bool(typing_config.get('enabled', True)),
            read_delay=ReadDelayConfig(
                min_ms=int(read_delay_cfg.get('min_ms', 500)),
                max_ms=int(read_delay_cfg.get('max_ms', 3000)),
                per_word_ms=int(read_delay_cfg.get('per_word_ms', 150))
            ),
            typing_action=TypingActionConfig(
                enabled=bool(typing_action_cfg.get('enabled', True)),
                base_delay_ms=int(typing_action_cfg.get('base_delay_ms', 1000)),
                per_character_ms=int(typing_action_cfg.get('per_character_ms', 50)),
                randomness=float(typing_action_cfg.get('randomness', 0.3)),
                min_ms=int(typing_action_cfg.get('min_ms', 800)),
                max_ms=int(typing_action_cfg.get('max_ms', 15000))
            ),
            thinking_delay=ThinkingDelayConfig(
                min_ms=int(thinking_delay_cfg.get('min_ms', 500)),
                max_ms=int(thinking_delay_cfg.get('max_ms', 2500))
            )
        )

    def _parse_decision_config(self, config: Dict[str, Any]):
        decision_config = config.get('decision', {})

        relationship_multipliers = decision_config.get('relationship_multipliers', {
            'owner': 1.0,
            'close_friend': 0.9,
            'friend': 0.7,
            'acquaintance': 0.5,
            'stranger': 0.3
        })

        time_based_cfg = decision_config.get('time_based', {})
        topic_based_cfg = decision_config.get('topic_based', {})
        context_aware_cfg = decision_config.get('context_aware', {})

        self.decision = DecisionConfig(
            relationship_multipliers=relationship_multipliers,
            time_based=TimeBasedConfig(
                enabled=bool(time_based_cfg.get('enabled', True)),
                quiet_hours_start=int(time_based_cfg.get('quiet_hours_start', 23)),
                quiet_hours_end=int(time_based_cfg.get('quiet_hours_end', 8)),
                quiet_hours_multiplier=float(time_based_cfg.get('quiet_hours_multiplier', 0.2))
            ),
            topic_based=TopicBasedConfig(
                enabled=bool(topic_based_cfg.get('enabled', True)),
                boring_topics=topic_based_cfg.get('boring_topics', ['weather', 'погода']),
                boring_topic_multiplier=float(topic_based_cfg.get('boring_topic_multiplier', 0.4)),
                interesting_topics=topic_based_cfg.get('interesting_topics', ['music', 'музыка']),
                interesting_topic_multiplier=float(topic_based_cfg.get('interesting_topic_multiplier', 1.5))
            ),
            context_aware=ContextAwareConfig(
                enabled=bool(context_aware_cfg.get('enabled', True)),
                recent_response_cooldown_seconds=int(context_aware_cfg.get('recent_response_cooldown_seconds', 60)),
                max_consecutive_responses=int(context_aware_cfg.get('max_consecutive_responses', 3)),
                consecutive_response_multiplier=float(context_aware_cfg.get('consecutive_response_multiplier', 0.5))
            )
        )

    def _parse_profiling_config(self, config: Dict[str, Any]):
        profiling_config = config.get('profiling', {})

        auto_upgrade_cfg = profiling_config.get('auto_upgrade', {})
        trust_adjustment_cfg = profiling_config.get('trust_adjustment', {})

        self.profiling = ProfilingConfig(
            enabled=bool(profiling_config.get('enabled', True)),
            auto_upgrade=AutoUpgradeConfig(
                enabled=bool(auto_upgrade_cfg.get('enabled', True)),
                stranger_to_acquaintance=int(auto_upgrade_cfg.get('stranger_to_acquaintance', 5)),
                acquaintance_to_friend=int(auto_upgrade_cfg.get('acquaintance_to_friend', 20)),
                friend_to_close_friend=int(auto_upgrade_cfg.get('friend_to_close_friend', 100))
            ),
            trust_adjustment=TrustAdjustmentConfig(
                positive_markers=trust_adjustment_cfg.get('positive_markers', ['thanks', 'спасибо']),
                negative_markers=trust_adjustment_cfg.get('negative_markers', ['stupid', 'тупой']),
                adjustment_amount=float(trust_adjustment_cfg.get('adjustment_amount', 0.1))
            )
        )

    def _parse_owner_learning_config(self, config: Dict[str, Any]):
        owner_config = config.get('owner_learning', {})

        self.owner_learning = OwnerLearningConfig(
            enabled=bool(owner_config.get('enabled', False)),
            owner_user_ids=owner_config.get('owner_user_ids', []),
            auto_collect=bool(owner_config.get('auto_collect', False)),
            collection_path=self.base_dir / owner_config.get('collection_path', 'data/owner_samples/collected.txt'),
            manual_samples_path=self.base_dir / owner_config.get('manual_samples_path', 'data/owner_samples/messages.txt'),
            analyze_on_startup=bool(owner_config.get('analyze_on_startup', False)),
            min_samples=int(owner_config.get('min_samples', 50))
        )

    def _parse_language_config(self, config: Dict[str, Any]):
        language_config = config.get('language', {})

        self.language = LanguageConfig(
            auto_detect=bool(language_config.get('auto_detect', True)),
            supported=language_config.get('supported', ['ru', 'en']),
            default=language_config.get('default', 'ru')
        )

    def validate(self) -> List[str]:
        warnings = []

        if not self.paths.corpus.exists():
            warnings.append(f"Corpus file not found: {self.paths.corpus}")

        if self.llm.temperature > 1.5:
            warnings.append(f"High temperature ({self.llm.temperature}) may produce very random responses")

        if self.bot.response_mode == 'all':
            warnings.append("Response mode 'all' may be spammy - consider 'probability' mode")

        if self.bot.response_mode == 'specific_users' and not self.bot.allowed_users:
            warnings.append("Response mode is 'specific_users' but allowed_users is empty")

        return warnings

    def to_dict(self) -> Dict[str, Any]:
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
