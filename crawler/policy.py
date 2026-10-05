from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CrawlPolicy:
    max_pages: int = 10
    max_depth: int = 1
    timeout: float = 10.0
    delay_seconds: float = 0.5
    user_agent: str = "NEXUS-Private-AI-Search/1.0"
    max_response_size: int = 2_000_000
    allow_localhost: bool = False
    max_redirects: int = 5
    max_retries: int = 1
