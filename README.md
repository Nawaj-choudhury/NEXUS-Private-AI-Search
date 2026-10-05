# NEXUS - Private AI Search Engine

## Private AI Search

NEXUS is a local-first search and research workspace for private documents and explicitly selected public web sources. It combines keyword retrieval, local semantic embeddings, hybrid ranking, local reranking, citation-backed research through Ollama, and a bounded knowledge graph without sending private content to cloud AI services.

## Quick Start

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Push-Location frontend; npm install; Pop-Location
Copy-Item .env.example .env
python -m scripts.setup
python -m scripts.prepare_models
python -m scripts.demo_setup
```

Start the backend with `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000` and the frontend with `Push-Location frontend; npm run dev; Pop-Location`. Visit `http://localhost:5173`.

## Documentation

- [Deployment](docs/DEPLOYMENT.md)
- [API](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Privacy](docs/PRIVACY.md)
- [Security](docs/SECURITY.md)
- [Performance](docs/PERFORMANCE.md)
- [Evaluation](docs/EVALUATION.md)
- [Testing](docs/TESTING.md)
- [Development](docs/DEVELOPMENT.md)

## Features

- Private document indexing for `.txt`, `.md`, and `.pdf`
- Cookie-based registration/login and per-user private vault isolation
- BM25, semantic, hybrid, and local CrossEncoder retrieval
- Private, public-web, and combined source modes
- Local Ollama research with citations and evidence validation
- Controlled crawler with robots, SSRF, redirect, size, depth, and page limits
- Local SQLite knowledge graph with bounded discovery
- Production-style health/readiness endpoints, Docker assets, and CI

## Model Setup

