from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .. import db
from ..auth import require_auth

router = APIRouter(prefix="/api", tags=["stats"], dependencies=[Depends(require_auth)])


class StatsOut(BaseModel):
    agent: int
    human: int
    inbound: int
    events: int


@router.get("/stats", response_model=StatsOut, summary="Overview counters")
async def get_stats():
    return db.stats()


@router.get("/events", summary="Recent webhook events",
            description="Raw audit log of webhook events received from WAHA, newest first.")
async def get_events(limit: int = 100):
    return db.recent_events(min(int(limit) or 100, 500))
