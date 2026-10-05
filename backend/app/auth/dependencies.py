from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, Request

from backend.app.core.config import settings
from database.repository import UserRepository

from .models import AuthUser
from .session import hash_session_token


def get_current_user(request: Request) -> AuthUser:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Authentication required."})

    repository = UserRepository(Path(settings.database_path))
    token_hash = hash_session_token(token)
    session = repository.get_session_by_token_hash(token_hash)
    if session is None or session.revoked_at is not None:
        raise HTTPException(status_code=401, detail={"code": "SESSION_INVALID", "message": "Session is invalid or revoked."})

    expires_at = datetime.fromisoformat(session.expires_at)
    if datetime.now(timezone.utc) > expires_at:
        repository.revoke_session(session.session_id)
        raise HTTPException(status_code=401, detail={"code": "SESSION_EXPIRED", "message": "Session expired."})

    user = repository.get_user_by_id(session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail={"code": "USER_INACTIVE", "message": "Account is inactive."})
    return AuthUser(user_id=user.user_id, email=user.email, is_active=user.is_active)
