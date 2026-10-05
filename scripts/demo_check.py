from __future__ import annotations

from pathlib import Path

from backend.app.api.search import search
from backend.app.api.routes import readiness_check
from backend.app.core.config import settings
from backend.app.schemas.research import ResearchRequestSchema
from backend.app.api.research import research
from database.repository import DocumentRepository
from backend.app.services.graph import get_graph_service


def main() -> int:
    repository = DocumentRepository(Path(settings.database_path))
    chunks = repository.all_chunks()
    print("NEXUS demo check")
    print(f"indexed_chunks={len(chunks)}")
    if not chunks:
        print("ERROR: run python -m scripts.demo_setup first")
        return 1
    result = search("machine learning", mode="hybrid", rerank=True)
    print(f"hybrid_results={result.total_results}")
    print(f"reranker_status={result.retrieval.reranker.status}")
    graph = get_graph_service().search_graph("machine")
    print(f"graph_nodes={len(graph.graph.nodes)} graph_edges={len(graph.graph.edges)}")
    readiness = readiness_check()
    print(f"readiness={readiness['status']}")
    if readiness["status"] == "ready":
        response = research(ResearchRequestSchema(query="machine learning", mode="private", top_k=2, rerank=True))
        print(f"research_citations={len(response.citations)}")
        print(f"citation_validation={response.citation_validation_passed}")
    else:
        print("research=skipped_local_services_not_ready")
    print("Demo check complete. Document contents were not printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
