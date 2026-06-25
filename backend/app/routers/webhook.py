"""WAHA webhook receiver + routing gate. THE critical file."""
import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .. import db, waha
from ..agent import agent_reply
from ..config import config
from ..phone import peer_jids, resolve_phone

logger = logging.getLogger("waha-control.webhook")
router = APIRouter(tags=["webhook"])

MESSAGE_EVENTS = {"message", "message.any", "message.received", "message.created"}


@router.post("/webhooks/waha/{token}", summary="WAHA webhook receiver",
             description=(
                 "Receives a WAHA event. The `{token}` path segment must equal `WEBHOOK_SECRET`.\n\n"
                 "WAHA nests the message under `payload`; peers may be **LID** (`@lid`). "
                 "The real phone is read from `payload._data.key.remoteJidAlt` (`@s.whatsapp.net`).\n\n"
                 "**Routing gate** per inbound message:\n"
                 "- not whitelisted → ignored (logged only)\n"
                 "- `mode=human` → agent **silent**; staff reply via `/api/messages/{phone}/reply`\n"
                 "- `mode=agent` → agent replies via WAHA `sendText`\n\n"
                 "Always returns `200 {ok:true}` so WAHA doesn't retry."
             ))
async def webhook(token: str, request: Request):
    if token != config.WEBHOOK_SECRET:
        return JSONResponse(status_code=401, content={"error": "invalid token"})

    try:
        ev = await request.json() or {}
    except Exception:
        ev = {}

    event_type = ev.get("event")
    session = ev.get("session") or config.WAHA_SESSION

    # 0. audit-log every event (best-effort)
    try:
        payload = ev.get("payload") or {}
        event_id = ev.get("id") or payload.get("id")
        db.insert_event(event_id=event_id, event_type=str(event_type or "unknown"),
                        session=session, payload=json.dumps(ev)[:8000])
    except Exception as e:
        logger.error("insert_event failed: %s", e)

    # only message events are routed
    if event_type not in MESSAGE_EVENTS:
        return {"ok": True}

    data = ev.get("payload") or {}

    # (a) ignore our own outgoing echoes (message.any is bidirectional)
    if data.get("fromMe") is True:
        return {"ok": True}

    # (b) v1: ignore groups
    if any(j.endswith("@g.us") for j in peer_jids(data)):
        return {"ok": True}

    # (c) resolve the REAL peer phone (handles WhatsApp LID privacy)
    phone = resolve_phone(data)
    if not phone:
        logger.info("inbound: cannot resolve phone (LID-only?) from=%s", data.get("from"))
        return {"ok": True}

    chat_id = f"{phone}@c.us"
    waha_id = data.get("id") or ev.get("id")
    body = data.get("body") or ((data.get("_data") or {}).get("message") or {}).get("conversation") or ""
    has_media = data.get("hasMedia") is True

    # (d) idempotent inbound insert + activity bump
    inserted = db.insert_message(waha_msg_id=waha_id, phone=phone, chat_id=chat_id,
                                 direction="in", source="system", body=body,
                                 has_media=1 if has_media else 0,
                                 media_url=data.get("mediaUrl"),
                                 raw_event=json.dumps(ev)[:4000])
    db.bump_number_activity(phone, body)

    # (e) routing gate
    row = db.get_number(phone)
    if not row:
        logger.info("non-whitelisted inbound ignored phone=%s from=%s", phone, data.get("from"))
        return {"ok": True}
    if row["mode"] == "human":
        logger.info("human-mode inbound: agent silent phone=%s", phone)
        return {"ok": True}
    if not inserted:
        logger.info("duplicate inbound: skip agent phone=%s", phone)
        return {"ok": True}

    # row.mode == 'agent' -> ask the (stub) agent and reply
    try:
        push_name = (data.get("_data") or {}).get("pushName") or data.get("pushName")
        reply_text = await agent_reply({"phone": phone, "chat_id": chat_id, "body": body,
                                        "push_name": push_name, "session_id": waha_id,
                                        "history": []})
        if reply_text:
            await waha.send_text(chat_id, reply_text, session)
            db.insert_message(waha_msg_id=None, phone=phone, chat_id=chat_id,
                              direction="out", source="agent", body=reply_text, has_media=0)
            logger.info("agent replied phone=%s text=%s", phone, str(reply_text)[:60])
    except Exception as e:
        logger.error("agent reply failed: %s", e)

    return {"ok": True}
