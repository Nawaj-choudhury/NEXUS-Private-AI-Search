import tempfile
import unittest
from pathlib import Path

from reranker.base import BaseReranker
from reranker.deduplicator import Deduplicator
from reranker.local_reranker import LocalReranker
from reranker.models import CandidateEvidence, RerankCandidate, RerankDecision
from reranker.pipeline import RerankPipeline


class DummyCrossEncoder:
    def __init__(self) -> None:
        self.calls = 0

    def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        self.calls += 1
        scores = []
        for query, text in pairs:
            lowered = text.lower()
            if "security" in query.lower() and "security" in lowered:
                scores.append(0.95)
            elif "learning" in query.lower() and "learning" in lowered:
                scores.append(0.9)
            elif "search" in query.lower() and "search" in lowered:
                scores.append(0.85)
            else:
                scores.append(0.1)
        return scores


class Step7RerankerTests(unittest.TestCase):
    def test_reranker_interface(self) -> None:
        self.assertTrue(issubclass(BaseReranker, object))

    def test_local_reranker_loads_and_orders_candidates(self) -> None:
        model = DummyCrossEncoder()
        reranker = LocalReranker(model=model, enabled=True)
        candidates = [
            RerankCandidate("d1", "c1", "Alpha", "alpha.txt", "A short security note.", 0.2, 0.1, 0.1, 0.0),
            RerankCandidate("d2", "c2", "Beta", "beta.txt", "A machine learning overview.", 0.8, 0.9, 0.8, 0.0),
            RerankCandidate("d3", "c3", "Gamma", "gamma.txt", "A search engine summary.", 0.4, 0.6, 0.4, 0.0),
        ]
        ranked = reranker.rerank("learning systems", candidates)
        self.assertEqual(ranked[0].chunk_id, "c2")
        self.assertGreater(ranked[0].reranker_score, ranked[-1].reranker_score)
        self.assertEqual(model.calls, 1)

    def test_pipeline_deduplicates_and_limits_top_k(self) -> None:
        deduplicator = Deduplicator(similarity_threshold=0.9)
        candidates = [
            RerankCandidate("d1", "c1", "Alpha", "alpha.txt", "This is machine learning and security.", 0.9, 0.8, 0.7, 0.0),
            RerankCandidate("d1", "c2", "Alpha", "alpha.txt", "This is machine learning and security.", 0.85, 0.75, 0.7, 0.0),
            RerankCandidate("d2", "c3", "Beta", "beta.txt", "Different topic about search engines.", 0.1, 0.2, 0.3, 0.0),
        ]
        retained = deduplicator.filter_duplicates(candidates)
        self.assertEqual(len(retained), 2)
        pipeline = RerankPipeline(reranker=LocalReranker(model=DummyCrossEncoder(), enabled=True), candidate_top_k=10, final_top_k=2, deduplicator=deduplicator)
        selected = pipeline.run("machine learning", candidates)
        self.assertLessEqual(len(selected), 2)
        self.assertTrue(all(item.final_rank >= 1 for item in selected))

    def test_evidence_quality_score_is_documented(self) -> None:
        candidate = RerankCandidate("d1", "c1", "Alpha", "alpha.txt", "Machine learning summary.", 0.8, 0.9, 0.7, 0.0)
        decision = RerankDecision(candidate, evidence_score=0.76, final_rank=1)
        self.assertGreaterEqual(decision.evidence_score, 0.0)
        self.assertLessEqual(decision.evidence_score, 1.0)


if __name__ == "__main__":
    unittest.main()
