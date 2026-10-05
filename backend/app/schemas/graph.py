from pydantic import BaseModel, Field


class GraphNodeSchema(BaseModel):
    node_id: str
    node_type: str
    label: str
    source_type: str | None = None
    document_id: str | None = None
    url: str | None = None
    domain: str | None = None
    occurrence_count: int = 0
    chunk_ids: tuple[str, ...] = ()


class GraphEdgeSchema(BaseModel):
    source_id: str
    target_id: str
    relation: str
    weight: float
    evidence_count: int
    method: str


class GraphResponseSchema(BaseModel):
    nodes: list[GraphNodeSchema]
    edges: list[GraphEdgeSchema]
    center_id: str | None = None
    explanation: str | None = None


class GraphRebuildResponseSchema(BaseModel):
    documents_processed: int
    concepts_created: int
    edges_created: int
    orphan_nodes_removed: int


class RelatedConceptSchema(BaseModel):
    node_id: str
    label: str
    occurrence_count: int


class GraphSourceSchema(BaseModel):
    node_id: str
    label: str
    source_type: str
    document_id: str
    url: str | None = None
    domain: str | None = None