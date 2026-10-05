from fastapi import APIRouter, Request

from ..auth.dependencies import get_current_user
from ..schemas.indexing import IndexingResponse
from ..services.indexing import rebuild_private_index

router = APIRouter(prefix="/api/index")


@router.post("/rebuild", response_model=IndexingResponse)
def rebuild_index(http_request: Request = None) -> IndexingResponse:
    current_user = get_current_user(http_request) if http_request is not None else None
    return IndexingResponse(**rebuild_private_index(user_id=current_user.user_id if current_user is not None else None))