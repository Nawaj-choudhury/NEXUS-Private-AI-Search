# Development Rules

NEXUS will be developed incrementally. Each phase should leave the project understandable, testable, and ready for the next capability without implementing future modules prematurely.

## Planned Phases

1. Project foundation
2. Search engine core
3. Web crawler
4. Document processing and indexing
5. Hybrid retrieval
6. Result reranking
7. AI research layer
8. Private knowledge vault
9. Knowledge graph
10. Search quality evaluation
11. Premium UI/UX
12. Security and privacy
13. Testing
14. Docker/deployment
15. Documentation and final presentation

## Rules

- Keep the architecture modular.
- Do not put everything into one file.
- Do not create unnecessary dependencies.
- Do not hardcode secrets.
- Do not implement future modules prematurely.
- Write clean, readable, maintainable code.
- Follow professional naming conventions.
- Keep the project scalable.
- Do not replace the existing folder structure.

## Search Engine Core

The search engine currently uses a small, framework-independent in-memory inverted index. Each document is tokenized into normalized lowercase terms and added to postings lists that map each term to the documents containing it.

When a query arrives, it is normalized with the same tokenizer. The index retrieves candidate chunks by looking up the query terms in its postings lists. The BM25 scorer combines term frequency, document frequency, document length, and configurable `k1` and `b` parameters so terms that occur in fewer documents contribute more to relevance.

Candidates are sorted by their calculated BM25 score and returned as ranked `SearchResult` values. The scorer and index are separate modules so future vector, hybrid, or reranking implementations can replace individual strategies without changing the frontend response contract.

The private-document architecture is:

```text
Document
	↓
Loader
	↓
Cleaner
	↓
Chunker
	↓
Metadata
	↓
SQLite
	↓
BM25 Index
	↓
Search API
	↓
Frontend
```

The ingestion pipeline discovers supported files below the configured vault. Bundled demo files remain in `private_vault/documents/`; authenticated users are indexed from `private_vault/documents/users/<user_id>/documents/`. It fingerprints files to skip unchanged documents, replaces changed documents, and scopes stale-record cleanup to the current user.

## Security Architecture

Step 11 keeps the application local-first and bounded. Backend request schemas limit query, research, crawl, graph, and result sizes. Private ingestion accepts only `.txt`, `.md`, and `.pdf` files below the configured size limit, skips symlinks, and indexes only files discovered beneath the configured vault. SQLite writes use parameters and transactions; foreign-key cleanup is enabled on document writes.

The crawler accepts only HTTP(S) URLs without credentials, blocks loopback, link-local, private, reserved, and unspecified destinations by default, applies robots policy, limits pages/depth/response size/retries/timeouts, and revalidates every redirect before following it. API errors are structured and do not return stack traces, source paths, model details, or private content. Security headers include `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and a restrictive `Content-Security-Policy`.

Run the lightweight static sanity check with:

```powershell
python -m scripts.security_check
```

This scans application source for obvious credentials, wildcard CORS, executable subprocess calls, unsafe HTML injection, and literal cloud AI endpoints. It is not a replacement for a professional security audit.

## Privacy Boundary

```text
PRIVATE DOCUMENTS -> local extraction -> local embeddings -> local retrieval
				  -> local reranking -> local Ollama
PUBLIC WEB       -> explicit bounded crawl -> local indexing/embeddings
				  -> local retrieval -> local reranking -> local Ollama
