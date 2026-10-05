import hashlib
import logging
from pathlib import Path

from database.repository import DocumentRepository
from .cleaner import clean_text
from .chunker import chunk_document
from .loaders import SUPPORTED_EXTENSIONS, load_document
from .metadata import metadata_for_file
from .models import Document
from retrieval.embeddings import EmbeddingProvider
from retrieval.vector_store import VectorStore

logger = logging.getLogger(__name__)


class IndexingPipeline:
    def __init__(self, vault_path: Path, repository: DocumentRepository, chunk_size: int, chunk_overlap: int, vector_store: VectorStore | None = None, embedding_model: EmbeddingProvider | None = None, max_document_size: int = 20_000_000, user_id: str | None = None) -> None:
        self.vault_path = vault_path.resolve()
        self.repository = repository
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.max_document_size = max_document_size
        self.user_id = user_id

    def rebuild(self) -> dict[str, int]:
        files = sorted(
            path for path in self.vault_path.rglob("*")
            if path.is_file() and not path.is_symlink() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        active_paths = {metadata_for_file(path, self.vault_path, self.user_id).source_path for path in files}
        removed = self.repository.remove_missing_documents(active_paths, user_id=self.user_id)
        if self.vector_store:
            active_document_ids = {metadata_for_file(path, self.vault_path, self.user_id).document_id for path in files}
            self.vector_store.remove_missing_documents(active_document_ids, user_id=self.user_id)
        succeeded = 0
        failed = 0
        chunks_created = 0

        for path in files:
            metadata = metadata_for_file(path, self.vault_path, self.user_id)
            try:
                relative_path = path.resolve().relative_to(self.vault_path)
                if path.resolve().is_symlink() or relative_path.parts != path.relative_to(self.vault_path).parts:
                    raise ValueError("Document path escapes the private vault")
                content = path.read_bytes()
                if len(content) > self.max_document_size:
                    raise ValueError("Document exceeds the configured size limit")
                fingerprint = (len(content), hashlib.sha256(content).hexdigest())
                vectors_ready = self.vector_store is None or self.vector_store.has_document(metadata.document_id)
                if self.repository.document_fingerprint(metadata.source_path) == fingerprint and vectors_ready:
                    continue
                text = clean_text(load_document(path))
                document = Document(metadata.document_id, metadata.filename, metadata.file_type, metadata.source_path, text, metadata)
                chunks = chunk_document(metadata.document_id, metadata.filename, text, self.chunk_size, self.chunk_overlap)
                self.repository.upsert_document(document, fingerprint[1], chunks, user_id=self.user_id)
                if self.vector_store and self.embedding_model:
                    vectors = self.embedding_model.embed_documents([chunk.content for chunk in chunks])
                    self.vector_store.delete_document(metadata.document_id)
                    self.vector_store.upsert([
                        (chunk.chunk_id, chunk.document_id, chunk.filename, metadata.source_path, chunk.content, vector)
                        for chunk, vector in zip(chunks, vectors)
                    ], user_id=self.user_id)
                succeeded += 1
                chunks_created += len(chunks)
            except Exception as error:
                failed += 1
                logger.warning("Failed to index document error_type=%s", type(error).__name__)

        logger.info("Indexed %d/%d files, failed %d, created %d chunks, removed %d stale files", succeeded, len(files), failed, chunks_created, removed)
        return {"files_discovered": len(files), "files_indexed": succeeded, "files_failed": failed, "chunks_created": chunks_created, "files_removed": removed}