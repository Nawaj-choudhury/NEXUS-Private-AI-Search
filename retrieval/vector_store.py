import json
from pathlib import Path

from database.connection import connect
from .models import SemanticResult


class VectorStore:
    """Persistent local vector store containing embeddings and safe chunk metadata."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self._initialize()

    def _initialize(self) -> None:
        with connect(self.database_path) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS embeddings (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    source_type TEXT NOT NULL DEFAULT 'private',
                    user_id TEXT,
                    url TEXT,
                    domain TEXT
                )"""
            )
            existing = {row["name"] for row in connection.execute("PRAGMA table_info(embeddings)").fetchall()}
            for name, definition in {"source_type": "TEXT NOT NULL DEFAULT 'private'", "user_id": "TEXT", "url": "TEXT", "domain": "TEXT"}.items():
                if name not in existing:
                    connection.execute(f"ALTER TABLE embeddings ADD COLUMN {name} {definition}")

    def upsert(self, results: list[tuple], *, user_id: str | None = None) -> None:
        entries: list[tuple] = []
        for item in results:
            if len(item) >= 7 and isinstance(item[6], str):
                chunk_id, document_id, filename, source_path, content, embedding, source_type = item[:7]
                url = item[7] if len(item) > 7 else None
                domain = item[8] if len(item) > 8 else None
                record_user_id = item[9] if len(item) > 9 else user_id
            else:
                chunk_id, document_id, filename, source_path, content, embedding = item[:6]
                source_type = "private"
                url = None
                domain = None
                record_user_id = user_id
            entries.append((chunk_id, document_id, filename, source_path, content, json.dumps(embedding), source_type, record_user_id, url, domain))
        with connect(self.database_path) as connection:
            connection.executemany(
                """INSERT INTO embeddings
                (chunk_id, document_id, filename, source_path, content, embedding, source_type, user_id, url, domain)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chunk_id) DO UPDATE SET document_id=excluded.document_id,
                filename=excluded.filename, source_path=excluded.source_path,
                content=excluded.content, embedding=excluded.embedding, source_type=excluded.source_type,
                user_id=excluded.user_id, url=excluded.url, domain=excluded.domain""",
                entries,
            )

    def delete_document(self, document_id: str) -> None:
        with connect(self.database_path) as connection:
            connection.execute("DELETE FROM embeddings WHERE document_id = ?", (document_id,))

    def remove_missing_documents(self, document_ids: set[str], user_id: str | None = None) -> None:
        with connect(self.database_path) as connection:
            if user_id is None:
                rows = connection.execute("SELECT DISTINCT document_id FROM embeddings WHERE user_id IS NULL AND source_type = 'private'").fetchall()
            else:
                rows = connection.execute("SELECT DISTINCT document_id FROM embeddings WHERE user_id = ? AND source_type = 'private'", (user_id,)).fetchall()
            for row in rows:
                if row["document_id"] not in document_ids:
                    if user_id is None:
                        connection.execute("DELETE FROM embeddings WHERE document_id = ? AND user_id IS NULL AND source_type = 'private'", (row["document_id"],))
                    else:
                        connection.execute("DELETE FROM embeddings WHERE document_id = ? AND user_id = ? AND source_type = 'private'", (row["document_id"], user_id))

    def search(self, query_vector: list[float], limit: int, source_type: str | None = None, user_id: str | None = None) -> list[SemanticResult]:
        with connect(self.database_path) as connection:
            filters = []
            params: list[object] = []
            if source_type is not None:
                filters.append("source_type = ?")
                params.append(source_type)
            if user_id is not None:
                if source_type == "private":
                    filters.append("user_id = ?")
                    params.append(user_id)
                elif source_type is None:
                    filters.append("(source_type = 'public_web' OR (source_type = 'private' AND user_id = ?))")
                    params.append(user_id)
            if filters:
                where_clause = " WHERE " + " AND ".join(filters)
            else:
                where_clause = ""
            rows = connection.execute(f"SELECT * FROM embeddings{where_clause}", tuple(params)).fetchall()
        scored: list[SemanticResult] = []
        for row in rows:
            vector = json.loads(row["embedding"])
            score = sum(left * right for left, right in zip(query_vector, vector))
            scored.append(SemanticResult(row["document_id"], row["chunk_id"], row["filename"], row["source_path"], row["content"], score, row["source_type"], row["url"], row["domain"]))
        scored.sort(key=lambda result: (-result.score, result.chunk_id))
        return scored[:limit]

    def count(self) -> int:
        with connect(self.database_path) as connection:
            return connection.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]

    def has_document(self, document_id: str) -> bool:
        with connect(self.database_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM embeddings WHERE document_id = ? LIMIT 1", (document_id,)
            ).fetchone()
        return row is not None