import unittest
from unittest.mock import patch

from ai_engine.citation_manager import citations_for_context, validate_citations
from ai_engine.context_builder import build_context
from ai_engine.grounding import ground_answer
from ai_engine.models import ResearchRequest, ResearchResponse
from ai_engine.providers.mock import MockProvider
from ai_engine.providers.ollama import OllamaProvider
from ai_engine.researcher import Researcher
from ai_engine.topic_generator import generate_related_topics
from backend.app.api.research import research
from backend.app.schemas.research import ResearchRequestSchema
from retrieval.models import HybridResult, RetrievalMetadata


def retrieved(text: str = "Machine learning learns patterns from data.") -> list[HybridResult]:
    return [HybridResult("doc-1", "chunk-1", "sample_ml.md", "sample_ml.md", text, 0.9, RetrievalMetadata("hybrid", hybrid_rank=1, fusion_score=0.9))]


class Step6Tests(unittest.TestCase):
    def test_provider_interface_and_mock_are_deterministic(self) -> None:
        provider = MockProvider("Answer [S1]")
        self.assertTrue(provider.health_check())
        self.assertEqual(provider.generate("private context"), "Answer [S1]")
        self.assertEqual(provider.prompts, ["private context"])

    def test_ollama_provider_configuration_is_local(self) -> None:
        provider = OllamaProvider("http://127.0.0.1:11434", "llama3.2:1b")
        self.assertEqual(provider.base_url, "http://127.0.0.1:11434")
        self.assertEqual(provider.model, "llama3.2:1b")

    def test_context_citations_and_evidence_are_stable(self) -> None:
        items = build_context(retrieved(), 1000)
        self.assertEqual(items[0].citation_id, "S1")
        citations = citations_for_context(items)
        self.assertEqual(citations[0].chunk_id, "chunk-1")
        self.assertEqual(validate_citations("Answer [S1]", citations)[2], True)
        self.assertEqual(validate_citations("Answer [S9]", citations)[2], False)

    def test_research_orchestration_and_prompt_grounding(self) -> None:
        provider = MockProvider("Machine learning uses data patterns. [S1]")
        researcher = Researcher(lambda query, mode, top_k: retrieved(), provider, 1000)
        response = researcher.research(ResearchRequest("How does learning work?"))
        self.assertTrue(response.answer.citation_validation_passed)
        self.assertEqual(response.evidence[0].excerpt, "Machine learning learns patterns from data.")
        self.assertIn("Answer ONLY from the supplied context", provider.prompts[0])
        self.assertIn("[S1]", provider.prompts[0])

    def test_no_evidence_does_not_call_provider(self) -> None:
        provider = MockProvider()
        researcher = Researcher(lambda query, mode, top_k: [], provider)
        response = researcher.research(ResearchRequest("Unknown question"))
        self.assertFalse(response.evidence_sufficient)
        self.assertEqual(provider.prompts, [])
        self.assertIn("couldn't find enough", response.answer.text)

    def test_invalid_citation_withholds_answer(self) -> None:
        researcher = Researcher(lambda query, mode, top_k: retrieved(), MockProvider("Unsupported claim [S99]"))
        response = researcher.research(ResearchRequest("Question"))
        self.assertFalse(response.answer.citation_validation_passed)
        self.assertIn("withheld", response.answer.text)

    def test_claim_grounding_replaces_partially_supported_claim(self) -> None:
        items = build_context(retrieved("Machine learning finds useful patterns in data for prediction and classification."), 1000)
        answer, grounding = ground_answer("Machine learning uses supervised learning and feature engineering [S1].", items)
        self.assertEqual(grounding.status, "partially_grounded")
        self.assertEqual(grounding.claims[0].status, "PARTIALLY_SUPPORTED")
        self.assertNotIn("supervised learning", answer)
        self.assertIn("does not provide enough information", answer)

    def test_claim_grounding_keeps_supported_claim_and_its_citation(self) -> None:
        items = build_context(retrieved("Machine learning finds useful patterns in data for prediction and classification."), 1000)
        answer, grounding = ground_answer("Machine learning finds useful patterns in data [S1].", items)
        self.assertEqual(grounding.status, "grounded")
        self.assertEqual(grounding.claims[0].supporting_citation_ids, ("S1",))
        self.assertEqual(answer, "Machine learning finds useful patterns in data [S1].")

    def test_claim_grounding_associates_citation_after_sentence_punctuation(self) -> None:
        items = build_context(retrieved("Machine learning learns patterns from data."), 1000)
        answer, grounding = ground_answer("Machine learning uses data patterns. [S1]", items)
        self.assertEqual(grounding.status, "grounded")
        self.assertEqual(answer, "Machine learning uses data patterns [S1].")

    def test_claim_grounding_does_not_reuse_citation_support_between_sentences(self) -> None:
        items = build_context(retrieved("Machine learning finds useful patterns in data for prediction and classification."), 1000)
        answer, grounding = ground_answer(
            "Machine learning finds useful patterns in data [S1]. Supervised learning needs labeled training sets [S1].",
            items,
        )
        self.assertEqual([claim.status for claim in grounding.claims], ["SUPPORTED", "UNSUPPORTED"])
        self.assertIn("Machine learning finds useful patterns in data [S1].", answer)
        self.assertNotIn("labeled training sets", answer)

    def test_claim_grounding_keeps_citations_local_to_semicolon_clauses(self) -> None:
        results = [
            HybridResult("doc-1", "chunk-1", "ml.md", "ml.md", "Machine learning finds useful patterns in data.", 1.0, RetrievalMetadata("hybrid")),
            HybridResult("doc-2", "chunk-2", "security.md", "security.md", "Cybersecurity protects systems from threats.", 0.9, RetrievalMetadata("hybrid")),
        ]
        items = build_context(results, 1000)
        answer, grounding = ground_answer(
            "Machine learning finds useful patterns in data [S1]; cybersecurity protects systems from threats [S2].",
            items,
        )
        self.assertEqual([claim.status for claim in grounding.claims], ["SUPPORTED", "SUPPORTED"])
        self.assertEqual(answer, "Machine learning finds useful patterns in data [S1]. Cybersecurity protects systems from threats [S2].")
        self.assertIn("[S1]", answer)
        self.assertIn("[S2]", answer)

        swapped_answer, swapped_grounding = ground_answer(
            "Machine learning finds useful patterns in data [S2]; cybersecurity protects systems from threats [S1].",
            items,
        )
        self.assertEqual([claim.status for claim in swapped_grounding.claims], ["UNSUPPORTED", "UNSUPPORTED"])
        self.assertNotIn("finds useful patterns", swapped_answer)

    def test_claim_grounding_splits_cited_coordinated_claims(self) -> None:
        results = [
            HybridResult("doc-1", "chunk-1", "ml.md", "ml.md", "Machine learning finds useful patterns in data.", 1.0, RetrievalMetadata("hybrid")),
            HybridResult("doc-2", "chunk-2", "security.md", "security.md", "Cybersecurity protects systems from threats.", 0.9, RetrievalMetadata("hybrid")),
        ]
        items = build_context(results, 1000)
        answer, grounding = ground_answer(
            "Machine learning finds useful patterns in data [S1] and cybersecurity protects systems from threats [S2].",
            items,
        )
        self.assertEqual([claim.status for claim in grounding.claims], ["SUPPORTED", "SUPPORTED"])
        self.assertEqual(grounding.claims[0].citation_ids, ("S1",))
        self.assertEqual(grounding.claims[1].citation_ids, ("S2",))
        self.assertIn("[S1]. Cybersecurity", answer)

    def test_claim_grounding_uses_evidence_text_not_source_title(self) -> None:
        item = build_context(retrieved("Machine learning finds useful patterns in data."), 1000)[0]
        from dataclasses import replace

        titled_item = replace(item, title="Supervised learning feature engineering")
        answer, grounding = ground_answer("Supervised learning requires feature engineering [S1].", [titled_item])
        self.assertEqual(grounding.claims[0].status, "UNSUPPORTED")
        self.assertNotIn("Supervised learning requires", answer)

    def test_claim_grounding_rejects_negation_mismatch(self) -> None:
        items = build_context(retrieved("Machine learning finds useful patterns in data."), 1000)
        answer, grounding = ground_answer("Machine learning does not find useful patterns [S1].", items)
        self.assertEqual(grounding.claims[0].status, "UNSUPPORTED")
        self.assertNotIn("does not find", answer)

    def test_research_replaces_claims_not_supported_by_cited_evidence(self) -> None:
        provider = MockProvider("Machine learning uses supervised learning and feature engineering [S1].")
        response = Researcher(lambda query, mode, top_k: retrieved("Machine learning finds useful patterns in data for prediction and classification."), provider).research(ResearchRequest("How does machine learning work?"))
        self.assertNotIn("supervised learning", response.answer.text)
        self.assertIn("does not provide enough information", response.answer.text)
        self.assertEqual(response.answer.grounding.status, "partially_grounded")
        self.assertEqual(response.answer.grounding.claims_partially_supported, 1)
        self.assertFalse(response.answer.citation_validation_passed)

    def test_research_keeps_supported_claims_with_source_mapped_citations(self) -> None:
        provider = MockProvider("Machine learning finds useful patterns in data for prediction and classification [S1].")
        response = Researcher(lambda query, mode, top_k: retrieved("Machine learning finds useful patterns in data for prediction and classification."), provider).research(ResearchRequest("Question"))
        self.assertEqual(response.answer.grounding.status, "grounded")
        self.assertEqual(response.answer.grounding.claims_supported, 1)
        self.assertTrue(response.answer.citation_validation_passed)
        self.assertEqual(response.answer.citation_ids, ("S1",))

    def test_topics_are_evidence_derived(self) -> None:
        topics = generate_related_topics(build_context(retrieved("Machine learning systems use data."), 1000))
        self.assertEqual([topic.topic for topic in topics], ["machine learning"])

    def test_research_api_serializes_typed_response(self) -> None:
        response = ResearchResponse("Question", Researcher(lambda q, m, k: retrieved(), MockProvider("Machine learning learns patterns from data [S1].")).research(ResearchRequest("Question")).answer)
        with patch("backend.app.api.research.research_private_documents", return_value=response):
            api_response = research(ResearchRequestSchema(query="Question"))
        self.assertEqual(api_response.query, "Question")
        self.assertIsInstance(api_response.answer, str)
        self.assertEqual(api_response.grounding.status, "grounded")
        self.assertEqual(api_response.grounding.claims_checked, 1)

    def test_privacy_boundary_has_no_cloud_provider_dependency(self) -> None:
        import ai_engine.providers.ollama as ollama_module
        self.assertFalse(hasattr(ollama_module, "openai"))
        self.assertFalse(hasattr(ollama_module, "anthropic"))


if __name__ == "__main__":
    unittest.main()