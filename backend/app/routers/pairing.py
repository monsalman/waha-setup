from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response

from .. import waha
from ..auth import require_auth
from ..config import webhook_url

router = APIRouter(prefix="/api/pairing", tags=["pairing"], dependencies=[Depends(require_auth)])


@router.get("/status", summary="Session status + WAHA version",
            description="Proxies `GET /api/sessions/{session}` and the WAHA server version. "
                        "Status `WORKING` = connected.")
async def status():
    try:
        session = await waha.get_session()
        err = None
    except Exception as e:
        session = None
        err = str(e)
    version = await waha.swallow(waha.version())
    out = {"session": session, "version": version}
    if err:
        out["error"] = err
    return out


@router.get("/qr", summary="QR code (PNG)",
            description="Streams the WhatsApp pairing QR as `image/png`. "
                        "Use as `<img src=\"/api/pairing/qr\">`. Only valid while status is SCAN_QR_CODE.")
async def qr():
    resp = await waha.get_qr()
    if resp.status_code != 200:
        text = (resp.text or "")[:200]
        return JSONResponse(status_code=resp.status_code,
                            content={"error": "qr not available", "status": resp.status_code, "detail": text})
    return Response(content=resp.content, media_type="image/png")


@router.post("/start", summary="Start session", description="Proxies `POST /api/sessions/{session}/start`.")
async def start():
    await waha.start_session()
    return {"ok": True}


@router.post("/stop", summary="Stop session", description="Disconnects WhatsApp (keeps saved login).")
async def stop():
    await waha.stop_session()
    return {"ok": True}


@router.post("/restart", summary="Restart session", description="Reconnect using the saved login.")
async def restart():
    await waha.restart_session()
    return {"ok": True}


@router.post("/logout", summary="Logout WhatsApp", description="Logs out — a QR scan is needed to reconnect.")
async def logout():
    await waha.logout_session()
    return {"ok": True}


@router.post("/recreate", summary="Recreate session (fresh QR + webhook)",
             description="stop → delete → create a new session with the correct **local webhook** and a fresh QR. "
                         "⚠️ This wipes the saved WhatsApp login (a new scan is required).")
async def recreate():
    url = webhook_url()
    try:
        await waha.recreate(url)
        return {"ok": True, "webhook": url}
    except Exception as e:
        return JSONResponse(status_code=502,
                            content={"error": "recreate failed", "detail": str(e), "webhook": url})
