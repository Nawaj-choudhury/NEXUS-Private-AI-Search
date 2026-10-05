from __future__ import annotations

from pathlib import Path

from backend.app.core.config import settings
from database.repository import DocumentRepository
from indexer.pipeline import IndexingPipeline
from knowledge_graph.service import GraphService
from retrieval.embeddings import get_embedding_model
from retrieval.vector_store import VectorStore


def main() -> int:
    print("NEXUS demo setup")
    pipeline = IndexingPipeline(
        Path(settings.private_vault_path),
        DocumentRepository(Path(settings.database_path)),
        settings.chunk_size,
        settings.chunk_overlap,
        VectorStore(Path(settings.vector_store_path)),
        get_embedding_model(settings.embedding_model),
        settings.max_document_size,
    )
    result = pipeline.rebuild()
    chunks = DocumentRepository(Path(settings.database_path)).all_chunks()
    graph_result = GraphService(Path(settings.graph_store_path), settings.graph_max_concepts_per_document, settings.graph_min_concept_frequency).rebuild(chunks)
    print(f"files_discovered={result['files_discovered']}")
    print(f"files_indexed={result['files_indexed']}")
    print(f"chunks_created={result['chunks_created']}")
    print(f"graph_documents={graph_result['documents_processed']}")
    print("Demo setup complete. No document contents were printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
