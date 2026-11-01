"""Frontend settings. Reads BACKEND_URL from the repo-root .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

# Real environment variables win; the .env only fills in what isn't already set.
load_dotenv(ENV_FILE)


def _env(name: str, default: str = "") -> str:
    """Return the variable, treating a blank value as unset."""
    return os.getenv(name) or default


BACKEND_URL = _env("BACKEND_URL", "http://localhost:8000")
# API_TIMEOUT_SECONDS = float(os.getenv("API_TIMEOUT_SECONDS", "10"))
# API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")