from __future__ import annotations

import re
from collections.abc import Sequence

from .models import RerankCandidate


class Deduplicator:
    """Remove repeated or near-identical evidence while preserving distinct evidence."""

    def __init__(self, similarity_threshold: float = 0.9) -> None:
        self.similarity_threshold = max(0.0, min(1.0, float(similarity_threshold)))

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {token for token in re.findall(r"\b\w+\b", text.lower()) if token}

    @staticmethod
    def similarity(left: str, right: str) -> float:
        left_tokens = Deduplicator._tokens(left)
        right_tokens = Deduplicator._tokens(right)
        if not left_tokens and not right_tokens:
            return 1.0
        if not left_tokens or not right_tokens:
            return 0.0
        union = left_tokens | right_tokens
        if not union:
            return 0.0
        intersection = left_tokens & right_tokens
        return len(intersection) / len(union)

    def filter_duplicates(self, candidates: Sequence[RerankCandidate]) -> list[RerankCandidate]:
        ordered = sorted(candidates, key=lambda candidate: (-(candidate.rrf_score or 0.0), -(candidate.reranker_score), candidate.title.lower()))
        kept: list[RerankCandidate] = []
        for candidate in ordered:
            if any(self._is_duplicate(candidate, existing) for existing in kept):
                continue
            kept.append(candidate)
        return kept

    def _is_duplicate(self, candidate: RerankCandidate, existing: RerankCandidate) -> bool:
        if candidate.chunk_id == existing.chunk_id and candidate.document_id == existing.document_id:
            return True
        similarity = self.similarity(candidate.content, existing.content)
        return similarity >= self.similarity_threshold
