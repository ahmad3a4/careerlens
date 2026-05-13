import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (folder that contains `app/`), regardless of CWD
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=True)


def _strip(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


# OpenRouter (https://openrouter.ai) — OpenAI-compatible API
OPENROUTER_API_KEY = _strip("OPENROUTER_API_KEY")
OPENROUTER_MODEL = _strip("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_BASE_URL = _strip("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip(
    "/"
)
OPENROUTER_HTTP_REFERER = _strip("OPENROUTER_HTTP_REFERER")
OPENROUTER_APP_TITLE = _strip("OPENROUTER_APP_TITLE", "CareerLens")

RAPID_API_KEY = _strip("RAPID_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is missing from .env (get a key at https://openrouter.ai/keys)")

if not RAPID_API_KEY:
    raise ValueError("RAPID_API_KEY is missing from .env")

DATABASE_URL = _strip("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from .env")
