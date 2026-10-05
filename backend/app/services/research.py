from backend.app.api.search import get_hybrid_search
from backend.app.core.config import settings
from ai_engine.models import ResearchRequest, ResearchResponse
from ai_engine.providers.ollama import OllamaProvider
from ai_engine.researcher import Researcher


def research_private_documents(request: ResearchRequest, user_id: str | None = None) -> ResearchResponse:
    if not settings.local_ai_enabled:
        raise RuntimeError("Local AI research is disabled by configuration")
    source_type = {"private": "private", "web": "public_web"}.get(request.mode)
    retrieval_mode = "hybrid" if request.mode in {"private", "web", "all"} else request.mode
    retriever = get_hybrid_search(source_type, user_id=user_id)
    provider = OllamaProvider(settings.ollama_base_url, settings.ollama_model, settings.research_temperature)
    researcher = Researcher(
        retriever=lambda query, mode, top_k: retriever.search(query, retrieval_mode, rerank=request.rerank if hasattr(request, "rerank") else settings.reranker_enabled, source_type=source_type, user_id=user_id)[:top_k],
        provider=provider,
        max_context_chars=settings.max_context_chars,
    )
    return researcher.research(request)