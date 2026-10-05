"""Deterministic Step 9 evaluation cases for graph extraction and retrieval."""

GRAPH_CASES = (
    {
        "text": "Machine learning uses vector search for retrieval.",
        "expected_concepts": {"machine learning", "vector search"},
        "excluded_concepts": {"uses", "for"},
    },
    {
        "text": "Feature engineering improves neural network classification.",
        "expected_concepts": {"feature engineering", "neural network", "classification"},
        "excluded_concepts": {"improves"},
    },
)
