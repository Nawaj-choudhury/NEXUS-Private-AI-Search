# Performance

The benchmark uses 50 synthetic local documents, a temporary SQLite vector store, five timed repeats, and mean elapsed milliseconds. It does not read private documents or perform network access.

Measured run:

| Operation | Mean |
| --- | ---: |
| Keyword search | 4.709 ms |
| Semantic search | 1.366 ms |
| Hybrid search | 6.139 ms |
| Hybrid + reranker | 7.743 ms |
| Graph rebuild | 2.621 ms |
| Graph query | 0.004 ms |

Graph output for this run contained 57 nodes and 371 edges. These values describe this controlled development workload on the current machine; they are not universal production capacity claims. The benchmark is warm within each repeated operation and does not measure cold model startup or Ollama generation latency.

Run again with `python -m scripts.performance_check` to obtain fresh local measurements.
