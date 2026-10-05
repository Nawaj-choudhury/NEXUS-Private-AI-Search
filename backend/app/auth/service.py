from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, Request, Response

from backend.app.core.config import settings
from database.repository import UserRepository

from .models import AuthUser
from .password import generate_session_token, hash_password, verify_password
from .session import hash_session_token


class AuthService:
    def __init__(self, database_path: Path | str | None = None) -> None:
        self.repository = UserRepository(Path(database_path or settings.database_path))

    def _user_root(self, user_id: str) -> Path:
        root = Path(settings.private_vault_path)
        user_dir = root / "users" / user_id / "documents"
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def register(self, email: str, password: str, response: Response | None = None) -> AuthUser:
        normalized = email.strip().lower()
        if len(password) < 8:
            raise HTTPException(status_code=400, detail={"code": "WEAK_PASSWORD", "message": "Password must be at least 8 characters long."})
        if self.repository.get_user_by_email(normalized):
            raise HTTPException(status_code=409, detail={"code": "EMAIL_EXISTS", "message": "Account already exists."})
        user = self.repository.create_user(normalized, hash_password(password))
        self._user_root(user.user_id)
        if response is not None:
            self._issue_session(response, user.user_id)
        return AuthUser(user_id=user.user_id, email=user.email, is_active=user.is_active)

    def _issue_session(self, response: Response, user_id: str) -> str:
        token = generate_session_token()
        self.repository.create_session(user_id, hash_session_token(token), settings.session_ttl_seconds)
        response.set_cookie(
            key=settings.session_cookie_name,
            value=token,
            httponly=True,
            samesite=settings.cookie_samesite,
            secure=settings.cookie_secure,
            max_age=settings.session_ttl_seconds,
        )
        return token

    def login(self, email: str, password: str, response: Response) -> AuthUser:
        record = self.repository.get_user_by_email(email.strip().lower())
        if not record or not record.is_active or not verify_password(password, record.password_hash):
            raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."})
        self._issue_session(response, record.user_id)
        return AuthUser(user_id=record.user_id, email=record.email, is_active=record.is_active)

    def logout(self, request: Request, response: Response) -> None:
        token = request.cookies.get(settings.session_cookie_name)
        if token:
            self.repository.revoke_session(self.repository.get_session_by_token_hash(hash_session_token(token)).session_id if self.repository.get_session_by_token_hash(hash_session_token(token)) else "")
        response.delete_cookie(key=settings.session_cookie_name, httponly=True, samesite=settings.cookie_samesite, secure=settings.cookie_secure)

    def me(self, request: Request) -> AuthUser:
        from .dependencies import get_current_user

        current = get_current_user(request)
        return current

    def get_user_by_id(self, user_id: str) -> AuthUser | None:
        record = self.repository.get_user_by_id(user_id)
        if not record or not record.is_active:
            return None
        return AuthUser(user_id=record.user_id, email=record.email, is_active=record.is_active)
