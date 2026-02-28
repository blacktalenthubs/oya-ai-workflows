"""Centralized configuration. Reads from .env file and supports runtime overrides."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# --- Defaults from .env ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/oya.db")

# --- .env file path for writing ---
ENV_FILE_PATH = _env_path


def save_env_file(values: dict[str, str]):
    """Write/update key-value pairs to the .env file."""
    existing = {}
    if ENV_FILE_PATH.exists():
        for line in ENV_FILE_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                existing[key.strip()] = val.strip()

    existing.update(values)

    lines = []
    for key, val in existing.items():
        lines.append(f"{key}={val}")

    ENV_FILE_PATH.write_text("\n".join(lines) + "\n")

    # Update module-level vars so they take effect immediately
    for key, val in values.items():
        os.environ[key] = val
        if key in globals():
            globals()[key] = val


def get_key(name: str) -> str:
    """Get an API key, checking os.environ first (picks up runtime saves)."""
    return os.environ.get(name, globals().get(name, ""))
