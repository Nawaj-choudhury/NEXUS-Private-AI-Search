from .embeddings import EmbeddingProvider
from .models import SemanticResult
from .vector_store import VectorStore


class SemanticSearch:
    def __init__(self, vector_store: VectorStore, embedding_model: EmbeddingProvider, top_k: int = 10) -> None:
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.top_k = top_k

    def search(self, query: str, source_type: str | None = None, user_id: str | None = None) -> list[SemanticResult]:
        if not query.strip():
            return []
        return self.vector_store.search(self.embedding_model.embed_query(query), self.top_k, source_type, user_id=user_id)