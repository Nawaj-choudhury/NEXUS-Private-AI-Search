from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    query: str
    mode: str = "hybrid"
    top_k: int = 5
    rerank: bool = True


@dataclass(frozen=True, slots=True)
class Citation:
    citation_id: str
    title: str
    source: str
    document_id: str
    chunk_id: str
    source_type: str = "private"
    url: str | None = None


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    citation_id: str
    excerpt: str
    title: str
    source: str
    document_id: str
    chunk_id: str
    score: float
    source_type: str = "private"
    url: str | None = None


@dataclass(frozen=True, slots=True)
class ResearchSource:
    title: str
    source: str
    document_id: str
    chunk_id: str
    source_type: str = "private"
    url: str | None = None


@dataclass(frozen=True, slots=True)
class ClaimGrounding:
    claim: str
    citation_ids: tuple[str, ...]
    supporting_citation_ids: tuple[str, ...]
    partially_supporting_citation_ids: tuple[str, ...]
    status: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED"]


@dataclass(frozen=True, slots=True)
class GroundingSummary:
    status: Literal["grounded", "partially_grounded", "unsupported", "not_assessed"] = "not_assessed"
    claims_checked: int = 0
    claims_supported: int = 0
    claims_partially_supported: int = 0
    claims_unsupported: int = 0
    claims: tuple[ClaimGrounding, ...] = ()


@dataclass(frozen=True, slots=True)
class RelatedTopic:
    topic: str
    citation_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResearchAnswer:
    text: str
    citation_ids: tuple[str, ...]
    citation_validation_passed: bool
    grounding: GroundingSummary = field(default_factory=GroundingSummary)


@dataclass(frozen=True, slots=True)
class ResearchResponse:
    query: str
    answer: ResearchAnswer
    citations: tuple[Citation, ...] = ()
    evidence: tuple[EvidenceItem, ...] = ()
    related_topics: tuple[RelatedTopic, ...] = ()
    sources: tuple[ResearchSource, ...] = ()
    evidence_sufficient: bool = True