from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request

from ..auth.dependencies import get_current_user
from ..schemas.research import (
    CitationSchema,
    ClaimGroundingSchema,
    EvidenceSchema,
    GroundingSchema,
    RelatedTopicSchema,
    ResearchRequestSchema,
    ResearchResponseSchema,
    SourceSchema,
)
from ..services.research import research_private_documents
from ai_engine.models import ResearchRequest
from ai_engine.providers.base import ProviderError

router = APIRouter(prefix="/api")


@router.post("/research", response_model=ResearchResponseSchema)
def research(request: ResearchRequestSchema | None = None, http_request: Request = None) -> ResearchResponseSchema:
    if request is None:
        raise HTTPException(status_code=400, detail="Research request body is required")

    current_user = None
    if request.mode != "web" and http_request is not None:
        current_user = get_current_user(http_request)
    try:
        response = research_private_documents(ResearchRequest(request.query, request.mode, request.top_k, request.rerank), user_id=current_user.user_id if current_user else None)
    except (ValueError, ProviderError, RuntimeError) as error:
        raise HTTPException(status_code=503, detail={"code": "LOCAL_AI_UNAVAILABLE", "message": "The local AI provider is currently unavailable."}) from error
    return ResearchResponseSchema(
        query=response.query,
        answer=response.answer.text,
        citations=[CitationSchema(**asdict(citation)) for citation in response.citations],
        evidence=[EvidenceSchema(**asdict(evidence)) for evidence in response.evidence],
        related_topics=[RelatedTopicSchema(**asdict(topic)) for topic in response.related_topics],
        sources=[SourceSchema(**asdict(source)) for source in response.sources],
        evidence_sufficient=response.evidence_sufficient,
        citation_validation_passed=response.answer.citation_validation_passed,
        grounding=GroundingSchema(
            status=response.answer.grounding.status,
            claims_checked=response.answer.grounding.claims_checked,
            claims_supported=response.answer.grounding.claims_supported,
            claims_partially_supported=response.answer.grounding.claims_partially_supported,
            claims_unsupported=response.answer.grounding.claims_unsupported,
            claims=[ClaimGroundingSchema(**asdict(claim)) for claim in response.answer.grounding.claims],
        ),
    )