"""WAHA HTTP client. The API key stays server-side here — never reaches the browser."""
import asyncio

import httpx

from .config import config

_BASE = config.WAHA_BASE_URL
_HEADERS = {"X-Api-Key": config.WAHA_API_KEY}


async def _request(method, path, json_body=None, headers=None, raw=False):
    url = path if path.startswith("http") else f"{_BASE}{path}"
    h = {**_HEADERS, **(headers or {})}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(method, url, json=json_body, headers=h)
    if raw:
        return resp
    if resp.status_code == 204:
        return None
    if not resp.content:
        return None
    try:
        return resp.json()
    except ValueError:
        return resp.text


def _session():
    return config.WAHA_SESSION


async def list_sessions():
    return await _request("GET", "/api/sessions")


async def get_session(s=None):
    return await _request("GET", f"/api/sessions/{s or _session()}")


async def create_session(payload):
    return await _request("POST", "/api/sessions", json_body=payload)


async def start_session(s=None):
    return await _request("POST", f"/api/sessions/{s or _session()}/start", json_body={})


async def stop_session(s=None):
    return await _request("POST", f"/api/sessions/{s or _session()}/stop", json_body={})


async def restart_session(s=None):
    return await _request("POST", f"/api/sessions/{s or _session()}/restart", json_body={})


async def logout_session(s=None):
    return await _request("POST", f"/api/sessions/{s or _session()}/logout", json_body={})


async def delete_session(s=None):
    return await _request("DELETE", f"/api/sessions/{s or _session()}")


async def get_qr(s=None):
    """Raw httpx response (caller streams the PNG)."""
    return await _request("GET", f"/api/{s or _session()}/auth/qr",
                          headers={"Accept": "image/png"}, raw=True)


async def send_text(chat_id, text, s=None):
    return await _request("POST", "/api/sendText",
                          json_body={"session": s or _session(), "chatId": chat_id, "text": text})


async def send_seen(chat_id, s=None):
    return await _request("POST", "/api/sendSeen",
                          json_body={"session": s or _session(), "chatId": chat_id})


async def version():
    return await _request("GET", "/api/server/version")


async def swallow(coro):
    """Await a coroutine, ignoring errors (used for best-effort stop/delete in recreate)."""
    try:
        return await coro
    except Exception:
        return None


async def recreate(webhook_target_url, events=None):
    """stop -> delete -> create with the correct local webhook URL. Returns the URL used."""
    events = events or ["message", "message.any", "session.status"]
    await swallow(stop_session())
    await asyncio.sleep(1.5)
    await swallow(delete_session())
    await asyncio.sleep(1.5)
    await create_session({
        "name": _session(),
        "start": True,
        "config": {"webhooks": [{"url": webhook_target_url, "events": events}]},
    })
    return webhook_target_url
