from dataclasses import dataclass

from retrieval.models import HybridResult


@dataclass(frozen=True, slots=True)
class ContextItem:
    citation_id: str
    document_id: str
    chunk_id: str
    title: str
    source: str
    text: str
    rank: int
    retrieval_method: str
    score: float
    source_type: str = "private"
    url: str | None = None


def build_context(results: list[HybridResult], max_chars: int) -> list[ContextItem]:
    items: list[ContextItem] = []
    used_chars = 0
    for rank, result in enumerate(results, start=1):
        text = result.content.strip()
        if not text or used_chars + len(text) > max_chars:
            break
        source = result.url if result.source_type == "public_web" and result.url else result.filename
        items.append(ContextItem(f"S{rank}", result.document_id, result.chunk_id, result.filename, source, text, rank, result.metadata.retrieval_method, result.score, result.source_type, result.url))
        used_chars += len(text)
    return items


def format_context(items: list[ContextItem]) -> str:
    return "\n\n".join(f"[{item.citation_id}] {'PUBLIC WEB' if item.source_type == 'public_web' else 'PRIVATE'} - {item.source}\n{item.text}" for item in items)