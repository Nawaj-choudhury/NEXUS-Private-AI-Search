from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Node:
    node_id: str
    node_type: str
    label: str
    source_type: str | None = None
    document_id: str | None = None
    url: str | None = None
    domain: str | None = None
    occurrence_count: int = 0
    chunk_ids: tuple[str, ...] = ()
    user_id: str | None = None


@dataclass(frozen=True, slots=True)
class Edge:
    source_id: str
    target_id: str
    relation: str
    weight: float
    evidence_count: int
    method: str


@dataclass(frozen=True, slots=True)
class Graph:
    nodes: tuple[Node, ...] = ()
    edges: tuple[Edge, ...] = ()


@dataclass(frozen=True, slots=True)
class GraphResult:
    graph: Graph
    center_id: str | None = None
    explanation: str | None = None


@dataclass(frozen=True, slots=True)
class Concept:
    concept_id: str
    label: str
    occurrence_count: int
    chunk_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class SourceReference:
    node_id: str
    title: str
    source_type: str
    document_id: str
    url: str | None = None
    domain: str | None = None