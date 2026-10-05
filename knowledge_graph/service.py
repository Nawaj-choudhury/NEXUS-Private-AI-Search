from pathlib import Path

from database.models import StoredChunk

from .builder import GraphBuilder
from .models import Graph, GraphResult, Node
from .query import GraphQuery
from .store import GraphStore


class GraphService:
    def __init__(self, database_path: Path, max_concepts_per_document: int = 30, min_concept_frequency: int = 1) -> None:
        self.store = GraphStore(database_path)
        self.builder = GraphBuilder(max_concepts_per_document, min_concept_frequency)
        self.query = GraphQuery(self.store)

    def rebuild(self, chunks: list[StoredChunk], user_id: str | None = None) -> dict[str, int]:
        graph = self.builder.build(chunks)
        self.store.replace_graph(graph)
        return {"documents_processed": len({chunk.document_id for chunk in chunks}), "concepts_created": sum(node.node_type == "concept" for node in graph.nodes), "edges_created": len(graph.edges), "orphan_nodes_removed": 0}

    def graph_around(self, node_id: str, max_nodes: int = 30, max_depth: int = 1, min_edge_weight: float = 1.0, user_id: str | None = None) -> GraphResult:
        return self.query.around(node_id, max_nodes, max_depth, min_edge_weight, user_id=user_id)

    def related(self, concept_id: str, limit: int = 10, user_id: str | None = None) -> list[Node]:
        return self.query.related(concept_id, limit, user_id=user_id)

    def sources(self, concept_id: str, limit: int = 20, user_id: str | None = None) -> list[Node]:
        return self.query.sources(concept_id, limit, user_id=user_id)

    def discovery(self, query: str, limit: int = 8, user_id: str | None = None) -> list[Node]:
        return self.store.find_concepts(query, limit, user_id=user_id)

    def search_graph(self, query: str, max_nodes: int = 30, user_id: str | None = None) -> GraphResult:
        concepts = self.discovery(query, 1, user_id=user_id)
        if not concepts:
            return GraphResult(Graph())
        return self.graph_around(concepts[0].node_id, max_nodes=max_nodes, user_id=user_id)