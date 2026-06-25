from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .. import db
from ..auth import require_auth
from ..phone import is_valid_phone, normalize_phone

router = APIRouter(prefix="/api/whitelist", tags=["whitelist"], dependencies=[Depends(require_auth)])


class NumberOut(BaseModel):
    phone: str
    mode: str = Field(description="'agent' or 'human'")
    display_name: str | None = None
    created_at: int
    updated_at: int
    last_in_at: int | None = None
    last_msg_preview: str | None = None


class AddIn(BaseModel):
    phone: str = Field(example="6281234567890", description="international format, digits only")
    mode: str = Field("agent", description="'agent' (whitelist) or 'human' (taken over)")
    display_name: str | None = Field(None, example="Budi (Mahasiswa)")


class ModeIn(BaseModel):
    mode: str = Field(..., description="'agent' = whitelist / return to agent · 'human' = take over")


@router.get("", response_model=list[NumberOut], summary="List whitelisted numbers")
async def list_whitelist():
    """All numbers with their current mode, most recently active first."""
    return db.list_numbers()


@router.post("", response_model=NumberOut, summary="Add / upsert a number",
             description="Adds a number (or updates its mode/name if it already exists).")
async def add(body: AddIn):
    p = normalize_phone(body.phone)
    if not is_valid_phone(p):
        return JSONResponse(status_code=400, content={"error": "invalid phone (expect 6-15 digits)"})
    if body.mode not in ("agent", "human"):
        return JSONResponse(status_code=400, content={"error": "mode must be 'agent' or 'human'"})
    return db.upsert_number(p, body.mode, body.display_name or None)


@router.patch("/{phone}", response_model=NumberOut, summary="Switch mode (whitelist ↔ take over)",
              description="`agent` = the AI agent auto-replies · `human` = agent goes silent, staff handles it.")
async def patch_mode(phone: str, body: ModeIn):
    p = normalize_phone(phone)
    if body.mode not in ("agent", "human"):
        return JSONResponse(status_code=400, content={"error": "mode must be 'agent' or 'human'"})
    if not db.get_number(p):
        return JSONResponse(status_code=404, content={"error": "number not in whitelist"})
    db.set_mode(p, body.mode)
    return db.get_number(p)


@router.delete("/{phone}", summary="Remove a number",
               description="Removes the number entirely — inbound messages from it are then ignored.")
async def delete(phone: str):
    db.delete_number(normalize_phone(phone))
    return {"ok": True}
