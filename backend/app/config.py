import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent  # .../waha-gateway/backend
load_dotenv(ROOT / ".env")  # harmless if absent (docker injects env via compose env_file)


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


class Config:
    PORT = int(_get("PORT", "3002"))
    NODE_ENV = _get("NODE_ENV", "development")
    WAHA_BASE_URL = _get("WAHA_BASE_URL", "http://localhost:3001").rstrip("/")
    WAHA_API_KEY = _get("WAHA_API_KEY", "")  # set via .env / compose
    WAHA_SESSION = _get("WAHA_SESSION", "default")
    WEBHOOK_PUBLIC_URL = _get("WEBHOOK_PUBLIC_URL", "http://172.19.0.1:3002").rstrip("/")
    WEBHOOK_SECRET = _get("WEBHOOK_SECRET", "change-me")
    DASHBOARD_USER = _get("DASHBOARD_USER", "admin")
    DASHBOARD_PASSWORD = _get("DASHBOARD_PASSWORD", "admin")
    SESSION_SECRET = _get("SESSION_SECRET", "dev-secret-change-me")
    AGENT_IMPL = _get("AGENT_IMPL", "stub")
    DB_PATH = _get("DB_PATH", str(ROOT / "data" / "control.db"))
    FRONTEND_DIR = _get("FRONTEND_DIR", "/app/frontend")


config = Config()


def webhook_url() -> str:
    """Full webhook URL WAHA should POST to (token embedded in path)."""
    return f"{config.WEBHOOK_PUBLIC_URL}/webhooks/waha/{config.WEBHOOK_SECRET}"
