import re

from .context_builder import ContextItem
from .models import Citation

CITATION_PATTERN = re.compile(r"\[(S\d+)\]")


def citations_for_context(items: list[ContextItem]) -> tuple[Citation, ...]:
    return tuple(Citation(item.citation_id, item.title, item.source, item.document_id, item.chunk_id, item.source_type, item.url) for item in items)


def validate_citations(answer: str, citations: tuple[Citation, ...]) -> tuple[str, tuple[str, ...], bool]:
    valid_ids = {citation.citation_id for citation in citations}
    found = tuple(dict.fromkeys(match.group(1) for match in CITATION_PATTERN.finditer(answer)))
    invalid = [citation_id for citation_id in found if citation_id not in valid_ids]
    if invalid:
        return answer, found, False
    return answer, found, True