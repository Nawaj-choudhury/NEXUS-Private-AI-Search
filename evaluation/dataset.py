from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvaluationQuery:
    query: str
    relevant_document_ids: frozenset[str]


DATASET = [
    EvaluationQuery("machine learning from data", frozenset({"sample_ml.md"})),
    EvaluationQuery("machine learning models and training", frozenset({"sample_ml.md"})),
    EvaluationQuery("protecting systems from threats", frozenset({"sample_security.txt"})),
    EvaluationQuery("cybersecurity measures against attacks", frozenset({"sample_security.txt"})),
    EvaluationQuery("finding information in documents", frozenset({"sample_search.txt"})),
    EvaluationQuery("search engine indexes and retrieval", frozenset({"sample_search.txt"})),
    EvaluationQuery("local private document search", frozenset({"sample_search.txt", "sample_ml.md"})),
    EvaluationQuery("safeguarding data with strong security", frozenset({"sample_security.txt"})),
    EvaluationQuery("learning from examples", frozenset({"sample_ml.md"})),
    EvaluationQuery("how documents are cached for retrieval", frozenset({"sample_search.txt"})),
]