from collections.abc import Callable

from .dataset import DATASET
from .metrics import ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank


def _unique_documents(retrieved: list[str]) -> list[str]:
    """Keep the first occurrence of each document, preserving ranking order."""
    return list(dict.fromkeys(retrieved))


def run_benchmark(
    searchers: dict[str, Callable[[str], list[str]]],
    k: int = 3,
) -> dict[str, dict[str, float]]:
    report: dict[str, dict[str, float]] = {}

    for method, search in searchers.items():
        values = {
            "precision_at_k": [],
            "recall_at_k": [],
            "mrr": [],
            "ndcg_at_k": [],
        }

        for case in DATASET:
            retrieved = _unique_documents(search(case.query))
            relevant = set(case.relevant_document_ids)

            values["precision_at_k"].append(
                precision_at_k(retrieved, relevant, k)
            )
            values["recall_at_k"].append(
                recall_at_k(retrieved, relevant, k)
            )
            values["mrr"].append(
                reciprocal_rank(retrieved, relevant)
            )
            values["ndcg_at_k"].append(
                ndcg_at_k(retrieved, relevant, k)
            )

        report[method] = {
            metric: round(sum(scores) / len(scores), 4)
            for metric, scores in values.items()
        }

    return report