from .index import InMemoryIndex
from .models import Document, SearchResult
from .scorer import BM25Scorer
from .tokenizer import tokenize


class SearchEngine:
    def __init__(self, documents: list[Document] | None = None, k1: float = 1.5, b: float = 0.75) -> None:
        self._index = InMemoryIndex()
        self._scorer = BM25Scorer(k1=k1, b=b)
        for document in documents or []:
            self._index.add_document(document)

    def add_document(self, document: Document) -> None:
        self._index.add_document(document)

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        query_terms = tokenize(query)
        if not query_terms:
            return []

        candidates = self._index.retrieve_candidates(query_terms)
        scored = [
            (document, self._scorer.score(document, query_terms, self._index))
            for document in candidates
        ]
        scored.sort(key=lambda item: (-item[1], item[0].title.lower()))
        return [
            SearchResult(
                document=document,
                snippet=self._make_snippet(document, query_terms),
                score=round(raw_score, 4),
            )
            for document, raw_score in scored[:limit]
            if raw_score > 0
        ]

    @staticmethod
    def _make_snippet(document: Document, query_terms: list[str]) -> str:
        words = document.content.split()
        matching_index = next(
            (index for index, word in enumerate(words) if tokenize(word) and tokenize(word)[0] in query_terms),
            0,
        )
        start = max(matching_index - 8, 0)
        snippet_words = words[start : start + 28]
        suffix = "..." if start + len(snippet_words) < len(words) else ""
        return " ".join(snippet_words) + suffix