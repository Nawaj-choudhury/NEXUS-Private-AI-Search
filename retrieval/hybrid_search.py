from search_engine.engine import SearchEngine
from reranker.deduplicator import Deduplicator
from reranker.local_reranker import LocalReranker
from reranker.models import RerankCandidate
from reranker.pipeline import RerankPipeline
from .models import HybridResult, RetrievalMetadata
from .semantic_search import SemanticSearch
from .fusion import reciprocal_rank_fusion


class HybridSearch:
    def __init__(
        self,
        bm25_engine: SearchEngine,
        semantic_search: SemanticSearch,
        top_k: int = 10,
        rrf_k: int = 60,
        reranker: LocalReranker | None = None,
        candidate_top_k: int = 20,
        final_top_k: int = 5,
        duplicate_similarity_threshold: float = 0.9,
    ) -> None:
        self.bm25_engine = bm25_engine
        self.semantic_search = semantic_search
        self.top_k = top_k
        self.rrf_k = rrf_k
        self.reranker = reranker or LocalReranker(enabled=True)
        self.candidate_top_k = candidate_top_k
        self.final_top_k = final_top_k
        self.deduplicator = Deduplicator(similarity_threshold=duplicate_similarity_threshold)

    def search(self, query: str, mode: str = "hybrid", rerank: bool = False, source_type: str | None = None, user_id: str | None = None) -> list[HybridResult]:
        if mode == "keyword":
            return self._keyword_results(query, source_type)
        if mode == "semantic":
            return self._semantic_results(query, source_type, user_id=user_id)
        if mode != "hybrid":
            raise ValueError(f"Unsupported search mode: {mode}")

        base_results = self._hybrid_results(query, source_type, user_id=user_id)
        if rerank:
            return self._reranked_results(query, base_results)
        return base_results[: self.top_k]

    def _hybrid_results(self, query: str, source_type: str | None = None, user_id: str | None = None) -> list[HybridResult]:
        bm25 = self._keyword_results(query, source_type)
        semantic = self._semantic_results(query, source_type, user_id=user_id)
        by_id = {result.chunk_id: result for result in bm25 + semantic}
        fused = reciprocal_rank_fusion(
            [[(result.chunk_id, result) for result in bm25], [(result.chunk_id, result) for result in semantic]],
            self.rrf_k,
        )
        results: list[HybridResult] = []
        for rank, (chunk_id, score, ranks) in enumerate(fused[: self.candidate_top_k], start=1):
            result = by_id[chunk_id]
            results.append(HybridResult(result.document_id, result.chunk_id, result.filename, result.source_path, result.content, score, RetrievalMetadata("hybrid", ranks.get("bm25_rank"), ranks.get("semantic_rank"), rank, score), result.source_type, result.url, result.domain))
        return results

    def _reranked_results(self, query: str, candidates: list[HybridResult]) -> list[HybridResult]:
        rerank_candidates = [
            RerankCandidate(
                document_id=result.document_id,
                chunk_id=result.chunk_id,
                title=result.filename,
                source=result.source_path,
                content=result.content,
                bm25_rank=result.metadata.bm25_rank,
                semantic_rank=result.metadata.semantic_rank,
                rrf_score=result.metadata.fusion_score if result.metadata.fusion_score is not None else result.score,
                reranker_score=0.0,
                final_rank=0,
                evidence_score=0.0,
                retrieval_method=result.metadata.retrieval_method,
            )
            for result in candidates
        ]
        pipeline = RerankPipeline(reranker=self.reranker, candidate_top_k=self.candidate_top_k, final_top_k=self.final_top_k, deduplicator=self.deduplicator)
        selected = pipeline.run(query, rerank_candidates)
        by_id = {result.chunk_id: result for result in candidates}
        final_results: list[HybridResult] = []
        for index, candidate in enumerate(selected, start=1):
            original = by_id.get(candidate.chunk_id)
            if original is None:
                continue
            final_results.append(
                HybridResult(
                    original.document_id,
                    original.chunk_id,
                    original.filename,
                    original.source_path,
                    original.content,
                    score=max(candidate.evidence_score, candidate.reranker_score),
                    metadata=RetrievalMetadata(
                        retrieval_method="hybrid",
                        bm25_rank=original.metadata.bm25_rank,
                        semantic_rank=original.metadata.semantic_rank,
                        hybrid_rank=index,
                        fusion_score=original.metadata.fusion_score,
                        reranker_score=candidate.reranker_score,
                        evidence_score=candidate.evidence_score,
                        final_rank=index,
                    ),
                    source_type=original.source_type,
                    url=original.url,
                    domain=original.domain,
                )
            )
        return final_results

    def _keyword_results(self, query: str, source_type: str | None = None) -> list[HybridResult]:
        results = self.bm25_engine.search(query, self.top_k)
        if source_type:
            results = [result for result in results if result.document.source_type == source_type]
        return [HybridResult(result.document.document_id or result.document.id, result.document.chunk_id or result.document.id, result.document.title, result.document.source, result.document.content, result.score, RetrievalMetadata("keyword", bm25_rank=rank), result.document.source_type, result.document.url, result.document.domain) for rank, result in enumerate(results, start=1)]

    def _semantic_results(self, query: str, source_type: str | None = None, user_id: str | None = None) -> list[HybridResult]:
        if user_id is None:
            semantic_hits = self.semantic_search.search(query, source_type)
        else:
            semantic_hits = self.semantic_search.search(query, source_type, user_id=user_id)
        return [HybridResult(result.document_id, result.chunk_id, result.filename, result.source_path, result.content, result.score, RetrievalMetadata("semantic", semantic_rank=rank), result.source_type, result.url, result.domain) for rank, result in enumerate(semantic_hits, start=1)]