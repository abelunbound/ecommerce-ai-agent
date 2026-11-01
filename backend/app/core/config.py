"""Process settings loaded from the repo-root .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import SecretStr

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"

# Real environment variables win; the .env only fills in what isn't already set.
load_dotenv(ENV_FILE)

_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
_LOG_FORMATS = {"text", "json"}
_SECRET_NAMES = {
    "database_url",
    "openai_api_key",
    "pinecone_api_key",
    "langfuse_public_key",
    "langfuse_secret_key",
}


class SettingsError(RuntimeError):
    """A required setting is missing or blank."""


def _env(name: str, default: str = "") -> str:
    """Return the variable, treating a blank value as unset."""
    return os.getenv(name) or default


APP_ENV = _env("APP_ENV", "local")  # local | dev | staging | production

DATABASE_URL = _env("DATABASE_URL")

OPENAI_API_KEY = _env("OPENAI_API_KEY")
OPENAI_CHAT_MODEL = _env("OPENAI_CHAT_MODEL")
OPENAI_EMBEDDING_MODEL = _env("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

PINECONE_API_KEY = _env("PINECONE_API_KEY")
PINECONE_INDEX_NAME = _env("PINECONE_INDEX_NAME", "lumen-oak-dev")
PINECONE_NAMESPACE = _env("PINECONE_NAMESPACE", "policies")

BACKEND_URL = _env("BACKEND_URL", "http://localhost:8000")  # used by the Dash frontend

LANGFUSE_PUBLIC_KEY = _env("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = _env("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = _env("LANGFUSE_HOST", "https://cloud.langfuse.com")

_REQUIRED = {
    "DATABASE_URL": DATABASE_URL,
    "OPENAI_API_KEY": OPENAI_API_KEY,
}


def check_required() -> None:
    """Raise SettingsError naming every required setting that is missing or blank."""
    missing = [name for name in _REQUIRED if not _env(name)]
    if missing:
        raise SettingsError(f"Missing required settings: {', '.join(missing)}")


class Settings:
    """Runtime settings. Secrets stay in SecretStr so logs can dump the rest."""

    def __init__(self) -> None:
        """Read the current environment and reject invalid log settings."""
        self.app_env = _env("APP_ENV", "local")
        level_default = "DEBUG" if self.app_env == "local" else "INFO"
        format_default = "text" if self.app_env == "local" else "json"
        self.log_level = _choice("LOG_LEVEL", _LOG_LEVELS, level_default)
        self.log_format = _choice("LOG_FORMAT", _LOG_FORMATS, format_default)
        self.log_sql = _bool("LOG_SQL") if self.app_env == "local" else False
        self.database_url = SecretStr(_env("DATABASE_URL"))
        self.openai_api_key = SecretStr(_env("OPENAI_API_KEY"))
        self.openai_chat_model = _env("OPENAI_CHAT_MODEL")
        self.openai_embedding_model = _env("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.pinecone_api_key = SecretStr(_env("PINECONE_API_KEY"))
        self.pinecone_index_name = _env("PINECONE_INDEX_NAME", "lumen-oak-dev")
        self.pinecone_namespace = _env("PINECONE_NAMESPACE", "policies")
        self.backend_url = _env("BACKEND_URL", "http://localhost:8000")
        self.langfuse_public_key = SecretStr(_env("LANGFUSE_PUBLIC_KEY"))
        self.langfuse_secret_key = SecretStr(_env("LANGFUSE_SECRET_KEY"))
        self.langfuse_host = _env("LANGFUSE_HOST", "https://cloud.langfuse.com")

    def safe_dump(self) -> dict[str, str]:
        """Return settings with every secret masked."""
        dumped: dict[str, str] = {}
        for name, value in self.__dict__.items():
            if name in _SECRET_NAMES:
                dumped[name] = str(value)
            else:
                dumped[name] = str(value)
        return dumped


def load_settings() -> Settings:
    """Load settings, failing when a log setting is invalid."""
    return Settings()


def _choice(name: str, allowed: set[str], default: str) -> str:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    value = raw.strip().upper() if name == "LOG_LEVEL" else raw.strip().lower()
    if value not in allowed:
        raise SettingsError(f"Invalid {name}: {raw}")
    return value


def _bool(name: str) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return False
    value = raw.strip().lower()
    if value in {"1", "true", "yes"}:
        return True
    if value not in {"0", "false", "no"}:
        raise SettingsError(f"Invalid {name}: {raw}")
    return False
