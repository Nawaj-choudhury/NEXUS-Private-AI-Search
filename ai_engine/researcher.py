
import logging
from collections.abc import Callable

from retrieval.models import HybridResult

from .citation_manager import citations_for_context, validate_citations
from .context_builder import build_context, format_context
from .evidence import extract_evidence
from .grounding import ground_answer
from .models import ResearchAnswer, ResearchRequest, ResearchResponse, ResearchSource
from .prompts.research import build_research_prompt
from .providers.base import LLMProvider, ProviderError
from .topic_generator import generate_related_topics

logger = logging.getLogger(__name__)


class Researcher:
    def __init__(
        self,
        retriever: Callable[[str, str, int], list[HybridResult]],
        provider: LLMProvider,
        max_context_chars: int = 6000,
    ) -> None:
        self.retriever = retriever
        self.provider = provider
        self.max_context_chars = max_context_chars

    def research(self, request: ResearchRequest) -> ResearchResponse:
        query = request.query.strip()
        if not query:
            raise ValueError("Research query cannot be empty")

        results = self.retriever(query, request.mode, request.top_k)
        context_items = build_context(results, self.max_context_chars)

        if not context_items:
            answer = (
                "I couldn't find enough relevant evidence in your private "
                "knowledge base to answer this question reliably."
            )
            return ResearchResponse(
                query,
                ResearchAnswer(answer, (), True),
                evidence_sufficient=False,
            )

        citations = citations_for_context(context_items)
        logger.info(
            "Research retrieved %d evidence chunks using %s",
            len(context_items),
            request.mode,
        )

        try:
            generated = self.provider.generate(
                build_research_prompt(query, format_context(context_items))
            )
        except ProviderError:
            raise

        # Diagnostic logging: inspect citation IDs without weakening validation.
        _, generated_citation_ids, valid = validate_citations(
            generated, citations
        )
        valid_citation_ids = [
            citation.citation_id for citation in citations
        ]

        logger.warning(
            "Research citation diagnostic: generated_ids=%s "
            "valid_ids=%s citations_valid=%s raw_response=%r",
            generated_citation_ids,
            valid_citation_ids,
            valid,
            generated,
        )

        text, grounding = ground_answer(generated, context_items)

        if not valid:
            text = (
                "The local model returned unsupported citation references, "
                "so the answer was withheld."
            )
            citation_ids = ()
        else:
            text, citation_ids, final_citations_valid = validate_citations(
                text, citations
            )
            valid = (
                valid
                and final_citations_valid
                and grounding.status in {"grounded", "not_assessed"}
            )

        evidence = extract_evidence(context_items)
        sources = tuple(
            ResearchSource(
                item.title,
                item.source,
                item.document_id,
                item.chunk_id,
                item.source_type,
                item.url,
            )
            for item in context_items
        )

        return ResearchResponse(
            query,
            ResearchAnswer(text, citation_ids, valid, grounding),
            citations,
            evidence,
            generate_related_topics(context_items),
            sources,
        )
