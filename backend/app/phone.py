"""Phone / chatId helpers, including WhatsApp LID -> real phone resolution."""
import re


def is_group(chat_id) -> bool:
    return isinstance(chat_id, str) and chat_id.endswith("@g.us")


def chat_id_to_phone(chat_id):
    if not chat_id:
        return None
    p = re.sub(r"@\d+$", "", str(chat_id))
    p = re.sub(r"@(c|g)\.us$", "", p)
    p = re.sub(r"[^0-9]", "", p)
    return p or None


def phone_to_chat_id(phone) -> str:
    return f"{normalize_phone(phone)}@c.us"


def normalize_phone(phone) -> str:
    return re.sub(r"[^0-9]", "", str(phone or ""))


def is_valid_phone(phone) -> bool:
    return bool(re.match(r"^[0-9]{6,15}$", normalize_phone(phone)))


def resolve_phone(payload):
    """Resolve the real phone from a WAHA message payload.

    Modern WhatsApp may address peers by LID (privacy), e.g. "123@lid" instead of
    the phone. The real phone (if available) lives in payload._data.key.remoteJidAlt
    as "<phone>@s.whatsapp.net". We prefer phone forms over LIDs.
    Returns digits-only phone, or None if only an unresolvable LID exists.
    """
    data = payload or {}
    key = (data.get("_data") or {}).get("key") or {}
    candidates = [c for c in [key.get("remoteJidAlt"), key.get("remoteJid"),
                              data.get("from"), data.get("to")] if c]
    phone_form = next((c for c in candidates
                       if re.search(r"@(c\.us|s\.whatsapp\.net)$", str(c))), None)
    return chat_id_to_phone(phone_form) if phone_form else None


def peer_jids(payload):
    """All jid-like fields from a payload (for group detection, etc.)."""
    data = payload or {}
    key = (data.get("_data") or {}).get("key") or {}
    return [str(x) for x in [data.get("from"), data.get("to"),
                             key.get("remoteJid"), key.get("remoteJidAlt")] if x]
