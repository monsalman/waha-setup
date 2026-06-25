import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import db  # noqa: F401  (apply schema on import)
from .config import config
from .routers import auth, messages, pairing, stats, webhook, whitelist

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("waha-control")

TAGS = [
    {"name": "auth", "description": "Dashboard login / logout. Sets a signed `sc_session` cookie "
                                    "used by all other `/api/*` endpoints."},
    {"name": "pairing", "description": "WhatsApp pairing via WAHA (proxied; the WAHA API key is held "
                                       "server-side and never reaches the browser)."},
    {"name": "whitelist", "description": "Whitelist numbers and toggle per-number mode: "
                                         "`agent` = AI agent auto-replies, `human` = taken over (agent silent)."},
    {"name": "messages", "description": "Conversation log + staff (student success) replies during handoff."},
    {"name": "stats", "description": "Overview counters and the raw webhook event log."},
    {"name": "webhook", "description": "WAHA webhook receiver. Public endpoint, gated by a path token "
                                       "(= `WEBHOOK_SECRET`)."},
]

app = FastAPI(
    title="Satu Cakrawala — WhatsApp Control API",
    description=(
        "Backend logic for the WAHA WhatsApp gateway: **pair WhatsApp**, "
        "**whitelist / unwhitelist numbers**, route inbound messages to an **agent** "
        "(or keep the agent **silent** during human handoff).\n\n"
        "### Auth\n"
        "All `/api/*` endpoints (except `POST /api/auth/login`) require the dashboard "
        "session cookie. In Swagger: call **POST /api/auth/login** first — the cookie is "
        "stored automatically and sent on subsequent requests.\n\n"
        "### Routing gate (per inbound message)\n"
        "- number **not whitelisted** → ignored\n"
        "- mode `agent` → agent auto-replies\n"
        "- mode `human` → agent **silent**; staff reply via `/api/messages/{phone}/reply`\n\n"
        "_WAHA API key is held server-side; this proxy never exposes it._"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=TAGS,
)

app.include_router(auth.router)
app.include_router(pairing.router)
app.include_router(whitelist.router)
app.include_router(messages.router)
app.include_router(stats.router)
app.include_router(webhook.router)


@app.get("/healthz", tags=["stats"], summary="Health check")
async def healthz():
    return {"ok": True}


@app.on_event("startup")
async def _startup():
    logger.info("waha-control (python) :%s | agent=%s | session=%s",
                config.PORT, config.AGENT_IMPL, config.WAHA_SESSION)
    logger.info("webhook target: %s/webhooks/waha/<token>", config.WEBHOOK_PUBLIC_URL)
    logger.info("API docs: /docs  ·  ReDoc: /redoc")


# Serve the dashboard at / (AFTER API + docs routes so /api/*, /docs, /openapi.json still win).
_front = Path(config.FRONTEND_DIR)
if _front.exists() and (_front / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(_front), html=True), name="frontend")
    logger.info("serving frontend from %s", _front)
else:
    logger.warning("frontend dir not found (%s) — API-only mode", _front)
