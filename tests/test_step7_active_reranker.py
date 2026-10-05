import unittest

from reranker.local_reranker import LocalReranker
from reranker.models import RerankCandidate


class DummyCrossEncoder:
    def __init__(self) -> None:
        self.calls = 0

    def predict(self, pairs, **kwargs):
        self.calls += 1
        results = []
        for query, text in pairs:
            lowered_query = query.lower()
            lowered_text = text.lower()
            if ("learning" in lowered_query or "learn" in lowered_query) and ("learning" in lowered_text or "learn" in lowered_text):
                results.append(0.92)
            elif ("security" in lowered_query or "secure" in lowered_query) and ("security" in lowered_text or "secure" in lowered_text):
                results.append(0.80)
            else:
                results.append(0.30)
        return results


class ActiveRerankerTests(unittest.TestCase):
    def test_real_crossencoder_loads_when_configured(self) -> None:
        reranker = LocalReranker(model=DummyCrossEncoder(), enabled=True, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.assertEqual(reranker.get_status()["provider"], "local_cross_encoder")
        self.assertEqual(reranker.get_status()["status"], "fallback")

    def test_real_reranker_scores_are_numeric_and_ordered(self) -> None:
        model = DummyCrossEncoder()
        reranker = LocalReranker(model=model, enabled=True, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
        candidates = [
            RerankCandidate("d1", "c1", "Alpha", "a.txt", "Learning from examples is crucial.", rrf_score=0.5),
            RerankCandidate("d2", "c2", "Beta", "b.txt", "Security controls prevent attacks.", rrf_score=0.7),
        ]
        ranked = reranker.rerank("How do computers learn patterns from examples?", candidates)
        self.assertEqual(len(ranked), 2)
        self.assertTrue(all(isinstance(item.reranker_score, float) for item in ranked))
        self.assertNotEqual(ranked[0].reranker_score, ranked[1].reranker_score)
        self.assertGreater(ranked[0].reranker_score, ranked[1].reranker_score)

    def test_fallback_status_is_reported_correctly(self) -> None:
        reranker = LocalReranker(model=None, enabled=False)
        self.assertEqual(reranker.get_status()["status"], "fallback")


if __name__ == "__main__":
    unittest.main()
