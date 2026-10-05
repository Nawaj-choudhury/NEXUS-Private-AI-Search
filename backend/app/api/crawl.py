from fastapi import APIRouter, HTTPException

from crawler.crawler import ControlledCrawler
from crawler.indexer import PublicWebIndexer
from crawler.policy import CrawlPolicy
from database.repository import DocumentRepository
from retrieval.embeddings import get_embedding_model
from retrieval.vector_store import VectorStore
from ..core.config import settings
from ..schemas.crawl import CrawlRequestSchema, CrawlResponseSchema

router = APIRouter(prefix="/api")


@router.post("/crawl", response_model=CrawlResponseSchema)
def crawl(request: CrawlRequestSchema) -> CrawlResponseSchema:
    policy = CrawlPolicy(
        max_pages=request.max_pages or settings.crawler_max_pages,
        max_depth=request.max_depth if request.max_depth is not None else settings.crawler_max_depth,
        timeout=settings.crawler_timeout,
        delay_seconds=settings.crawler_delay_seconds,
        user_agent=settings.crawler_user_agent,
        max_response_size=settings.crawler_max_response_size,
        allow_localhost=settings.crawler_allow_localhost,
    )
    try:
        result = ControlledCrawler(policy).crawl(request.url)
        indexing = PublicWebIndexer(
            DocumentRepository(settings.database_path),
            VectorStore(settings.vector_store_path),
            get_embedding_model(settings.embedding_model),
            settings.chunk_size,
            settings.chunk_overlap,
        ).index(result.pages)
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=400, detail={"code": "CRAWL_REJECTED", "message": "The requested crawl could not be completed."}) from error
    return CrawlResponseSchema(
        pages_discovered=result.discovered,
        pages_fetched=len(result.pages),
        pages_skipped=len(result.skipped),
        pages_failed=len(result.failed),
        documents_indexed=indexing["pages_indexed"],
    )