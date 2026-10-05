import math
from collections import Counter

from .index import InMemoryIndex
from .models import Document
from .tokenizer import tokenize


class BM25Scorer:
    """Calculate BM25 relevance scores for indexed documents."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        if k1 < 0 or not 0 <= b <= 1:
            raise ValueError("BM25 requires k1 >= 0 and b between 0 and 1")
        self.k1 = k1
        self.b = b

    def score(self, document: Document, query_terms: list[str], index: InMemoryIndex) -> float:
        document_terms = tokenize(f"{document.title} {document.content}")
        term_counts = Counter(document_terms)
        document_length = max(len(document_terms), 1)
        average_length = max(index.average_document_length, 1.0)
        score = 0.0

        for term in set(query_terms):
            document_frequency = index.document_frequency(term)
            if not document_frequency:
                continue
            inverse_document_frequency = math.log(
                1 + (index.document_count - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            term_frequency = term_counts[term]
            denominator = term_frequency + self.k1 * (1 - self.b + self.b * document_length / average_length)
            score += inverse_document_frequency * (term_frequency * (self.k1 + 1) / denominator)

        return score