from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .. import db, waha
from ..auth import require_auth
from ..phone import is_valid_phone, normalize_phone, phone_to_chat_id

router = APIRouter(prefix="/api/messages", tags=["messages"], dependencies=[Depends(require_auth)])


class MessageOut(BaseModel):
    id: int
    direction: str = Field(description="'in' (from WhatsApp) or 'out' (we sent)")
    source: str = Field(description="'agent' | 'staff' | 'system'")
    body: str | None = None
    has_media: int
    created_at: int


class InboxItem(BaseModel):
    phone: str
    display_name: str | None = None
    mode: str
    last_in_at: int | None = None
    last_msg_preview: str | None = None
    unread: int


class ReplyIn(BaseModel):
    text: str = Field(..., example="Halo, ini dari staff Student Success.")


@router.get("/inbox", response_model=list[InboxItem], summary="Handoff inbox",
            description="One row per **human-mode** number, with unread count "
                        "(inbound after the last outbound). Powers the Handoff Console.")
async def inbox():
    return db.get_inbox()


@router.get("/{phone}", response_model=list[MessageOut], summary="Conversation log")
async def get_messages(phone: str, limit: int = 50):
    """Chronological messages for a number (oldest first)."""
    p = normalize_phone(phone)
    return db.get_messages(p, min(int(limit) or 50, 500))


@router.post("/{phone}/reply", summary="Staff reply (handoff)",
             description="Sends a text to the number via WAHA and logs it as `out/staff`. "
                         "Used during human take-over.")
async def reply(phone: str, body: ReplyIn):
    p = normalize_phone(phone)
    if not is_valid_phone(p):
        return JSONResponse(status_code=400, content={"error": "invalid phone"})
    if not body.text or not body.text.strip():
        return JSONResponse(status_code=400, content={"error": "text required"})
    chat_id = phone_to_chat_id(p)
    try:
        r = await waha.send_text(chat_id, body.text)
        waha_id = None
        if isinstance(r, dict) and isinstance(r.get("id"), dict):
            waha_id = r["id"].get("_serialized")
        db.insert_message(waha_msg_id=waha_id, phone=p, chat_id=chat_id,
                          direction="out", source="staff", body=body.text, has_media=0)
        return {"ok": True, "waha_id": waha_id}
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": "send failed", "detail": str(e)})
