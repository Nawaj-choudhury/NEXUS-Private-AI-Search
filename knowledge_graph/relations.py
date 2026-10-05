from collections import Counter
from itertools import combinations

from .models import Concept, Edge


def document_concept_edges(document_node_id: str, concepts: list[Concept]) -> list[Edge]:
    return [Edge(document_node_id, concept.concept_id, "MENTIONS", float(concept.occurrence_count), concept.occurrence_count, "concept-extraction") for concept in concepts]


def concept_cooccurrence_edges(concepts_by_chunk: dict[str, list[Concept]]) -> list[Edge]:
    counts: Counter[tuple[str, str]] = Counter()
    for concepts in concepts_by_chunk.values():
        ids = sorted({concept.concept_id for concept in concepts})
        for left, right in combinations(ids, 2):
            counts[(left, right)] += 1
    return [Edge(left, right, "RELATED_TO", float(count), count, "same-chunk-cooccurrence") for (left, right), count in sorted(counts.items())]