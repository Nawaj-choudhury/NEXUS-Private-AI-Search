import time
from collections import deque
from datetime import datetime, timezone

from .extractor import extract_html
from .fetcher import WebFetcher
from .metadata import page_metadata
from .models import CrawlFailure, CrawlResult, WebPage
from .policy import CrawlPolicy
from .robots import RobotsPolicy
from .url_utils import normalize_url, resolve_link


class ControlledCrawler:
    def __init__(self, policy: CrawlPolicy | None = None, fetcher: WebFetcher | None = None, robots: RobotsPolicy | None = None) -> None:
        self.policy = policy or CrawlPolicy()
        self.fetcher = fetcher or WebFetcher(self.policy)
        self.robots = robots or RobotsPolicy(self.policy.user_agent, self.policy.timeout)

    def crawl(self, start_url: str) -> CrawlResult:
        start = normalize_url(start_url, self.policy.allow_localhost)
        queue = deque([(start, 0)])
        visited: set[str] = set()
        pages: list[WebPage] = []
        skipped: list[CrawlFailure] = []
        failed: list[CrawlFailure] = []
        while queue and len(pages) < self.policy.max_pages:
            url, depth = queue.popleft()
            if url in visited:
                continue
            visited.add(url)
            allowed, reason = self.robots.allowed(url)
            if not allowed:
                skipped.append(CrawlFailure(url, reason, depth))
                continue
            try:
                response = self.fetcher.fetch(url)
                extracted = extract_html(response.body, response.url)
                content = str(extracted["content"])
                if not content:
                    failed.append(CrawlFailure(url, "empty extracted content", depth))
                    continue
                metadata = page_metadata(response.url, extracted, response.content_type, datetime.now(timezone.utc), depth, response.etag, response.last_modified)
                pages.append(WebPage(**metadata, description=extracted["description"], headings=extracted["headings"], content=content, links=tuple(extracted["links"])))
                if depth < self.policy.max_depth:
                    for link in extracted["links"]:
                        normalized = resolve_link(response.url, str(link), self.policy.allow_localhost)
                        if normalized and normalized not in visited:
                            queue.append((normalized, depth + 1))
            except (RuntimeError, ValueError) as error:
                failed.append(CrawlFailure(url, str(error), depth))
            if queue and self.policy.delay_seconds > 0:
                time.sleep(self.policy.delay_seconds)
        return CrawlResult(tuple(pages), tuple(skipped), tuple(failed), len(visited) + len(queue))