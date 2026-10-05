import hashlib
from datetime import datetime, timedelta, timezone


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_expiration(now: datetime | None = None, ttl_seconds: int = 86400) -> datetime:
    base = now or datetime.now(timezone.utc)
    return base + timedelta(seconds=ttl_seconds)
