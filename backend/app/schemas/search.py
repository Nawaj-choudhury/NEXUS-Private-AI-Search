from pydantic import BaseModel, Field


class SearchResultResponse(BaseModel):
    title: str
    snippet: str
    score: float = Field(ge=0)
    source: str
    document_id: str
    chunk_id: str
    retrieval: "RetrievalMetadataResponse"
    reranker_score: float | None = None
    final_rank: int | None = None
    evidence_score: float | None = None
    source_type: str = "private"
    url: str | None = None
    domain: str | None = None


class RetrievalMetadataResponse(BaseModel):
    retrieval_method: str
    bm25_rank: int | None = None
    semantic_rank: int | None = None
    hybrid_rank: int | None = None
    fusion_score: float | None = None
    reranker_score: float | None = None
    evidence_score: float | None = None
    final_rank: int | None = None


class RerankerStatusResponse(BaseModel):
    provider: str = "local_cross_encoder"
    status: str = "active"


class RetrievalSummaryResponse(BaseModel):
    mode: str
    reranked: bool = False
    candidate_count: int = 0
    final_count: int = 0
    reranker: RerankerStatusResponse = Field(default_factory=lambda: RerankerStatusResponse(provider="local_cross_encoder", status="fallback"))


class SearchResponse(BaseModel):
    query: str
    total_results: int
    retrieval: RetrievalSummaryResponse = Field(default_factory=lambda: RetrievalSummaryResponse(mode="hybrid", reranked=False, candidate_count=0, final_count=0, reranker=RerankerStatusResponse(provider="local_cross_encoder", status="fallback")))
    results: list[SearchResultResponse]
    discovery: "DiscoveryResponse" = Field(default_factory=lambda: DiscoveryResponse())


class SearchQuerySchema(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class DiscoveryResponse(BaseModel):
    concepts: list[str] = Field(default_factory=list)