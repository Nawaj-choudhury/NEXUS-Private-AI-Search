import unittest
from datetime import datetime, timezone

from crawler.cleaner import clean_text
from crawler.crawler import ControlledCrawler
from crawler.extractor import extract_html
from crawler.fetcher import FetchResponse
from crawler.models import WebPage
from crawler.policy import CrawlPolicy
from crawler.url_utils import normalize_url
from retrieval.hybrid_search import HybridSearch
from retrieval.models import SemanticResult


class FakeRobots:
    def __init__(self, allowed=True):
        self.allowed_value = allowed

    def allowed(self, url):
        return self.allowed_value, "allowed" if self.allowed_value else "disallowed by robots.txt"


class FakeFetcher:
    def __init__(self):
        self.calls = []

    def fetch(self, url):
        self.calls.append(url)
        return FetchResponse(url, "text/html", f"<html><title>{url}</title><main><h1>Useful topic</h1><p>Public evidence for testing.</p><a href=\"{url}/next\">Next</a></main></html>".encode(), None, None)


class Step8Tests(unittest.TestCase):
    def test_url_validation_blocks_local_destinations(self):
        with self.assertRaises(ValueError):
            normalize_url("http://127.0.0.1:8000")
        with self.assertRaises(ValueError):
            normalize_url("file:///private/data")

    def test_extraction_and_cleaning_remove_noise(self):
        extracted = extract_html("<html><title>Title</title><nav>Noise</nav><main><h1>Heading</h1><p>Text   here</p><script>bad()</script></main></html>", "https://example.com")
        self.assertEqual(extracted["title"], "Title")
        self.assertIn("Heading", extracted["content"])
        self.assertNotIn("Noise", extracted["content"])
        self.assertNotIn("bad", extracted["content"])
        self.assertEqual(clean_text("a   b\n\na"), "a b\n\na")

    def test_crawler_is_bounded_and_respects_robots(self):
        fetcher = FakeFetcher()
        result = ControlledCrawler(CrawlPolicy(max_pages=1, max_depth=2, delay_seconds=0), fetcher=fetcher, robots=FakeRobots()).crawl("https://example.com")
        self.assertEqual(len(result.pages), 1)
        self.assertEqual(len(fetcher.calls), 1)

        blocked = ControlledCrawler(CrawlPolicy(delay_seconds=0), fetcher=fetcher, robots=FakeRobots(False)).crawl("https://example.com")
        self.assertEqual(len(blocked.pages), 0)
        self.assertEqual(blocked.skipped[0].reason, "disallowed by robots.txt")

    def test_source_modes_filter_results(self):
        class FakeBM25:
            def search(self, query, limit):
                from search_engine.models import Document, SearchResult
                return [SearchResult(Document("private", "Private", "private evidence", "private.txt", source_type="private"), "private evidence", 1.0), SearchResult(Document("web", "Web", "public evidence", "https://example.com", source_type="public_web", url="https://example.com", domain="example.com"), "public evidence", 0.9)]

        class FakeSemantic:
            def search(self, query, source_type=None):
                return []

        search = HybridSearch(FakeBM25(), FakeSemantic(), top_k=10)
        self.assertEqual(search.search("evidence", source_type="private")[0].source_type, "private")
        self.assertEqual(search.search("evidence", source_type="public_web")[0].source_type, "public_web")


if __name__ == "__main__":
    unittest.main()
