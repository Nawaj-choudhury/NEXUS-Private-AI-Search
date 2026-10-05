import math
from collections.abc import Sequence


def precision_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    results = list(retrieved[:k])
    return sum(item in relevant for item in results) / len(results) if results else 0.0


def recall_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    return sum(item in relevant for item in retrieved[:k]) / len(relevant) if relevant else 0.0


def reciprocal_rank(retrieved: Sequence[str], relevant: set[str]) -> float:
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1 / rank
    return 0.0


def ndcg_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    dcg = sum((1 / math.log2(rank + 1)) for rank, item in enumerate(retrieved[:k], start=1) if item in relevant)
    ideal_hits = min(len(relevant), k)
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / ideal if ideal else 0.0