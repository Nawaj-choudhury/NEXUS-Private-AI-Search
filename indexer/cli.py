import logging
from pathlib import Path

from backend.app.core.config import settings
from database.repository import DocumentRepository
from .pipeline import IndexingPipeline
from retrieval.embeddings import get_embedding_model
from retrieval.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> None:
    summary = IndexingPipeline(
        Path(settings.private_vault_path),
        DocumentRepository(Path(settings.database_path)),
        settings.chunk_size,
        settings.chunk_overlap,
        vector_store=VectorStore(Path(settings.vector_store_path)),
        embedding_model=get_embedding_model(settings.embedding_model),
    ).rebuild()
    print(summary)


if __name__ == "__main__":
    main()