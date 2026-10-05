from collections.abc import Sequence


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence[tuple[str, object]]],
    rrf_k: int = 60,
) -> list[tuple[str, float, dict[str, int]]]:
    """Fuse ranked IDs with RRF and retain each method's one-based rank."""
    if rrf_k <= 0:
        raise ValueError("rrf_k must be positive")
    scores: dict[str, float] = {}
    ranks: dict[str, dict[str, int]] = {}
    for method_index, ranked_list in enumerate(ranked_lists):
        method_name = "bm25" if method_index == 0 else "semantic"
        for rank, item in enumerate(ranked_list, start=1):
            item_id = item[0]
            scores[item_id] = scores.get(item_id, 0.0) + 1 / (rrf_k + rank)
            ranks.setdefault(item_id, {})[f"{method_name}_rank"] = rank
    fused = [(item_id, score, ranks[item_id]) for item_id, score in scores.items()]
    fused.sort(key=lambda item: (-item[1], item[0]))
    return fused