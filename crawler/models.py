from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class WebPage:
    url: str
    canonical_url: str
    domain: str
    title: str
    content: str
    description: str | None
    headings: tuple[str, ...]
    content_type: str
    content_hash: str
    fetched_at: datetime
    published_at: datetime | None = None
    crawl_depth: int = 0
    etag: str | None = None
    last_modified: str | None = None
    source_type: str = "public_web"
    links: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class CrawlFailure:
    url: str
    reason: str
    depth: int


@dataclass(frozen=True, slots=True)
class CrawlResult:
    pages: tuple[WebPage, ...]
    skipped: tuple[CrawlFailure, ...]
    failed: tuple[CrawlFailure, ...]
    discovered: int
