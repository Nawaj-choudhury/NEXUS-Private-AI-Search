from pathlib import Path

from backend.app.core.config import settings
from database.repository import DocumentRepository
from reranker.local_reranker import LocalReranker
from retrieval.embeddings import get_embedding_model
from retrieval.hybrid_search import HybridSearch
from retrieval.semantic_search import SemanticSearch
from retrieval.vector_store import VectorStore
from search_engine.engine import SearchEngine
from search_engine.models import Document
from .benchmark import run_benchmark


def _make_hybrid_search() -> HybridSearch:
    chunks = DocumentRepository(settings.database_path).all_chunks()
    documents = [Document(chunk.chunk_id, chunk.filename, chunk.content, chunk.filename, chunk.document_id, chunk.chunk_id) for chunk in chunks]
    return HybridSearch(
        SearchEngine(documents, settings.bm25_k1, settings.bm25_b),
        SemanticSearch(VectorStore(settings.vector_store_path), get_embedding_model(settings.embedding_model), settings.semantic_top_k),
        settings.hybrid_top_k,
        settings.rrf_k,
        reranker=LocalReranker(enabled=settings.reranker_enabled),
        candidate_top_k=settings.candidate_top_k,
        final_top_k=settings.final_top_k,
        duplicate_similarity_threshold=settings.duplicate_similarity_threshold,
    )


def main() -> None:
    hybrid = _make_hybrid_search()
    report = run_benchmark({
        "BM25": lambda query: [result.filename for result in hybrid._keyword_results(query)],
        "Semantic": lambda query: [result.filename for result in hybrid._semantic_results(query)],
        "Hybrid": lambda query: [result.filename for result in hybrid.search(query, "hybrid")],
        "Hybrid + Reranker": lambda query: [result.filename for result in hybrid.search(query, "hybrid", rerank=True)],
    })
    print(report)


if __name__ == "__main__":
    main()