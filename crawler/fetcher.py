from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .policy import CrawlPolicy
from .url_utils import normalize_url


@dataclass(frozen=True, slots=True)
class FetchResponse:
    url: str
    content_type: str
    body: bytes
    etag: str | None
    last_modified: str | None


class WebFetcher:
    def __init__(self, policy: CrawlPolicy, opener=None) -> None:
        self.policy = policy
        policy_for_redirects = policy

        class SafeRedirectHandler(HTTPRedirectHandler):
            max_redirections = policy_for_redirects.max_redirects

            def redirect_request(self, req, fp, code, msg, headers, newurl):
                safe_url = normalize_url(newurl, policy_for_redirects.allow_localhost)
                return super().redirect_request(req, fp, code, msg, headers, safe_url)

        redirect_handler = SafeRedirectHandler()
        self.opener = opener or build_opener(redirect_handler)

    def fetch(self, url: str) -> FetchResponse:
        request = Request(url, headers={"User-Agent": self.policy.user_agent, "Accept": "text/html,application/xhtml+xml"})
        last_error: Exception | None = None
        for _ in range(self.policy.max_retries + 1):
            try:
                with self.opener.open(request, timeout=self.policy.timeout) as response:
                    content_type = response.headers.get_content_type()
                    if content_type not in {"text/html", "application/xhtml+xml"}:
                        raise ValueError(f"Unsupported content type: {content_type}")
                    length = int(response.headers.get("Content-Length", "0") or 0)
                    if length > self.policy.max_response_size:
                        raise ValueError("Response exceeds configured size limit")
                    body = response.read(self.policy.max_response_size + 1)
                    if len(body) > self.policy.max_response_size:
                        raise ValueError("Response exceeds configured size limit")
                    return FetchResponse(response.geturl(), content_type, body, response.headers.get("ETag"), response.headers.get("Last-Modified"))
            except (HTTPError, URLError, TimeoutError) as error:
                last_error = error
        raise RuntimeError(f"Web fetch failed: {last_error}") from last_error