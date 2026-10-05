from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from .models import RerankCandidate


class BaseReranker(ABC):
    """Abstract interface for candidate reranking."""

    @abstractmethod
    def rerank(self, query: str, candidates: Sequence[RerankCandidate]) -> list[RerankCandidate]:
        """Return the same candidates sorted by a stronger relevance signal."""
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> dict[str, str]:
        """Return structured status for the reranker provider and active state."""
        raise NotImplementedError
