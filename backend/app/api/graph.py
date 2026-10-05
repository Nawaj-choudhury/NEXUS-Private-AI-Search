from fastapi import APIRouter, HTTPException, Query, Request

from ..auth.dependencies import get_current_user
from ..schemas.graph import GraphEdgeSchema, GraphNodeSchema, GraphRebuildResponseSchema, GraphResponseSchema, GraphSourceSchema, RelatedConceptSchema
from ..services.graph import get_graph_service, rebuild_graph

router = APIRouter(prefix="/api/graph")


def _response(result) -> GraphResponseSchema:
    return GraphResponseSchema(
        nodes=[GraphNodeSchema(**node.__dict__) if hasattr(node, "__dict__") else GraphNodeSchema(node_id=node.node_id, node_type=node.node_type, label=node.label, source_type=node.source_type, document_id=node.document_id, url=node.url, domain=node.domain, occurrence_count=node.occurrence_count, chunk_ids=node.chunk_ids) for node in result.graph.nodes],
        edges=[GraphEdgeSchema(source_id=edge.source_id, target_id=edge.target_id, relation=edge.relation, weight=edge.weight, evidence_count=edge.evidence_count, method=edge.method) for edge in result.graph.edges],
        center_id=result.center_id,
        explanation=result.explanation,
    )


@router.get("/concept/{concept_id:path}", response_model=GraphResponseSchema)
def concept_graph(http_request: Request, concept_id: str) -> GraphResponseSchema:
    current_user = get_current_user(http_request)
    if len(concept_id) > 300:
        raise HTTPException(status_code=422, detail={"code": "GRAPH_LIMIT", "message": "Concept identifier exceeds the configured limit."})
    service = get_graph_service()
    return _response(service.graph_around(concept_id, user_id=current_user.user_id))


@router.get("/related/{concept_id:path}", response_model=list[RelatedConceptSchema])
def related_concepts(http_request: Request, concept_id: str, limit: int = Query(10, ge=1, le=50)) -> list[RelatedConceptSchema]:
    current_user = get_current_user(http_request)
    if len(concept_id) > 300:
        raise HTTPException(status_code=422, detail={"code": "GRAPH_LIMIT", "message": "Concept identifier exceeds the configured limit."})
    return [RelatedConceptSchema(node_id=node.node_id, label=node.label, occurrence_count=node.occurrence_count) for node in get_graph_service().related(concept_id, limit, user_id=current_user.user_id)]


@router.get("/sources/{concept_id:path}", response_model=list[GraphSourceSchema])
def concept_sources(http_request: Request, concept_id: str, limit: int = Query(20, ge=1, le=100)) -> list[GraphSourceSchema]:
    current_user = get_current_user(http_request)
    if len(concept_id) > 300:
        raise HTTPException(status_code=422, detail={"code": "GRAPH_LIMIT", "message": "Concept identifier exceeds the configured limit."})
    return [GraphSourceSchema(node_id=node.node_id, label=node.label, source_type=node.source_type or "private", document_id=node.document_id or "", url=node.url if node.source_type == "public_web" else None, domain=node.domain if node.source_type == "public_web" else None) for node in get_graph_service().sources(concept_id, limit, user_id=current_user.user_id)]


@router.get("/search", response_model=GraphResponseSchema)
def search_graph(http_request: Request, q: str = Query(..., min_length=1, max_length=300)) -> GraphResponseSchema:
    current_user = get_current_user(http_request)
    return _response(get_graph_service().search_graph(q, user_id=current_user.user_id))


@router.post("/rebuild", response_model=GraphRebuildResponseSchema)
def rebuild(http_request: Request) -> GraphRebuildResponseSchema:
    get_current_user(http_request)
    return GraphRebuildResponseSchema(**rebuild_graph())