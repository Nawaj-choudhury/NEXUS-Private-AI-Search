from pathlib import Path
import re

from backend.app.core.config import settings
from database.repository import DocumentRepository
from indexer.pipeline import IndexingPipeline
from retrieval.embeddings import get_embedding_model
from retrieval.vector_store import VectorStore


def private_vault_for_user(user_id: str | None = None) -> Path:
    base = Path(settings.private_vault_path)
    if user_id:
        if re.fullmatch(r"[A-Za-z0-9_-]{1,128}", user_id) is None:
            raise ValueError("Invalid user identifier")
        users_root = base.resolve() / "users"
        vault_path = users_root / user_id / "documents"
        if not vault_path.resolve().is_relative_to(users_root):
            raise ValueError("User vault path escapes the configured vault root")
        return vault_path
    if base.name == "documents":
        return base
    documents_dir = base / "documents"
    if documents_dir.exists() and any(documents_dir.iterdir()):
        return documents_dir
    if base.exists() and any(base.iterdir()):
        return base
    return documents_dir


def rebuild_private_index(user_id: str | None = None) -> dict[str, int]:
    vault_path = private_vault_for_user(user_id)
    vault_path.mkdir(parents=True, exist_ok=True)
    pipeline = IndexingPipeline(
        vault_path=vault_path,
        repository=DocumentRepository(Path(settings.database_path)),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        vector_store=VectorStore(Path(settings.vector_store_path)),
        embedding_model=get_embedding_model(settings.embedding_model),
        max_document_size=settings.max_document_size,
        user_id=user_id,
    )
    return pipeline.rebuild()