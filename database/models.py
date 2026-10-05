from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StoredChunk:
    document_id: str
    chunk_id: str
    filename: str
    source_path: str
    content: str
    position: int
    source_type: str = "private"
    url: str | None = None
    canonical_url: str | None = None
    domain: str | None = None
    fetched_at: str | None = None
    published_at: str | None = None
    user_id: str | None = None


@dataclass(frozen=True, slots=True)
class UserRecord:
    user_id: str
    email: str
    password_hash: str
    created_at: str
    updated_at: str
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class SessionRecord:
    session_id: str
    user_id: str
    token_hash: str
    created_at: str
    expires_at: str
    revoked_at: str | None = None
    last_seen_at: str | None = None