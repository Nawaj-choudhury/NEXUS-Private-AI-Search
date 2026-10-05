# Architecture

```text
                         NEXUS
                           |
                +----------+----------+
                |                     |
             Frontend              Backend
                                      |
                         +------------+------------+
                         |                         |
                      Search                    Research
                         |                         |
                    Retrieval                 Evidence
                         |
                +--------+--------+
                |                 |
              BM25           Semantic
                |                 |
                +--------+--------+
                         |
                         RRF
                         |
                    CrossEncoder
                         |
                    Local Ollama

                Frontend -> Knowledge Graph API
```

The React/Vite frontend calls a FastAPI backend and keeps auth state in memory, restored through an HttpOnly session cookie. Search combines BM25 and local semantic retrieval with reciprocal rank fusion, then optionally applies the local CrossEncoder reranker. Research uses final evidence, bounded context construction, local Ollama generation, and citation validation. The graph is deterministic, user-scoped, bounded, and stored in SQLite.

Private flow:

```text
Private file -> loader -> cleaner -> chunker -> SQLite metadata/chunks
             -> local embedding -> vector store -> retrieval -> reranking -> research
```

Public flow:

```text
Explicit URL -> URL validation -> robots policy -> bounded fetch -> extraction
             -> local indexing/embedding -> retrieval -> reranking -> research
```

There are no cloud LLMs, cloud vector databases, external identity providers, or external analytics in the application architecture. Authentication is built into the local backend with hashed server-side sessions. Model acquisition is a separate intentional operation; runtime model loading is local-only.

Persistent stores are `database/nexus.db`, `database/vectors.db`, and `database/knowledge_graph.db`. Bundled demo samples are in `private_vault/documents/`; authenticated private documents are stored below `private_vault/documents/users/<user_id>/documents/`. Public indexed pages retain verified URL/domain provenance.
