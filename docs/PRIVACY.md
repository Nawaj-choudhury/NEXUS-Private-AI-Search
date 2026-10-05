# Technical Privacy Architecture

This document describes implementation boundaries, not legal certification.

## Local data

Private document bytes, extracted text, chunks, embeddings, reranker inputs, graph metadata, and research context remain on the local machine. Private source responses expose filenames and identifiers, not absolute filesystem paths.

Accounts use a built-in local session API. Passwords are hashed; random session tokens are held in HttpOnly cookies and only their hashes are stored server-side. Private vault files, chunks, vectors, research evidence, and graph nodes are scoped to the authenticated user. Public WEB search remains available without a session; private and combined retrieval require one.

## Network access

- Model preparation may contact Hugging Face only when `python -m scripts.prepare_models` is intentionally run.
- Runtime model loading is local-only from the configured cache.
- Research contacts only the configured local Ollama endpoint.
- Public web access occurs only through the explicit bounded crawler.
- No analytics, hosted vector store, cloud LLM, or browser telemetry path is configured.

## Public crawling

Crawler URLs are validated, private/loopback/link-local destinations are blocked by default, robots policy is required, redirects are revalidated, and page/depth/response/time limits are enforced.

## Storage and logs

SQLite databases and the private vault are local. Logs contain operational metadata and safe error categories, not document contents, full prompts, model responses, credentials, cookies, tokens, or private source paths.

## Deletion

Rebuilding after a private file disappears removes its document metadata, chunks, vectors, and stale graph contributions. Public indexed data uses the same document/chunk/vector/graph cleanup model.

## File protection

Only `.txt`, `.md`, and `.pdf` are supported. Files must be below the configured size limit, symlinks are skipped, and discovered paths must remain under the configured vault.
