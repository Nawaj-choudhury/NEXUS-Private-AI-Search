# Deployment

NEXUS is a local-first FastAPI and React application. The supported deployment modes are local development, a production-style local process, and Docker Compose.

## Development on Windows

Prerequisites: Python 3.11+, Node.js/npm, and optional Ollama for research.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Push-Location frontend
npm install
Pop-Location
python -m scripts.setup
python -m scripts.prepare_models
python -m scripts.demo_setup
```

Start the backend in one PowerShell window:

```powershell
$env:PYTHONPATH='.'
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in another:

```powershell
Push-Location frontend
npm run dev
Pop-Location
```

Open `http://localhost:5173`. Verify `http://localhost:8000/health` and `/readiness`.

## Production-style local process

Set `ENVIRONMENT=production`, explicit non-local `CORS_ORIGINS`, conservative limits, and a trusted `OLLAMA_BASE_URL` in `.env`. Prepare models once with `python -m scripts.prepare_models`; normal runtime is local-only. Start Uvicorn without reload and serve the built frontend with a static web server.

## Docker Compose

The Compose backend runs in production mode, so it requires a Secure session cookie and an exact, non-local HTTPS browser origin. Put the following environment values in the shell or a private deployment environment file before building. Replace the example origins with the actual URLs served by a trusted TLS reverse proxy; do not commit deployment credentials or machine-specific settings.

```powershell
$env:NEXUS_PRODUCTION_CORS_ORIGINS='["https://search.example.com"]'
$env:NEXUS_PRODUCTION_API_URL='https://api.example.com'
```

From the repository root:

```powershell
docker compose -f deployment/docker-compose.yml build
docker compose -f deployment/docker-compose.yml up -d
```

The containers expose frontend port 8080 and backend port 8000 for a trusted TLS reverse proxy. The backend runs as a non-root user. No private documents or model files are copied into the image. The plain HTTP port mappings are not a production TLS endpoint; keep the proxy and API private behind the configured HTTPS origins.

The Compose backend stores runtime data in the `nexus_data` volume and mounts `private_vault/documents` from the host. Persistent data includes `database/nexus.db`, `database/vectors.db`, `database/knowledge_graph.db`, model caches, and private documents. Back up the volume and the host vault together.

Ollama is not started by Compose. By default the backend uses `host.docker.internal:11434`. Set `OLLAMA_BASE_URL` to a reachable host Ollama endpoint, or run an optional Ollama container separately on a private network. Do not publish Ollama publicly.

Stop services:

```powershell
docker compose -f deployment/docker-compose.yml down
```

## Troubleshooting

- Missing models: run `python -m scripts.prepare_models` with intentional network access, then `python -m scripts.verify_models`.
- Readiness is `not_ready`: check local model cache and that the configured Ollama model exists.
- Docker cannot reach Ollama: use `http://host.docker.internal:11434` on Docker Desktop or set an appropriate private network address.
- Search has no results: run `python -m scripts.demo_setup` or rebuild the index with `python -m indexer.cli`.
