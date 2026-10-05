from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


class RobotsPolicy:
    def __init__(self, user_agent: str, timeout: float = 10.0, opener=urlopen) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self.opener = opener
        self._parsers: dict[str, RobotFileParser | None] = {}

    def allowed(self, url: str) -> tuple[bool, str]:
        parts = urlsplit(url)
        origin = urlunsplit((parts.scheme, parts.netloc, "", "", ""))
        if origin not in self._parsers:
            robots_url = f"{origin}/robots.txt"
            parser = RobotFileParser()
            parser.set_url(robots_url)
            try:
                request = Request(robots_url, headers={"User-Agent": self.user_agent})
                with self.opener(request, timeout=self.timeout) as response:
                    parser.parse(response.read(512_000).decode("utf-8", errors="replace").splitlines())
                self._parsers[origin] = parser
            except Exception:
                # Conservative failure policy: inaccessible robots means no fetch.
                self._parsers[origin] = None
        parser = self._parsers[origin]
        if parser is None:
            return False, "robots.txt unavailable"
        return (True, "allowed") if parser.can_fetch(self.user_agent, url) else (False, "disallowed by robots.txt")