```

Private document content is not sent to the crawler, public URLs, hosted AI APIs, hosted vector stores, analytics, or the frontend as filesystem paths. Public URLs originate from validated crawler metadata. Model preparation is the only intentional Hugging Face network operation; runtime model loading is local-only.

## Production Configuration

Set `ENVIRONMENT=production` and provide explicit non-local `CORS_ORIGINS`; wildcard CORS and localhost origins are rejected for production. Keep `.env` untracked, use conservative crawler and document limits, leave `CRAWLER_ALLOW_LOCALHOST=false`, and keep Ollama on a trusted local endpoint. `/health` reports high-level service state. `/readiness` reports whether cached embedding/reranker models and the configured local Ollama model are ready for full operation.

## Performance Testing

Run the controlled synthetic benchmark with:

```powershell
python -m scripts.performance_check
```

It measures keyword, semantic, hybrid, reranked search, graph rebuild, and graph query timing on synthetic in-memory content and a temporary local SQLite vector store. Results are machine- and workload-specific; the command prints the actual measurements from that run and does not read private documents.

## Backup and Recovery

Preserve the public demo samples and each user's `private_vault/documents/users/<user_id>/documents/` directory with the local SQLite stores when making a local backup. The source documents are authoritative; SQLite files can be rebuilt from them. Do not include `.env`, runtime SQLite files, private vault contents, or model caches in source control.

## Privacy

Private documents stay on the local machine. NEXUS does not send them to external services, does not log their contents, and does not expose absolute filesystem paths through the API. Personal documents are ignored by Git by default; only the small committed sample files are retained for local development.

## Privacy-Preserving Semantic Search

Semantic retrieval follows a local-only path:

```text
Document
	↓
Local Text Extraction
	↓
Local Embedding Model
	↓
Local Vector Store
	↓
Local Retrieval
```

The embedding model runs in the project environment and stores vectors plus chunk metadata in SQLite. No private document content is transmitted to OpenAI, Anthropic, Google, Groq, hosted Hugging Face inference, or another external embedding API.

## Hybrid Search with Reranking

```text
BM25
 +
Semantic
 ↓
RRF
 ↓
Candidate Pool
 ↓
Local Reranker
 ↓
Evidence Quality
 ↓
Research
```

BM25 is strong when exact terminology matters, while semantic search can find related language even when the query does not share exact words with a document. RRF combines both ranked lists without treating their raw score scales as directly comparable. The reranker is then used after the initial retrieval stage to improve precision on the candidate pool, focusing the final evidence on the highest-quality chunks. This is important because the first stage is designed for recall and the second stage is designed for precision.

Evidence quality scoring explicitly balances retrieval relevance, reranker relevance, and evidence availability. Duplicate filtering removes repeated or near-identical chunks while preserving distinct information from the same source when it is genuinely useful. The final evidence list is what research and citation validation use, so citations remain anchored to actual final evidence and not to filtered-out candidates.

## AI Research Layer

```text
		    User Question
			    ↓
		    Hybrid Search
			    ↓
		   Evidence Chunks
			    ↓
		    Context Builder
			    ↓
		   Citation Manager
			    ↓
		    Research Prompt
			    ↓
		    Local Ollama
			    ↓
		 Citation Validation
			    ↓
	    ┌───────────┼────────────┐
	    ↓           ↓            ↓
	 Answer      Evidence    Related Topics
```

The research layer is a grounded synthesis workflow, not a general chatbot. It accepts only retrieved chunks, assigns deterministic `[S1]`-style citations, preserves short exact evidence excerpts, and rejects unsupported citation identifiers. It also maps each short-answer sentence/clause to only its attached citation IDs, then compares meaningful normalized terms against the cited chunk text (never its title). A claim is `SUPPORTED` at 80% or greater term overlap with one cited item, `PARTIALLY_SUPPORTED` at 30%-79%, and `UNSUPPORTED` below 30%, for missing citations, or for a basic negation mismatch. These deterministic lexical thresholds are conservative triage, not entailment or fact-checking. Partial and unsupported claims are replaced by an evidence-limit notice; only strongly supported claims and their supporting citation IDs remain. The API exposes a `grounding` summary with `grounded`, `partially_grounded`, `unsupported`, or `not_assessed` status and per-claim states. Related topics are selected from terms present in retrieved evidence.

## Public Web Search

The Step 8 source boundary is explicit:

```text
		   QUERY
		     ↓
	    SOURCE SELECTION
		 /        \
	  PRIVATE       WEB
	    ↓            ↓
	 LOCAL         FETCH
	 INDEX          ↓
	    ↓        EXTRACT
	    │           ↓
	    │        LOCAL INDEX
	    │           │
	    └─────┬─────┘
		    ↓
	   HYBRID RETRIEVAL
		    ↓
	    CROSS-ENCODER
		    ↓
	     AI RESEARCH
