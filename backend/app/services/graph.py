from backend.app.core.config import settings
from database.repository import DocumentRepository
from knowledge_graph.service import GraphService


def get_graph_service() -> GraphService:
    return GraphService(
        settings.graph_store_path,
        settings.graph_max_concepts_per_document,
        settings.graph_min_concept_frequency,
    )


def rebuild_graph() -> dict[str, int]:
    chunks = DocumentRepository(settings.database_path).all_chunks()
    return get_graph_service().rebuild(chunks)