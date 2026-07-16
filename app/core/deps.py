from __future__ import annotations

import secrets
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CSRF_COOKIE_NAME, ACCESS_COOKIE_NAME, compare_csrf_tokens, decode_access_token
from app.crud.users import get_user_by_id
from app.models.user import User

DBSession = Annotated[Session, Depends(get_db)]


def get_token_from_request(request: Request) -> str | None:
    authorization = request.headers.get("Authorization")
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return request.cookies.get(ACCESS_COOKIE_NAME)


def get_optional_current_user(request: Request, db: DBSession) -> User | None:
    token = get_token_from_request(request)
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", "0"))
    except Exception:
        return None
    return get_user_by_id(db, user_id)


def get_current_user(request: Request, db: DBSession) -> User:
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub", "0"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")
    return user


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


def csrf_token_from_request(request: Request) -> str | None:
    return request.headers.get("X-CSRF-Token") or request.cookies.get(CSRF_COOKIE_NAME)


def validate_csrf(request: Request, form_token: str | None = None) -> None:
    expected = request.cookies.get(CSRF_COOKIE_NAME)
    received = form_token or request.headers.get("X-CSRF-Token")
    if not compare_csrf_tokens(expected, received):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")


def get_csrf_token(request: Request) -> str:
    token = request.cookies.get(CSRF_COOKIE_NAME)
    return token if token else secrets.token_urlsafe(32)