```

`private` searches only the local vault, `web` searches only explicitly fetched public pages, and `all` combines both while retaining `source_type` provenance. Web crawling is queue-based, explicit, bounded by page count and depth, rate-limited, robots-aware, and protected against localhost, loopback, link-local, private-network, unsupported-content, oversized-response, duplicate, and excessive-redirect access. When `robots.txt` cannot be retrieved, the conservative policy skips the URL.

Private documents remain in the private vault and local vector/BM25 indexes. Public pages are marked `public_web`; their URL, domain, fetched timestamp, content hash, and optional HTTP freshness metadata are stored separately as provenance. No cloud embeddings or cloud LLMs are used.

Ollama is configured with `OLLAMA_BASE_URL` and `OLLAMA_MODEL`, and the default provider communicates only with the local Ollama HTTP API. The provider is replaceable through the small `LLMProvider` interface; the mock provider is test-only and never used by production configuration. Private document text is never sent to external LLM or hosted inference APIs.

## Knowledge Discovery

```text
		INDEXED CONTENT
			↓
	      CONCEPT EXTRACTION
			↓
	     RELATIONSHIP DETECTION
			↓
		GRAPH STORAGE
			↓
		GRAPH QUERY ENGINE
			↓
	    ┌─────────┴─────────┐
	    ↓                   ↓
      CONCEPT SEARCH       SOURCE DISCOVERY
	    ↓
      USER EXPLORATION
```

The graph is a local SQLite subsystem. Public concepts receive deterministic normalized IDs such as `concept:machine-learning`; private concept IDs are namespaced as `user:<user_id>:concept:<normalized-concept>`. Private source nodes are `document:<user_id>:<document_id>`, while public source nodes are `web:<document_id>`. `MENTIONS` edges come from deterministic concept extraction. `RELATED_TO` edges come from same-chunk co-occurrence only, so each edge has an explicit evidence method and count rather than an invented semantic claim.

Graph construction is explicit and persistent; search requests only query the existing graph discovery index and do not rebuild it. Traversal is bounded by maximum depth, node count, and edge weight. The Step 9 evaluation cases measure phrase preservation, stopword filtering, deterministic IDs, evidence-backed relationships, duplicate prevention, provenance, and orphan cleanup using temporary SQLite databases.

## Frontend Architecture

Step 10 keeps the existing API contract and composes the experience from a single responsive shell:

```text
NEXUS shell
├── Search instrument
├── Result provenance and actions
├── Research synthesis
├── Citations and evidence
├── Knowledge map
└── Command palette
```

The page owns only interaction state: query, source scope, retrieval mode, reranking, view, theme, and selected graph node. Existing service modules continue to call `/api/search`, `/api/research`, and the graph endpoints, so the backend contract remains stable. CSS variables define the design system for background, surface, ink, muted text, border, accent, signal, warning, and error tokens in both themes. Public URLs are rendered only when supplied by verified backend provenance; private sources remain filename-only and are never exposed as absolute filesystem paths.

The graph UX intentionally renders the backend's bounded neighborhood as SVG instead of introducing a new visualization dependency. Nodes are keyboard focusable, source types have distinct colors, and a selected node can trigger search or research actions. Focus-visible styles, semantic buttons, live loading states, error alerts, responsive breakpoints, and reduced-motion support remain part of the accessibility baseline.

## Design Tokens and Theme System

The frontend relies on a centralized design-token layer defined in the app stylesheet rather than arbitrary component-specific color values. The tokens include spacing, transitions, radii, shadow depth, and color variables for light and dark themes. This creates a consistent product language across search, research, citations, and graph views without coupling the styling to a single page or component.

## Graph UX

The knowledge map is intentionally sparse and bounded to the current graph payload rather than trying to visualize a large network all at once. The selected node is emphasized, related edges remain legible, and concept search/research actions are placed adjacent to the graph so the discovery flow feels native to the product rather than debug-like.

## Accessibility and Command Palette

The experience includes semantic buttons, visible keyboard focus, labels for the search field, a command palette powered by the same real actions as the product, and careful contrast across both themes. `Cmd/Ctrl + K` focuses the search field and opens the command surface, which exposes real actions such as search mode changes, research, discovery, and theme toggling.

## Responsive Behavior

The navigation rail collapses into a compact top bar on smaller screens, the research grid stacks vertically, and the graph and result panels remain readable without simply shrinking the desktop layout. The overall structure preserves hierarchy while adapting to mobile and tablet layouts without losing product clarity.