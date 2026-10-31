
# Evaluation

NEXUS includes a small, project-specific retrieval benchmark for regression checks and comparing retrieval configurations. It is not evidence of general-world search quality.

The benchmark contains 10 queries and uses the indexed sample documents. Relevance labels currently cover `sample_ml.md`, `sample_security.txt`, and `sample_search.txt`. The indexed corpus also contains `sample_ai.txt`, which is not explicitly labelled as relevant in the current dataset.

Metrics are averaged across the evaluation queries at **k = 3**. Retrieved chunks are deduplicated by filename before document-level metrics are calculated.

| Method | Precision@3 | Recall@3 | MRR | NDCG@3 |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 0.5167 | 0.9500 | 0.9000 | 0.9018 |
| Semantic | 0.3667 | 1.0000 | 0.9500 | 0.9693 |
| Hybrid | 0.3667 | 1.0000 | 0.9500 | 0.9693 |
| Hybrid + Reranker | 0.3667 | 1.0000 | 0.9500 | 0.9693 |

These values reflect the current local benchmark run and configuration. Identical aggregate scores do not establish that the methods rank every query identically or that reranking provides no benefit on other datasets.

## Reproducing the results

Prepare the sample index and required local models, then run:

```bash
python -m evaluation.run
```

The evaluation queries cover machine-learning, security, and document-search concepts in the project samples. Treat these results as a small regression baseline, not a broad performance claim.
