import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .connection import connect
from .models import SessionRecord, StoredChunk, UserRecord
from indexer.models import Document, DocumentChunk
from crawler.models import WebPage


class UserRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._initialize()

    def _initialize(self) -> None:
        with connect(self.database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT,
                    last_seen_at TEXT
                );
                """
            )
            connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower ON users (LOWER(email))")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)")

    def normalize_email(self, email: str) -> str:
        return email.strip().lower()

    def create_user(self, email: str, password_hash: str) -> UserRecord:
        normalized = self.normalize_email(email)
        now = datetime.now(timezone.utc).isoformat()
        record = UserRecord(
            user_id=uuid.uuid4().hex,
            email=normalized,
            password_hash=password_hash,
            created_at=now,
            updated_at=now,
            is_active=True,
        )
        with connect(self.database_path) as connection:
            connection.execute(
                "INSERT INTO users (user_id, email, password_hash, created_at, updated_at, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                (record.user_id, record.email, record.password_hash, record.created_at, record.updated_at, int(record.is_active)),
            )
        return record

    def get_user_by_email(self, email: str) -> UserRecord | None:
        normalized = self.normalize_email(email)
        with connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT user_id, email, password_hash, created_at, updated_at, is_active FROM users WHERE LOWER(email) = ?",
                (normalized,),
            ).fetchone()
        if not row:
            return None
        return UserRecord(**{**dict(row), "is_active": bool(row["is_active"])})

    def get_user_by_id(self, user_id: str) -> UserRecord | None:
        with connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT user_id, email, password_hash, created_at, updated_at, is_active FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        return UserRecord(**{**dict(row), "is_active": bool(row["is_active"])})

    def create_session(self, user_id: str, token_hash: str, ttl_seconds: int) -> SessionRecord:
        session_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        expiry = (datetime.now(timezone.utc).timestamp() + ttl_seconds)
        expires_at = datetime.fromtimestamp(expiry, tz=timezone.utc).isoformat()
        record = SessionRecord(
            session_id=session_id,
            user_id=user_id,
            token_hash=token_hash,
            created_at=now,
            expires_at=expires_at,
            revoked_at=None,
            last_seen_at=now,
        )
        with connect(self.database_path) as connection:
            connection.execute(
                "INSERT INTO sessions (session_id, user_id, token_hash, created_at, expires_at, revoked_at, last_seen_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (record.session_id, record.user_id, record.token_hash, record.created_at, record.expires_at, record.revoked_at, record.last_seen_at),
            )
        return record

    def get_session_by_token_hash(self, token_hash: str) -> SessionRecord | None:
        with connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT session_id, user_id, token_hash, created_at, expires_at, revoked_at, last_seen_at FROM sessions WHERE token_hash = ?",
                (token_hash,),
            ).fetchone()
        if not row:
            return None
        return SessionRecord(**dict(row))

    def revoke_session(self, session_id: str) -> None:
        with connect(self.database_path) as connection:
            connection.execute(
                "UPDATE sessions SET revoked_at = ?, last_seen_at = ? WHERE session_id = ?",
                (datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat(), session_id),
            )

    def revoke_all_sessions_for_user(self, user_id: str) -> None:
        with connect(self.database_path) as connection:
            connection.execute(
                "UPDATE sessions SET revoked_at = ?, last_seen_at = ? WHERE user_id = ? AND revoked_at IS NULL",
                (datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat(), user_id),
            )


class DocumentRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._initialize()

    def _initialize(self) -> None:
        with connect(self.database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    source_path TEXT NOT NULL UNIQUE,
                    file_size INTEGER NOT NULL,
                    content_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    user_id TEXT,
                    source_type TEXT NOT NULL DEFAULT 'private'
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
                    filename TEXT NOT NULL,
                    content TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    user_id TEXT
                );
                """
            )
            existing_documents = {row["name"] for row in connection.execute("PRAGMA table_info(documents)").fetchall()}
            for name, definition in {
                "url": "TEXT",
                "canonical_url": "TEXT",
                "domain": "TEXT",
                "fetched_at": "TEXT",
                "published_at": "TEXT",
                "etag": "TEXT",
                "last_modified": "TEXT",
            }.items():
                if name not in existing_documents:
                    connection.execute(f"ALTER TABLE documents ADD COLUMN {name} {definition}")
            existing_chunks = {row["name"] for row in connection.execute("PRAGMA table_info(chunks)").fetchall()}
            if "user_id" not in existing_chunks:
                connection.execute("ALTER TABLE chunks ADD COLUMN user_id TEXT")
            connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_owner_source ON documents (user_id, source_path)")
            connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_document ON chunks (document_id, chunk_id)")

    def document_fingerprint(self, source_path: str) -> tuple[int, str] | None:
        with connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT file_size, content_hash FROM documents WHERE source_path = ?", (source_path,)
            ).fetchone()
        return (row["file_size"], row["content_hash"]) if row else None

    def upsert_document(self, document: Document | None = None, content_hash: str | None = None, chunks: list[DocumentChunk] | None = None, *, document_type: str = "private", user_id: str | None = None, filename: str | None = None, source_path: str | None = None, content: str | None = None, document_id: str | None = None) -> None:
        if document is not None:
            metadata = document.metadata
            document_id = metadata.document_id
            filename = metadata.filename
            source_path = metadata.source_path
            file_type = metadata.file_type
            file_size = metadata.file_size
            created_at = metadata.created_at.isoformat()
            updated_at = metadata.updated_at.isoformat()
            content_text = document.content
            target_hash = content_hash or hashlib.sha256(content_text.encode("utf-8")).hexdigest()
            chunk_list = chunks or []
            ownership = user_id or getattr(document.metadata, "user_id", None)
        else:
            if not document_id or not filename or not source_path:
                raise ValueError("document_id, filename, and source_path are required")
            file_type = "text/plain"
            file_size = len(content or "")
            created_at = datetime.now(timezone.utc).isoformat()
            updated_at = created_at
            target_hash = content_hash or hashlib.sha256((content or "").encode("utf-8")).hexdigest()
            chunk_list = chunks or []
            ownership = user_id

        with connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.execute(
                """INSERT INTO documents
                (document_id, filename, file_type, source_path, file_size, content_hash, created_at, updated_at, user_id, source_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET filename=excluded.filename,
                file_type=excluded.file_type, source_path=excluded.source_path, file_size=excluded.file_size,
                content_hash=excluded.content_hash, created_at=excluded.created_at, updated_at=excluded.updated_at,
                user_id=excluded.user_id, source_type=excluded.source_type""",
                (
                    document_id, filename, file_type, source_path, file_size, target_hash, created_at, updated_at,
                    ownership, document_type,
                ),
            )
            normalized_chunks: list[tuple[str, str, str, str, int, str | None]] = []
            for chunk in chunk_list:
                if isinstance(chunk, tuple):
                    chunk_id, document_id, filename, content, position = chunk[:5]
                    normalized_chunks.append((chunk_id, document_id, filename, content, position, ownership))
                else:
                    normalized_chunks.append((chunk.chunk_id, chunk.document_id, chunk.filename, chunk.content, chunk.position, ownership))
            connection.executemany(
                "INSERT INTO chunks (chunk_id, document_id, filename, content, position, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                normalized_chunks,
            )

    def upsert_web_page(self, page: WebPage, chunks: list[DocumentChunk]) -> None:
        document_id = f"web:{page.content_hash}"
        now = page.fetched_at.isoformat()
        with connect(self.database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.execute(
                """INSERT INTO documents
                (document_id, filename, file_type, source_path, file_size, content_hash, created_at, updated_at,
                 source_type, url, canonical_url, domain, fetched_at, published_at, etag, last_modified, user_id)
                VALUES (?, ?, 'text/html', ?, ?, ?, ?, ?, 'public_web', ?, ?, ?, ?, ?, ?, ?, NULL)
                ON CONFLICT(document_id) DO UPDATE SET filename=excluded.filename, source_path=excluded.source_path,
                file_size=excluded.file_size, content_hash=excluded.content_hash, updated_at=excluded.updated_at,
                source_type='public_web', url=excluded.url, canonical_url=excluded.canonical_url, domain=excluded.domain,
                fetched_at=excluded.fetched_at, published_at=excluded.published_at, etag=excluded.etag, last_modified=excluded.last_modified, user_id=excluded.user_id""",
                (document_id, page.title, page.url, len(page.content), page.content_hash, now, now, page.url,
                 page.canonical_url, page.domain, now, page.published_at.isoformat() if page.published_at else None,
                 page.etag, page.last_modified),
            )
            connection.executemany(
                "INSERT INTO chunks (chunk_id, document_id, filename, content, position, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                [(chunk.chunk_id, document_id, page.title, chunk.content, chunk.position, None) for chunk in chunks],
            )

    def web_fingerprint(self, url: str) -> tuple[str, str | None, str | None] | None:
        with connect(self.database_path) as connection:
            row = connection.execute("SELECT content_hash, etag, last_modified FROM documents WHERE url = ?", (url,)).fetchone()
        return (row["content_hash"], row["etag"], row["last_modified"]) if row else None

    def remove_missing_documents(self, active_source_paths: set[str], user_id: str | None = None) -> int:
        with connect(self.database_path) as connection:
            if user_id is None:
                rows = connection.execute(
                    "SELECT document_id, source_path, user_id FROM documents WHERE user_id IS NULL AND source_type = 'private'"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT document_id, source_path, user_id FROM documents WHERE user_id = ? AND source_type = 'private'",
                    (user_id,),
                ).fetchall()
            stale_ids = [row["document_id"] for row in rows if row["source_path"] not in active_source_paths]
            for document_id in stale_ids:
                connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
                connection.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
        return len(stale_ids)

    def all_chunks(self, user_id: str | None = None, source_type: str | None = None) -> list[StoredChunk]:
        filters: list[str] = []
        parameters: list[str | None] = []
        if source_type == "private":
            filters.append("documents.source_type = 'private'")
            if user_id is not None:
                filters.append("documents.user_id = ?")
                parameters.append(user_id)
        elif source_type == "public_web":
            filters.append("documents.source_type = 'public_web'")
        elif user_id is not None:
            filters.append("(documents.source_type = 'public_web' OR (documents.source_type = 'private' AND documents.user_id = ?))")
            parameters.append(user_id)
        if not filters:
            filter_clause = ""
        else:
            filter_clause = " WHERE " + " AND ".join(filters)
        with connect(self.database_path) as connection:
            rows = connection.execute(
                f"""SELECT chunks.document_id, chunks.chunk_id, chunks.filename,
                documents.source_path, chunks.content, chunks.position, documents.source_type,
                documents.url, documents.canonical_url, documents.domain, documents.fetched_at,
                documents.published_at, documents.user_id
                FROM chunks JOIN documents ON documents.document_id = chunks.document_id
                {filter_clause}
                ORDER BY chunks.chunk_id""",
                tuple(parameters),
            ).fetchall()
        return [StoredChunk(**{**dict(row), "user_id": row["user_id"]}) for row in rows]
