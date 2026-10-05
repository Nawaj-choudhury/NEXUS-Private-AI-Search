from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request

from ..auth.dependencies import get_current_user
from ..schemas.search import RerankerStatusResponse, RetrievalMetadataResponse, RetrievalSummaryResponse, SearchResponse, SearchResultResponse
from database.repository import DocumentRepository
from backend.app.core.config import settings
from search_engine.engine import SearchEngine
from search_engine.models import Document
from retrieval.embeddings import get_embedding_model
from retrieval.hybrid_search import HybridSearch
from retrieval.semantic_search import SemanticSearch
from retrieval.vector_store import VectorStore
from backend.app.services.graph import get_graph_service

router = APIRouter(prefix="/api")


def get_search_engine(source_type: str | None = None, user_id: str | None = None) -> SearchEngine:
    chunks = DocumentRepository(settings.database_path).all_chunks(user_id=user_id, source_type=source_type)
    documents = [
        Document(
            id=chunk.chunk_id,
            title=chunk.filename,
            content=chunk.content,
            source=chunk.filename,
            document_id=chunk.document_id,
            chunk_id=chunk.chunk_id,
            source_type=chunk.source_type,
            url=chunk.url,
            domain=chunk.domain,
        )
        for chunk in chunks
        if source_type is None or chunk.source_type == source_type
    ]
    return SearchEngine(documents, k1=settings.bm25_k1, b=settings.bm25_b)


def get_hybrid_search(source_type: str | None = None, user_id: str | None = None) -> HybridSearch:
    return HybridSearch(
        get_search_engine(source_type, user_id=user_id),
        SemanticSearch(VectorStore(settings.vector_store_path), get_embedding_model(settings.embedding_model), settings.semantic_top_k),
        top_k=settings.hybrid_top_k,
        rrf_k=settings.rrf_k,
        candidate_top_k=settings.candidate_top_k,
        final_top_k=settings.final_top_k,
        duplicate_similarity_threshold=settings.duplicate_similarity_threshold,
    )


@router.get("/search", response_model=SearchResponse)
def search(
    q: str | None = None,
    request: Request = None,
    mode: Literal["keyword", "semantic", "hybrid", "private", "web", "all"] = "hybrid",
    rerank: bool | None = None,
) -> SearchResponse:
    normalized_query = (q or "").strip()
    if not normalized_query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    current_user = None
    if mode != "web" and request is not None:
        current_user = get_current_user(request)

    effective_rerank = settings.reranker_enabled if rerank is None else rerank
    source_type = {"private": "private", "web": "public_web"}.get(mode)
    retrieval_mode = "hybrid" if mode in {"private", "web", "all"} else mode
    if retrieval_mode != "hybrid":
        effective_rerank = False

    hybrid_search = get_hybrid_search(source_type, user_id=current_user.user_id if current_user else None)
    results = hybrid_search.search(normalized_query, mode=retrieval_mode, rerank=effective_rerank, source_type=source_type, user_id=current_user.user_id if current_user else None)
    status = hybrid_search.reranker.get_status() if hasattr(hybrid_search.reranker, "get_status") else {"provider": "local_cross_encoder", "status": "fallback"}
    summary = RetrievalSummaryResponse(
        mode=mode,
        reranked=effective_rerank and retrieval_mode == "hybrid" and status.get("status") == "active",
        candidate_count=settings.candidate_top_k if effective_rerank and retrieval_mode == "hybrid" else len(results),
        final_count=len(results),
        reranker=RerankerStatusResponse(provider=status.get("provider", "local_cross_encoder"), status=status.get("status", "fallback")),
    )
    return SearchResponse(
        query=normalized_query,
        total_results=len(results),
        retrieval=summary,
        results=[
            SearchResultResponse(
                title=result.filename,
                snippet=result.content,
                score=result.score,
                source=result.url if result.source_type == "public_web" and result.url else result.filename,
                document_id=result.document_id,
                chunk_id=result.chunk_id,
                reranker_score=result.metadata.reranker_score,
                evidence_score=result.metadata.evidence_score,
                final_rank=result.metadata.final_rank,
                source_type=result.source_type,
                url=result.url if result.source_type == "public_web" else None,
                domain=result.domain if result.source_type == "public_web" else None,
                retrieval=RetrievalMetadataResponse(
                    retrieval_method=result.metadata.retrieval_method,
                    bm25_rank=result.metadata.bm25_rank,
                    semantic_rank=result.metadata.semantic_rank,
                    hybrid_rank=result.metadata.hybrid_rank,
                    fusion_score=result.metadata.fusion_score,
                    reranker_score=result.metadata.reranker_score,
                    evidence_score=result.metadata.evidence_score,
                    final_rank=result.metadata.final_rank,
                ),
            )
            for result in results
        ],
        discovery={"concepts": [node.label for node in get_graph_service().discovery(normalized_query, user_id=current_user.user_id if current_user else None)]},
    )