"""Dashboard auth: signed-cookie session + server-side session map."""
import secrets
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from itsdangerous import URLSafeTimedSerializer

from .config import config

_serializer = URLSafeTimedSerializer(config.SESSION_SECRET, salt="sc-session")
_sessions: dict[str, dict] = {}
_SESSION_TTL = 12 * 3600
SESSION_MAX_AGE = _SESSION_TTL
COOKIE_NAME = "sc_session"


def check_credentials(user: str, pw: str) -> bool:
    ok_user = secrets.compare_digest(str(user), config.DASHBOARD_USER)
    ok_pass = secrets.compare_digest(str(pw), config.DASHBOARD_PASSWORD)
    return ok_user and ok_pass


def create_session(user: str) -> str:
    token = secrets.token_hex(32)
    _sessions[token] = {"user": user, "ts": time.time()}
    return token


def sign(token: str) -> str:
    return _serializer.dumps(token)


def unsign(signed: str | None) -> str | None:
    if not signed:
        return None
    try:
        return _serializer.loads(signed, max_age=_SESSION_TTL)
    except Exception:
        return None


def destroy(token: str | None) -> None:
    if token:
        _sessions.pop(token, None)


def is_valid_session(token: str | None) -> bool:
    if not token:
        return False
    s = _sessions.get(token)
    if not s:
        return False
    if time.time() - s["ts"] > _SESSION_TTL:
        _sessions.pop(token, None)
        return False
    return True


def read_token(request: Request) -> str | None:
    return unsign(request.cookies.get(COOKIE_NAME))


async def require_auth(request: Request) -> str:
    """FastAPI dependency: 401 unless a valid session cookie is present."""
    from fastapi import HTTPException
    token = read_token(request)
    if not is_valid_session(token):
        raise HTTPException(status_code=401, detail="unauthorized")
    return token
