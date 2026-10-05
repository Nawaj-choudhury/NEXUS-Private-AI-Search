from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CandidateEvidence:
    document_id: str
    chunk_id: str
    title: str
    source: str
    content: str
    score: float = 0.0


@dataclass(frozen=True, slots=True)
class RerankCandidate:
    document_id: str
    chunk_id: str
    title: str
    source: str
    content: str
    bm25_rank: int | None = None
    semantic_rank: int | None = None
    rrf_score: float | None = None
    reranker_score: float = 0.0
    final_rank: int = 0
    evidence_score: float = 0.0
    retrieval_method: str = "hybrid"


@dataclass(frozen=True, slots=True)
class RerankDecision:
    candidate: RerankCandidate
    evidence_score: float = 0.0
    final_rank: int = 0
    notes: str = ""