Embedding: `sentence-transformers/all-MiniLM-L6-v2`

Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`

LLM: configured local Ollama model, default `llama3.2:1b`

Model acquisition is explicit:

```powershell
python -m scripts.prepare_models
python -m scripts.verify_models
```

Preparation populates the local cache. Runtime loads from that cache and private content stays local.

## Demo

```powershell
python -m scripts.demo_setup
python -m scripts.demo_check
```

The demo uses only the original sample files under `private_vault/documents/` and does not print document contents.

## Testing and CI

```powershell
python -m unittest discover -s tests -p "test_*.py" -q
python -m scripts.security_check
python -m scripts.performance_check
Push-Location frontend; npm run build; Pop-Location
```

GitHub Actions runs Python compilation/tests/security checks and the frontend build without downloading model weights during standard CI.

## Docker

Compose runs the backend in production mode and requires an exact HTTPS frontend origin and browser-reachable HTTPS API origin. Replace these placeholders with the origins served by your trusted TLS reverse proxy:

```powershell
$env:NEXUS_PRODUCTION_CORS_ORIGINS='["https://search.example.com"]'
$env:NEXUS_PRODUCTION_API_URL='https://api.example.com'
```

```powershell
docker compose -f deployment/docker-compose.yml up --build -d
```

The Compose setup exposes frontend port 8080 and backend port 8000 for a TLS reverse proxy, preserves local runtime data, and expects Ollama on the host by default. The plain HTTP mappings are not a production TLS endpoint. See [Deployment](docs/DEPLOYMENT.md).

## Project Structure

`backend/` FastAPI application, local authentication, and services; `frontend/` React/Vite UI; `retrieval/`, `reranker/`, and `search_engine/` ranking pipeline; `indexer/` per-user private ingestion; `crawler/` bounded public web ingestion; `knowledge_graph/` user-scoped graph storage and queries; `database/` SQLite repositories; `ai_engine/` local research; `scripts/` setup, verification, audit, and benchmark commands; `tests/` regression suite.

## Known Limitations and Future Work

Research depends on a locally installed and available Ollama model. Model preparation is intentionally separate from runtime. The crawler is bounded and is not a general web indexer. Evaluation uses a small project-specific dataset. Hosted inference and cloud deployment infrastructure are not included.

## License

License: not yet specified.

NEXUS is a privacy-first AI search engine project designed to help people search, understand, and work with information while keeping their data under their control.

The project will be developed in multiple phases, beginning with a stable backend and frontend foundation. Planned modules include the search engine, web crawler, document indexer, retrieval and reranking layers, AI research layer, private knowledge vault, knowledge graph, evaluation tooling, and deployment infrastructure.

The architecture is intentionally modular so each capability can be developed, tested, and improved independently as the project grows.

## Current Functionality

NEXUS supports local private document search for `.txt`, `.md`, and `.pdf` files. Each account has a user-scoped vault and authenticated private retrieval; public WEB search remains available without an account. NEXUS cleans and chunks documents, stores local indexing metadata and chunk text in SQLite, calculates configurable BM25 scores, and exposes ranked results through `GET /api/search?q=<query>` for the React frontend.

The bundled public demo documents live in `private_vault/documents/`. Authenticated user documents are indexed from `private_vault/documents/users/<user_id>/documents/`; rebuild the current user's local index through `POST /api/index/rebuild`.

```powershell
python -m indexer.cli
```

Re-indexing skips unchanged files, updates changed files, and removes deleted files. Source documents remain local, and the API exposes filenames rather than absolute filesystem paths.

## Two-Stage Retrieval

NEXUS uses a two-stage retrieval flow:

Stage 1: High-recall retrieval

Stage 2: High-precision reranking

The reranking stage is intentionally separate from the normal API and UI logic. It is local-only, does not send private content to a cloud model, and can safely fall back to the original hybrid ordering if the local reranker is unavailable.

Use `GET /api/search?q=machine%20learning&mode=hybrid&rerank=true` to enable second-stage reranking.

Run the retrieval benchmark after indexing:

```powershell
python -m evaluation.run
```

## AI Research Mode

Search retrieves ranked private documents. Research retrieves evidence, builds a bounded private context, sends that context only to the local Ollama service, generates a cited synthesis, validates the citations, and returns evidence and related topics.

The research endpoint is:

```text
POST /api/research
```

Example request:

```json
{"query":"How does machine learning learn from data?","mode":"hybrid","top_k":5}
```

Research uses the configured local Ollama model and never forwards private context to a cloud LLM. When evidence is absent, the local model is not called. Unsupported citation identifiers cause the generated answer to be withheld.

## Public Web Search

Public web ingestion is explicit and bounded through `POST /api/crawl`. NEXUS validates URLs, blocks local/private destinations by default, checks `robots.txt`, limits pages/depth/response size, extracts HTML text, and stores public pages in the local index with `source_type=public_web`. It does not perform autonomous or large-scale crawling.

Search supports three source modes:

- `private`: only the authenticated user's private documents
- `web`: only explicitly crawled public pages
- `all`: authenticated combined retrieval over the current user's private documents and public pages, with provenance preserved

Every mode except public `web` requires a valid session. Registration and login issue an HttpOnly session cookie; session tokens are not stored in browser storage. See [API](docs/API.md) for auth endpoints and response behavior.

Example crawl request:

```json
{"url":"https://example.com/article","max_pages":5,"max_depth":1}
```

Public results expose their title, domain, and verified fetched URL. Private results expose a filename only; local filesystem paths are never returned. Both public and private content are indexed and embedded locally. Public citations are generated only from fetched source metadata, while private citations remain path-free.

## Security & Privacy

NEXUS keeps private documents on the local machine: extraction, indexing, embeddings, retrieval, reranking, graph storage, and research through Ollama are local operations. Built-in authentication uses server-side sessions and user-scoped vault/index records; the browser receives only an HttpOnly cookie. Private content is not sent to public crawler URLs, hosted AI APIs, cloud vector stores, or analytics. Hugging Face access is limited to the explicit model-preparation command; runtime loads are local-only.

The backend enforces query, research, graph, crawl, document-size, page-count, depth, timeout, and response-size limits. Private ingestion allowlists `.txt`, `.md`, and `.pdf`, skips symlinks, and only discovers files beneath the configured vault. The crawler validates every URL and redirect, blocks local/private destinations by default, respects robots policy, and uses bounded requests. API responses use safe structured errors and do not expose stack traces, absolute paths, or private content. Health is high-level; readiness separately reports cached model and Ollama availability.

For production, set `ENVIRONMENT=production`, `COOKIE_SECURE=true`, and explicit HTTPS `CORS_ORIGINS`. Wildcard CORS and localhost origins are rejected in production. Keep `.env` ignored and leave `CRAWLER_ALLOW_LOCALHOST=false`.

Run the local static audit:

```powershell
python -m scripts.security_check
```

## Knowledge Discovery

NEXUS can build a local knowledge graph from indexed chunks:

```text
Search -> Results -> Concepts -> Relationships -> Interactive Exploration
```

Concepts are extracted deterministically from meaningful local phrases. `MENTIONS` edges connect source nodes to concepts, while `RELATED_TO` edges are created only when concepts co-occur in the same indexed chunk. Each relationship records its method, weight, and evidence count. Graph data is stored in `database/knowledge_graph.db` and is never sent to a cloud graph or AI service.

Run a graph rebuild explicitly with `POST /api/graph/rebuild`. The graph API supports bounded concept neighborhoods, related concepts, supporting sources, and graph search. Private source nodes expose titles and document IDs only. Public web nodes retain only verified public URL and domain metadata.

## Performance

Run the controlled benchmark with:

```powershell
python -m scripts.performance_check
```

It measures keyword, semantic, hybrid, reranked search, graph rebuild, and graph query using synthetic content and temporary local storage. It does not read private documents or create broad internet traffic. Measurements are workload- and machine-specific; the command prints the actual values from each run.

Back up `private_vault/documents/`, `database/nexus.db`, `database/vectors.db`, and `database/knowledge_graph.db` together. The source documents are authoritative and the indexes can be rebuilt locally. Never commit `.env` or private data.

## NEXUS Interface

The interface is organized around a premium product flow rather than a generic dashboard shell:

- **Search** returns ranked private/web sources with provenance and retrieval state.
- **Research** presents a grounded synthesis with visible citations, evidence, and related topics.
- **Knowledge map** turns the local graph into a bounded, selectable SVG exploration workspace.
- **Private vault** remains a quiet local-status indicator rather than an exposed filesystem surface.

The frontend uses centralized CSS design tokens, warm editorial typography, dark/light themes, and a restrained product aesthetic. `Cmd/Ctrl + K` opens the command palette, source scope and retrieval mode remain connected to the existing backend, and the layout adapts cleanly from desktop to mobile without sacrificing legibility. The result is a recognizably premium NEXUS interface that keeps the existing search and graph APIs intact while making the product feel intentional and cohesive.