from pydantic import BaseModel, Field


class CrawlRequestSchema(BaseModel):
    url: str = Field(min_length=1, max_length=2_048)
    max_pages: int | None = Field(default=None, ge=1, le=100)
    max_depth: int | None = Field(default=None, ge=0, le=5)


class CrawlResponseSchema(BaseModel):
    pages_discovered: int
    pages_fetched: int
    pages_skipped: int
    pages_failed: int
    documents_indexed: int