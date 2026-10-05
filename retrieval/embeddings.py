from functools import lru_cache
from typing import Protocol

from model_cache import load_embedding_model_from_cache


class EmbeddingProvider(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class LocalEmbeddingModel:
    """Lazy local sentence-transformer model manager."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                self._model = load_embedding_model_from_cache(self.model_name, allow_download=False)
            except RuntimeError as error:
                raise RuntimeError("sentence-transformers is required for semantic search") from error
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self._load().encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [embedding.tolist() for embedding in embeddings]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


@lru_cache(maxsize=4)
def get_embedding_model(model_name: str) -> LocalEmbeddingModel:
    return LocalEmbeddingModel(model_name)