from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthUser:
    user_id: str
    email: str
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class SessionInfo:
    session_id: str
    user_id: str
    token_hash: str
    created_at: str
    expires_at: str
    revoked_at: str | None = None
    last_seen_at: str | None = None
