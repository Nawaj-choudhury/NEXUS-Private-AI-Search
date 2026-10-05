# API

The backend listens on port 8000 by default. Responses never expose private absolute filesystem paths.

## `GET /health`

High-level liveness status. Returns `status` and component states for API, database, and graph store. It does not load models or contact Ollama.

## `GET /readiness`

Full local-service readiness. Returns `status` plus `embedding_model`, `reranker`, and `ollama` states. It reports `not_ready` when required local AI services are unavailable.

## `GET /api/search`

Parameters: `q` required, 1-500 characters; `mode` is `keyword`, `semantic`, `hybrid`, `private`, `web`, or `all`; `rerank` is optional boolean. Returns query, result count, retrieval summary, provenance-safe results, and graph discovery concepts.

Every mode except `web` requires an authenticated session. `private` returns only the current user's private records. `all` combines that user's private records with public-web records. Unauthenticated `web` searches are public. Authenticated semantic and hybrid retrieval is scoped before fusion and reranking.

Errors: `422` for invalid limits or values; `500` for unexpected failures. Private results expose filenames, not filesystem paths. Public URLs are verified crawler URLs.

## `POST /api/research`

Body:

```json
{"query":"machine learning","mode":"private","top_k":5,"rerank":true}
```

`query` is 1-500 characters; `top_k` is 1-20. Returns answer, citations, evidence, related topics, sources, citation validation status, and a `grounding` object containing a high-level status, claim counts, and claim-to-citation assessments. Claim states are `SUPPORTED`, `PARTIALLY_SUPPORTED`, or `UNSUPPORTED`; the summary states are `grounded`, `partially_grounded`, `unsupported`, or `not_assessed`. The local lexical overlap check is a conservative heuristic, not general-purpose fact checking. Uses only local Ollama. `503` indicates local AI/provider failure with a safe error code.

Research modes other than public `web` require authentication. Private evidence, sources, citations, and the context passed to local Ollama are limited to the current user's retrieval results.

## Authentication

- `POST /api/auth/register` accepts `email` and `password`; successful registration creates the account and starts an HttpOnly session. Duplicate email returns `409`.
- `POST /api/auth/login` accepts `email` and `password`; successful login starts an HttpOnly session. Invalid credentials return `401`.
- `GET /api/auth/me` returns the authenticated user or `401` when the session is absent, expired, or revoked.
- `POST /api/auth/logout` revokes the current server-side session and clears the cookie.

The cookie uses the configured name and SameSite policy; Secure is required in production. Frontends must send requests with credentials enabled. Session tokens are stored only as hashes in the database and are not exposed to JavaScript.

## `POST /api/index/rebuild`

Requires authentication. Indexes only the current user's vault and scopes stale document/vector cleanup to that user.

## `POST /api/crawl`

Body:

```json
{"url":"https://example.com/article","max_pages":5,"max_depth":1}
```

The URL must be HTTP(S), credential-free, and pass SSRF checks. Page count is 1-100 and depth is 0-5. Robots policy, redirect checks, response size, retries, and timeouts remain enforced. This endpoint indexes only explicitly requested public web pages.

## `POST /api/graph/rebuild`

Requires authentication. Rebuilds the local graph from indexed chunks while preserving user ownership. Returns document, concept, edge, and orphan counts. No network access is required.

## `GET /api/graph/search`

Requires authentication. Parameter `q` is 1-300 characters. Returns a bounded graph response scoped to the current user plus public nodes.

## `GET /api/graph/concept/{concept_id}`

Requires authentication. Returns a bounded neighborhood for an accessible concept identifier. Foreign or unknown private identifiers return an empty result. Identifiers are limited to 300 characters.

## `GET /api/graph/related/{concept_id}`

Requires authentication. Returns related concepts visible to the current user. `limit` is 1-50.

## `GET /api/graph/sources/{concept_id}`

Requires authentication. Returns supporting sources visible to the current user. `limit` is 1-100. Private sources remain path-free; public sources include verified URL/domain metadata.
