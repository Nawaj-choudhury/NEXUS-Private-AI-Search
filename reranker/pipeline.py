from __future__ import annotations

import logging
from collections.abc import Sequence

from .base import BaseReranker
from .deduplicator import Deduplicator
from .local_reranker import LocalReranker
from .models import RerankCandidate
from .scorer import EvidenceQualityScorer

logger = logging.getLogger(__name__)


class RerankPipeline:
    def __init__(
        self,
        reranker: BaseReranker | None = None,
        candidate_top_k: int = 20,
        final_top_k: int = 5,
        deduplicator: Deduplicator | None = None,
    ) -> None:
        self.reranker = reranker or LocalReranker(enabled=False)
        self.candidate_top_k = candidate_top_k
        self.final_top_k = final_top_k
        self.deduplicator = deduplicator or Deduplicator()

    def run(self, query: str, candidates: Sequence[RerankCandidate]) -> list[RerankCandidate]:
        limited = list(candidates)[: self.candidate_top_k]
        logger.info("Rerank pipeline candidate count=%d", len(limited))
        deduped = self.deduplicator.filter_duplicates(limited)
        logger.info("Rerank pipeline deduplicated count=%d", len(deduped))
        if not deduped:
            return []

        ranked = self.reranker.rerank(query, deduped)
        max_rrf = max((candidate.rrf_score or 0.0) for candidate in ranked) if ranked else 0.0
        reranker_min = min((candidate.reranker_score for candidate in ranked), default=0.0)
        reranker_max = max((candidate.reranker_score for candidate in ranked), default=0.0)
        scored: list[RerankCandidate] = []
        for index, candidate in enumerate(ranked, start=1):
            evidence_score = EvidenceQualityScorer.score(candidate, max_rrf, reranker_min, reranker_max)
            scored.append(
                RerankCandidate(
                    document_id=candidate.document_id,
                    chunk_id=candidate.chunk_id,
                    title=candidate.title,
                    source=candidate.source,
                    content=candidate.content,
                    bm25_rank=candidate.bm25_rank,
                    semantic_rank=candidate.semantic_rank,
                    rrf_score=candidate.rrf_score,
                    reranker_score=candidate.reranker_score,
                    final_rank=index,
                    evidence_score=evidence_score,
                    retrieval_method=candidate.retrieval_method,
                )
            )
        final = sorted(scored, key=lambda item: (-item.evidence_score, -float(item.reranker_score), -(item.rrf_score or 0.0), item.title.lower()))
        final = [
            RerankCandidate(
                document_id=item.document_id,
                chunk_id=item.chunk_id,
                title=item.title,
                source=item.source,
                content=item.content,
                bm25_rank=item.bm25_rank,
                semantic_rank=item.semantic_rank,
                rrf_score=item.rrf_score,
                reranker_score=item.reranker_score,
                final_rank=rank,
                evidence_score=item.evidence_score,
                retrieval_method=item.retrieval_method,
            )
            for rank, item in enumerate(final[: self.final_top_k], start=1)
        ]
        logger.info("Rerank pipeline finalized count=%d", len(final))
        return final
