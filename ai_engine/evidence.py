from .context_builder import ContextItem
from .models import EvidenceItem


def extract_evidence(items: list[ContextItem], excerpt_chars: int = 320) -> tuple[EvidenceItem, ...]:
    return tuple(EvidenceItem(item.citation_id, item.text[:excerpt_chars], item.title, item.source, item.document_id, item.chunk_id, item.score, item.source_type, item.url) for item in items)