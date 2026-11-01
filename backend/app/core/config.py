"""Process settings loaded from the repo-root .env file."""

from pathlib import Path

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"


class SettingsError(RuntimeError):
    """A required setting is missing or blank."""


class Settings(BaseSettings):
    """Typed settings. Required fields have no default, so a blank value fails startup."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_env: str = "local"
    database_url: str
    openai_api_key: str
    openai_chat_model: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    pinecone_api_key: str = ""
    pinecone_index_name: str = "lumen-oak-dev"
    pinecone_namespace: str = "policies"
    backend_url: str = "http://localhost:8000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"


def load_settings(**overrides: object) -> Settings:
    """Read settings and raise SettingsError naming any missing required values."""
    try:
        return Settings(**overrides)
    except ValidationError as exc:
        missing = [
            str(err["loc"][0]).upper()
            for err in exc.errors()
            if err["type"] == "missing"
        ]
        if not missing:
            raise
        names = ", ".join(missing)
        raise SettingsError(f"Missing required settings: {names}") from exc
