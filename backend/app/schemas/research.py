from typing import Literal

from pydantic import BaseModel, Field


class ResearchRequestSchema(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    mode: str = Field(default="hybrid", pattern="^(keyword|semantic|hybrid|private|web|all)$")
    top_k: int = Field(default=5, ge=1, le=20)
    rerank: bool = True


class CitationSchema(BaseModel):
    citation_id: str
    title: str
    source: str
    document_id: str
    chunk_id: str
    source_type: str = "private"
    url: str | None = None


class EvidenceSchema(BaseModel):
    citation_id: str
    excerpt: str
    title: str
    source: str
    document_id: str
    chunk_id: str
    score: float
    source_type: str = "private"
    url: str | None = None


class RelatedTopicSchema(BaseModel):
    topic: str
    citation_ids: tuple[str, ...]


class SourceSchema(BaseModel):
    title: str
    source: str
    document_id: str
    chunk_id: str
    source_type: str = "private"
    url: str | None = None


class ClaimGroundingSchema(BaseModel):
    claim: str
    citation_ids: tuple[str, ...]
    supporting_citation_ids: tuple[str, ...]
    partially_supporting_citation_ids: tuple[str, ...]
    status: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED"]


class GroundingSchema(BaseModel):
    status: Literal["grounded", "partially_grounded", "unsupported", "not_assessed"]
    claims_checked: int
    claims_supported: int
    claims_partially_supported: int
    claims_unsupported: int
    claims: list[ClaimGroundingSchema]


class ResearchResponseSchema(BaseModel):
    query: str
    answer: str
    citations: list[CitationSchema]
    evidence: list[EvidenceSchema]
    related_topics: list[RelatedTopicSchema]
    sources: list[SourceSchema]
    evidence_sufficient: bool
    citation_validation_passed: bool
    grounding: GroundingSchema