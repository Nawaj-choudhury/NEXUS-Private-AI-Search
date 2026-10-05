import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def page_metadata(url: str, extracted: dict[str, object], content_type: str, fetched_at: datetime | None = None, crawl_depth: int = 0, etag: str | None = None, last_modified: str | None = None) -> dict[str, object]:
    return {"url": url, "canonical_url": str(extracted["canonical_url"]), "domain": urlparse(url).netloc.lower(), "title": str(extracted["title"]), "content_hash": content_hash(str(extracted["content"])), "fetched_at": fetched_at or datetime.now(timezone.utc), "published_at": None, "content_type": content_type, "crawl_depth": crawl_depth, "etag": etag, "last_modified": last_modified, "source_type": "public_web"}