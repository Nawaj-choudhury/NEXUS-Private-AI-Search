from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Document:
    id: str
    title: str
    content: str
    source: str
    document_id: str | None = None
    chunk_id: str | None = None
    source_type: str = "private"
    url: str | None = None
    domain: str | None = None


@dataclass(frozen=True, slots=True)
class SearchResult:
    document: Document
    snippet: str
    score: float