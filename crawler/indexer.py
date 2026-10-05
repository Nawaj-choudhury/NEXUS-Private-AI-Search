from pathlib import Path

from crawler.models import WebPage
from database.repository import DocumentRepository
from indexer.chunker import chunk_document
from retrieval.embeddings import EmbeddingProvider
from retrieval.vector_store import VectorStore


class PublicWebIndexer:
    def __init__(self, repository: DocumentRepository, vector_store: VectorStore, embedding_model: EmbeddingProvider, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        self.repository = repository
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def index(self, pages: tuple[WebPage, ...]) -> dict[str, int]:
        indexed = 0
        unchanged = 0
        chunks_created = 0
        for page in pages:
            previous = self.repository.web_fingerprint(page.url)
            if previous and previous[0] == page.content_hash:
                unchanged += 1
                continue
            document_id = f"web:{page.content_hash}"
            chunks = chunk_document(document_id, page.title, page.content, self.chunk_size, self.chunk_overlap)
            self.repository.upsert_web_page(page, chunks)
            vectors = self.embedding_model.embed_documents([chunk.content for chunk in chunks])
            self.vector_store.upsert([
                (chunk.chunk_id, document_id, page.title, page.url, chunk.content, vector, "public_web", page.url, page.domain)
                for chunk, vector in zip(chunks, vectors, strict=True)
            ])
            indexed += 1
            chunks_created += len(chunks)
        return {"pages_indexed": indexed, "pages_unchanged": unchanged, "chunks_created": chunks_created}