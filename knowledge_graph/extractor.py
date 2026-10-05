import re
import unicodedata
from collections import Counter

from .models import Concept

_STOPWORDS = {
    "about", "after", "again", "also", "because", "before", "being", "between", "could", "from",
    "have", "into", "more", "most", "other", "over", "same", "some", "such", "than", "that",
    "their", "there", "these", "they", "this", "those", "through", "under", "using", "were", "which",
    "while", "with", "would", "your", "and", "for", "not", "the", "are", "can", "how", "its", "was",
    "uses", "use", "using", "supports", "support", "improves", "improve", "finds", "find", "includes",
    "include", "based", "good", "short", "different", "useful", "important",
}
_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")


def normalize_concept(label: str) -> str:
    normalized = unicodedata.normalize("NFKC", label).casefold()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized


def concept_id(label: str) -> str:
    return f"concept:{normalize_concept(label)}"


def extract_concepts(text: str, chunk_id: str = "", max_concepts: int = 30, min_frequency: int = 1) -> list[Concept]:
    tokens = [token.casefold() for token in _TOKEN_PATTERN.findall(text)]
    if not tokens:
        return []
    candidates: Counter[str] = Counter()
    for size in (2, 1):
        for index in range(len(tokens) - size + 1):
            phrase_tokens = tokens[index : index + size]
            if any(token in _STOPWORDS for token in phrase_tokens):
                continue
            if len(set(phrase_tokens)) != len(phrase_tokens):
                continue
            if size == 1 and (len(phrase_tokens[0]) < 5 or phrase_tokens[0].isdigit()):
                continue
            phrase = " ".join(phrase_tokens)
            candidates[phrase] += 1
    selected = [item for item in candidates.items() if item[1] >= min_frequency]
    selected.sort(key=lambda item: (-len(item[0].split()), -item[1], item[0]))
    concepts: list[Concept] = []
    for label, count in selected[:max_concepts]:
        concepts.append(Concept(concept_id(label), label, count, (chunk_id,) if chunk_id else ()))
    return concepts