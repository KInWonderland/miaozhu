"""Login and session endpoints."""

from hmac import compare_digest

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["登录"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)


class LoginResponse(BaseModel):
    username: str


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request):
    """Authenticate the configured administrator and establish a signed session."""
    valid_username = compare_digest(payload.username, settings.AUTH_USERNAME)
    valid_password = compare_digest(payload.password, settings.AUTH_PASSWORD)
    if not (valid_username and valid_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # Drop any pre-existing session data to avoid session fixation.
    request.session.clear()
    request.session["authenticated_user"] = settings.AUTH_USERNAME
    return LoginResponse(username=settings.AUTH_USERNAME)


@router.get("/me", response_model=LoginResponse)
async def get_current_user(request: Request):
    """Return the currently authenticated user. Protected by the middleware."""
    return LoginResponse(username=request.session["authenticated_user"])


@router.post("/logout")
async def logout(request: Request):
    """End the current session. Protected by the middleware."""
    request.session.clear()
    return {"message": "已退出登录"}
