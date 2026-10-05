# Security

Step 11 security hardening is intentionally lightweight and local-first.

- SSRF: HTTP(S)-only URLs, no embedded credentials, DNS/IP checks for loopback, private, link-local, reserved, and unspecified destinations.
- Redirects: each redirect is normalized and checked again before following.
- Robots: inaccessible robots files fail closed.
- Files: `.txt`, `.md`, and `.pdf` allowlist, size/page limits, symlink exclusion, and vault containment.
- Database: SQL values are parameterized and connection transactions roll back on failure; foreign-key cleanup is enabled where writes occur.
- CORS: explicit origins only; wildcard origins are rejected and production disallows localhost origins.
- Authentication: Argon2 password hashes, server-side session records containing token hashes, HttpOnly cookies, expiry/revocation checks, and per-user private-data scoping.
- Headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and CSP are set by API middleware.
- Errors: API responses use safe messages and do not expose stack traces, paths, model internals, or private content.
- Logging: no full document content, prompts, responses, credentials, cookies, or bearer tokens.
- Cleanup: document removal removes metadata, chunks, vectors, and graph contributions.

Run `python -m scripts.security_check` for the repository’s static sanity check. It scans configured source patterns only and is not a professional security audit.
