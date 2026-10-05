from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SemanticResult:
    document_id: str
    chunk_id: str
    filename: str
    source_path: str
    content: str
    score: float
    source_type: str = "private"
    url: str | None = None
    domain: str | None = None


@dataclass(frozen=True, slots=True)
class RetrievalMetadata:
    retrieval_method: str
    bm25_rank: int | None = None
    semantic_rank: int | None = None
    hybrid_rank: int | None = None
    fusion_score: float | None = None
    reranker_score: float | None = None
    evidence_score: float | None = None
    final_rank: int | None = None


@dataclass(frozen=True, slots=True)
class HybridResult:
    document_id: str
    chunk_id: str
    filename: str
    source_path: str
    content: str
    score: float
    metadata: RetrievalMetadata = field(default_factory=lambda: RetrievalMetadata("hybrid"))
    source_type: str = "private"
    url: str | None = None
    domain: str | None = None