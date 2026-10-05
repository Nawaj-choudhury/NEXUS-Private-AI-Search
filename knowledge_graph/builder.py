from collections import defaultdict

from database.models import StoredChunk

from .extractor import extract_concepts
from .models import Graph, Node
from .relations import concept_cooccurrence_edges, document_concept_edges


class GraphBuilder:
    def __init__(self, max_concepts_per_document: int = 30, min_concept_frequency: int = 1) -> None:
        self.max_concepts_per_document = max_concepts_per_document
        self.min_concept_frequency = min_concept_frequency

    def build(self, chunks: list[StoredChunk]) -> Graph:
        concepts_by_chunk: dict[str, list] = {}
        concepts_by_document: dict[tuple[str, str | None, str], dict[str, object]] = defaultdict(dict)
        for chunk in chunks:
            concepts = extract_concepts(chunk.content, chunk.chunk_id, self.max_concepts_per_document, self.min_concept_frequency)
            if chunk.source_type == "private" and chunk.user_id is not None:
                concepts = [type(concept)(f"user:{chunk.user_id}:{concept.concept_id}", concept.label, concept.occurrence_count, concept.chunk_ids) for concept in concepts]
            scope_id = chunk.user_id if chunk.source_type == "private" else "public"
            concepts_by_chunk[f"{scope_id}:{chunk.chunk_id}"] = concepts
            document_key = (chunk.source_type, chunk.user_id, chunk.document_id)
            document_state = concepts_by_document[document_key]
            document_state.setdefault("chunk", chunk)
            by_id = document_state.setdefault("concepts", {})
            for concept in concepts:
                existing = by_id.get(concept.concept_id)
                if existing is None:
                    by_id[concept.concept_id] = concept
                else:
                    by_id[concept.concept_id] = type(concept)(concept.concept_id, concept.label, existing.occurrence_count + concept.occurrence_count, tuple(sorted(set(existing.chunk_ids + concept.chunk_ids))))
        nodes: list[Node] = []
        edges = []
        for (_, _, document_id), state in concepts_by_document.items():
            chunk = state["chunk"]
            source_node_type = "web_source" if chunk.source_type == "public_web" else "document"
            source_node_id = f"web:{document_id}" if source_node_type == "web_source" else f"document:{document_id}"
            if source_node_type == "document" and chunk.user_id is not None:
                source_node_id = f"document:{chunk.user_id}:{document_id}"
            nodes.append(Node(source_node_id, source_node_type, chunk.filename, chunk.source_type, document_id, chunk.url if source_node_type == "web_source" else None, chunk.domain if source_node_type == "web_source" else None, user_id=chunk.user_id))
            concepts = list(state["concepts"].values())
            nodes.extend(Node(concept.concept_id, "concept", concept.label, source_type=chunk.source_type, occurrence_count=concept.occurrence_count, chunk_ids=concept.chunk_ids, user_id=chunk.user_id) for concept in concepts)
            edges.extend(document_concept_edges(source_node_id, concepts))
        edges.extend(concept_cooccurrence_edges(concepts_by_chunk))
        return Graph(tuple({node.node_id: node for node in nodes}.values()), tuple({(edge.source_id, edge.target_id, edge.relation): edge for edge in edges}.values()))