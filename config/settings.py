import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:

    def __init__(self):
        self.api_id = self._get_required("API_ID", int)
        self.api_hash = self._get_required("API_HASH", str)
        self.session_name = os.getenv("SESSION_NAME", "alphasnob_session")

        self.llm_provider = os.getenv("LLM_PROVIDER", "claude").lower()
        if self.llm_provider not in ["claude", "openai"]:
            raise ValueError(f"Invalid LLM_PROVIDER: {self.llm_provider}. Must be 'claude' or 'openai'")

        if self.llm_provider == "claude":
            self.anthropic_api_key = self._get_required("ANTHROPIC_API_KEY", str)
            self.openai_api_key = None
        else:
            self.openai_api_key = self._get_required("OPENAI_API_KEY", str)
            self.anthropic_api_key = None

        self.response_mode = os.getenv("RESPONSE_MODE", "probability").lower()
        if self.response_mode not in ["all", "specific_users", "probability", "mentioned"]:
            raise ValueError(f"Invalid RESPONSE_MODE: {self.response_mode}")

        self.response_probability = float(os.getenv("RESPONSE_PROBABILITY", "0.3"))
        if not 0 <= self.response_probability <= 1:
            raise ValueError("RESPONSE_PROBABILITY must be between 0 and 1")

        allowed_users_str = os.getenv("ALLOWED_USERS", "")
        self.allowed_users: List[int] = []
        if allowed_users_str.strip():
            try:
                self.allowed_users = [int(uid.strip()) for uid in allowed_users_str.split(",")]
            except ValueError:
                raise ValueError("ALLOWED_USERS must be comma-separated integers")

        self.context_length = int(os.getenv("CONTEXT_LENGTH", "50"))

        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.db_path = self.data_dir / "context.db"
        self.corpus_path = self.base_dir / "olds.txt"

        self.data_dir.mkdir(exist_ok=True)

        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.9"))
        self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "500"))
        self.llm_model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022" if self.llm_provider == "claude" else "gpt-4")

    def _get_required(self, key: str, value_type):
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Required environment variable {key} is not set")

        try:
            return value_type(value)
        except ValueError:
            raise ValueError(f"Environment variable {key} must be of type {value_type.__name__}")

    def __repr__(self):
        return (
            f"Settings(api_id={self.api_id}, "
            f"llm_provider={self.llm_provider}, "
            f"response_mode={self.response_mode}, "
            f"context_length={self.context_length})"
        )


settings = Settings()
