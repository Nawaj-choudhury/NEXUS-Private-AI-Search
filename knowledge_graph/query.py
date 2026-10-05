from collections import deque

from .models import Graph, GraphResult, Node
from .store import GraphStore


class GraphQuery:
    def __init__(self, store: GraphStore) -> None:
        self.store = store

    def around(self, node_id: str, max_nodes: int = 30, max_depth: int = 1, min_edge_weight: float = 1.0, user_id: str | None = None) -> GraphResult:
        graph = self.store.graph(user_id=user_id)
        nodes = {node.node_id: node for node in graph.nodes}
        if node_id not in nodes:
            return GraphResult(Graph())
        edges = [edge for edge in graph.edges if edge.weight >= min_edge_weight]
        adjacency: dict[str, list[str]] = {}
        for edge in edges:
            adjacency.setdefault(edge.source_id, []).append(edge.target_id)
            adjacency.setdefault(edge.target_id, []).append(edge.source_id)
        selected = {node_id}
        queue = deque([(node_id, 0)])
        while queue and len(selected) < max_nodes:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor in adjacency.get(current, []):
                if neighbor not in selected:
                    selected.add(neighbor)
                    queue.append((neighbor, depth + 1))
                    if len(selected) >= max_nodes:
                        break
        bounded_nodes = tuple(nodes[item] for item in sorted(selected) if item in nodes)
        bounded_edges = tuple(edge for edge in edges if edge.source_id in selected and edge.target_id in selected)
        return GraphResult(Graph(bounded_nodes, bounded_edges), node_id)

    def related(self, node_id: str, limit: int = 10, min_edge_weight: float = 1.0, user_id: str | None = None) -> list[Node]:
        result = self.around(node_id, max_nodes=limit + 1, max_depth=1, min_edge_weight=min_edge_weight, user_id=user_id)
        return [node for node in result.graph.nodes if node.node_id != node_id][:limit]

    def sources(self, concept_id: str, limit: int = 20, user_id: str | None = None) -> list[Node]:
        result = self.around(concept_id, max_nodes=limit + 1, max_depth=1, user_id=user_id)
        return [node for node in result.graph.nodes if node.node_type in {"document", "web_source"}][:limit]

    def concepts_for_document(self, document_id: str, limit: int = 50, user_id: str | None = None) -> list[Node]:
        node_id = f"document:{user_id}:{document_id}" if user_id is not None else f"document:{document_id}"
        result = self.around(node_id, max_nodes=limit + 1, max_depth=1, user_id=user_id)
        return [node for node in result.graph.nodes if node.node_type == "concept"][:limit]