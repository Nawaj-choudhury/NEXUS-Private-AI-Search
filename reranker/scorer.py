from __future__ import annotations

from .models import RerankCandidate


class EvidenceQualityScorer:
    """Score evidence quality using three explicit signals:

    - retrieval relevance: normalized RRF contribution from the first-stage hybrid search
    - reranking relevance: normalized cross-encoder score within the ranked candidate set
    - evidence availability: 1 only when the chunk has usable text and source metadata

    The final value is the weighted combination of these signals:
    quality = 0.5 * rerank_norm + 0.3 * normalized_rrf + 0.2 * evidence_available.
    The raw CrossEncoder score is preserved as the rerank score; only the evidence-quality
    signal is normalized to [0, 1] so it stays comparable across candidates.
    """

    @staticmethod
    def score(candidate: RerankCandidate, max_rrf_score: float = 0.0, reranker_min: float | None = None, reranker_max: float | None = None) -> float:
        retrieval_relevance = 0.0
        if max_rrf_score > 0 and candidate.rrf_score is not None:
            retrieval_relevance = candidate.rrf_score / max_rrf_score

        raw_rerank = float(candidate.reranker_score)
        if reranker_min is not None and reranker_max is not None and reranker_max > reranker_min:
            reranking_relevance = (raw_rerank - reranker_min) / (reranker_max - reranker_min)
        else:
            reranking_relevance = 1.0 if raw_rerank >= 0 else 0.0
        evidence_availability = 1.0 if candidate.content.strip() and candidate.source and candidate.chunk_id else 0.0

        quality = (0.5 * reranking_relevance) + (0.3 * retrieval_relevance) + (0.2 * evidence_availability)
        return round(max(0.0, min(1.0, quality)), 6)


def compute_evidence_quality(candidate: RerankCandidate, max_rrf_score: float = 0.0, reranker_min: float | None = None, reranker_max: float | None = None) -> float:
    return EvidenceQualityScorer.score(candidate, max_rrf_score, reranker_min, reranker_max)
