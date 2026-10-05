from pathlib import Path

from fastapi import APIRouter

from backend.app.core.config import settings
from model_cache import get_model_status
from ai_engine.providers.ollama import OllamaProvider

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, object]:
    database_ok = Path(settings.database_path).parent.exists()
    graph_ok = Path(settings.graph_store_path).parent.exists()
    return {
        "status": "ok" if database_ok and graph_ok else "degraded",
        "components": {"api": "ok", "database": "ok" if database_ok else "degraded", "graph_store": "ok" if graph_ok else "degraded"},
    }


@router.get("/readiness")
def readiness_check() -> dict[str, object]:
    embedding = get_model_status(settings.embedding_model, "embedding")
    reranker = get_model_status(settings.reranker_model, "reranker")
    ollama = OllamaProvider(settings.ollama_base_url, settings.ollama_model).health_check() if settings.local_ai_enabled else False
    components = {
        "api": "ok",
        "embedding_model": "ready" if embedding.state == "READY_LOCAL" else "not_ready",
        "reranker": "ready" if reranker.state == "READY_LOCAL" else "not_ready",
        "ollama": "available" if ollama else "unavailable",
    }
    ready = all(value in {"ok", "ready", "available"} for value in components.values())
    return {"status": "ready" if ready else "not_ready", "components": components}