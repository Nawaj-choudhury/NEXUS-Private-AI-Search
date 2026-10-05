from __future__ import annotations

import logging
import os
from collections.abc import Sequence

from model_cache import configure_model_cache, get_model_status

from .base import BaseReranker
from .models import RerankCandidate

logger = logging.getLogger(__name__)


class LocalReranker(BaseReranker):
    """Local cross-encoder reranker that uses the installed sentence-transformers API."""

    def __init__(self, model: object | None = None, enabled: bool = True, model_name: str | None = None) -> None:
        self.model_name = model_name or os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.model = model
        self.enabled = enabled
        self.status = "fallback"
        self.provider = "local_cross_encoder"
        configure_model_cache()
        if model is None and enabled and self.model_name:
            status = get_model_status(self.model_name, "reranker")
            if status.state == "READY_LOCAL":
                try:
                    from sentence_transformers import CrossEncoder

                    self.model = CrossEncoder(
                        self.model_name,
                        cache_folder=str(status.cache_dir),
                        local_files_only=True,
                    )
                    self.enabled = True
                    self.status = "READY_LOCAL"
                except Exception as exc:  # pragma: no cover - fallback behavior is intentionally safe
                    logger.warning("Reranker model '%s' could not be loaded from local cache: %s", self.model_name, exc)
                    self.model = None
                    self.enabled = False
                    self.status = "LOAD_FAILED"
            else:
                logger.warning(
                    "Reranker model '%s' is not cached locally. Run 'python -m scripts.prepare_models' before runtime. Status: %s",
                    self.model_name,
                    status.state,
                )
                self.model = None
                self.enabled = False
                self.status = status.state
        elif model is None:
            self.model = None
            self.enabled = False
            self.status = "fallback"

    def get_status(self) -> dict[str, str]:
        return {"provider": self.provider, "status": self.status}

    def set_status(self, status: str) -> None:
        if status in {"active", "READY_LOCAL", "fallback", "unavailable", "NOT_CACHED", "DOWNLOAD_REQUIRED", "LOAD_FAILED"}:
            self.status = status

    def rerank(self, query: str, candidates: Sequence[RerankCandidate]) -> list[RerankCandidate]:
        if not self.enabled or not candidates:
            return list(candidates)
        if self.model is None:
            self.set_status("fallback")
            return list(candidates)

        pairs = [(query, candidate.content) for candidate in candidates]
        if not hasattr(self.model, "predict"):
            self.set_status("unavailable")
            return list(candidates)

        try:
            predictions = self.model.predict(pairs, show_progress_bar=False, apply_softmax=False)
        except TypeError:
            predictions = self.model.predict(pairs)
        reranked: list[RerankCandidate] = []
        for candidate, prediction in zip(candidates, predictions, strict=True):
            score = float(prediction)
            reranked.append(
                RerankCandidate(
                    document_id=candidate.document_id,
                    chunk_id=candidate.chunk_id,
                    title=candidate.title,
                    source=candidate.source,
                    content=candidate.content,
                    bm25_rank=candidate.bm25_rank,
                    semantic_rank=candidate.semantic_rank,
                    rrf_score=candidate.rrf_score,
                    reranker_score=score,
                    final_rank=candidate.final_rank,
                    evidence_score=candidate.evidence_score,
                    retrieval_method=candidate.retrieval_method,
                )
            )
        reranked.sort(key=lambda item: (-item.reranker_score, -(item.rrf_score or 0.0), item.title.lower()))
        self.set_status("active")
        return reranked
