# Testing

Run the complete suite with:

```powershell
python -m unittest discover -s tests -p "test_*.py" -q
```

Run the suite to get the current test count; it includes auth and cross-user isolation regressions in addition to retrieval, indexing, graph, and security coverage.

Coverage areas include BM25 and retrieval behavior, semantic/vector storage, hybrid fusion, reranking, research/citation validation, crawler URL and robots behavior, graph construction/query/cleanup, indexing lifecycle, privacy boundaries, request limits, safe API errors, health/readiness, and deletion cleanup.

Model-dependent tests use the prepared local cache and skip or use test doubles where appropriate. Crawler tests use fake fetchers and robots policies; they do not create broad internet traffic. Research tests use mocked providers unless the live local verification is explicitly requested. Standard CI remains model-free where practical; `python -m scripts.verify_models` is a separate local integration check.

Additional checks:

```powershell
python -m scripts.security_check
python -m scripts.performance_check
python -m scripts.verify_models
Push-Location frontend
npm run build
Pop-Location
```
