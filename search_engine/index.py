from collections import defaultdict

from .models import Document
from .tokenizer import tokenize


class InMemoryIndex:
    """Small inverted index that can later be replaced by another index backend."""

    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}
        self._postings: dict[str, set[str]] = defaultdict(set)

    @property
    def document_count(self) -> int:
        return len(self._documents)

    def add_document(self, document: Document) -> None:
        if document.id in self._documents:
            self._remove_document(document.id)

        self._documents[document.id] = document
        for term in set(tokenize(f"{document.title} {document.content}")):
            self._postings[term].add(document.id)

    def get_document(self, document_id: str) -> Document:
        return self._documents[document_id]

    def document_frequency(self, term: str) -> int:
        return len(self._postings.get(term, set()))

    @property
    def average_document_length(self) -> float:
        if not self._documents:
            return 0.0
        return sum(len(tokenize(f"{document.title} {document.content}")) for document in self._documents.values()) / len(self._documents)

    def retrieve_candidates(self, terms: list[str]) -> list[Document]:
        candidate_ids = set()
        for term in set(terms):
            candidate_ids.update(self._postings.get(term, set()))
        return [self._documents[document_id] for document_id in candidate_ids]

    def _remove_document(self, document_id: str) -> None:
        document = self._documents.pop(document_id)
        for term in set(tokenize(f"{document.title} {document.content}")):
            self._postings[term].discard(document_id)