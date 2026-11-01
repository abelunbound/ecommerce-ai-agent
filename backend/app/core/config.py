"""Process settings loaded from the repo-root .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"

# Real environment variables win; the .env only fills in what isn't already set.
load_dotenv(ENV_FILE)


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
    missing = [name for name, value in _REQUIRED.items() if not value]
    if missing:
        raise SettingsError(f"Missing required settings: {', '.join(missing)}")