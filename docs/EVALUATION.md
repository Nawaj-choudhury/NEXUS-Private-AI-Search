# Evaluation

The evaluation set is a small project-specific dataset based on the original sample documents. It is useful for regression checks, not a claim of general-world search quality.

Metrics are calculated at the project’s configured evaluation cutoff.

| Method | Precision | Recall | MRR | NDCG |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 0.5167 | 0.9500 | 0.9000 | 0.9018 |
| Semantic | 0.3667 | 1.0000 | 0.9500 | 0.9693 |
| Hybrid | 0.3667 | 1.0000 | 0.9000 | 0.9324 |
| Hybrid + Reranker | 0.3667 | 1.0000 | 0.9500 | 0.9693 |

Run `python -m evaluation.run` after the sample index and local models are prepared. The current dataset covers machine learning, security, and search concepts in the original project samples.
