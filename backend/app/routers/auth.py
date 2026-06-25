from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..auth import (COOKIE_NAME, SESSION_MAX_AGE, check_credentials, create_session,
                    destroy, read_token, require_auth, sign)
from ..config import config

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    username: str | None = Field(None, example="admin")
    password: str | None = Field(None, example="your-dashboard-password")


@router.post("/login", summary="Dashboard login",
             description="Validates credentials and sets a signed `sc_session` cookie "
                         "(HttpOnly). All other `/api/*` endpoints require it.")
async def login(body: LoginIn, response: Response):
    if not body.username or not body.password:
        return JSONResponse(status_code=400, content={"error": "username & password required"})
    if not check_credentials(body.username, body.password):
        return JSONResponse(status_code=401, content={"error": "invalid credentials"})
    token = create_session(body.username)
    response.set_cookie(COOKIE_NAME, sign(token),
                        httponly=True, samesite="lax", max_age=SESSION_MAX_AGE, path="/")
    return {"ok": True}


@router.post("/logout", summary="Dashboard logout", description="Clears the session cookie.")
async def logout(request: Request, response: Response):
    destroy(read_token(request))
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me", summary="Current session", description="Returns the logged-in user, or 401.")
async def me(_token: str = Depends(require_auth)):
    return {"username": config.DASHBOARD_USER}
