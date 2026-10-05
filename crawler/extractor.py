from html.parser import HTMLParser
from urllib.parse import urljoin

from .cleaner import clean_text


class _ContentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description: str | None = None
        self.headings: list[str] = []
        self.text: list[str] = []
        self.links: list[str] = []
        self.canonical: str | None = None
        self._ignored = 0
        self._title = False
        self._heading = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag in {"script", "style", "nav", "footer", "header", "aside", "noscript", "svg"}:
            self._ignored += 1
        if tag == "title":
            self._title = True
        if tag in {"h1", "h2", "h3"}:
            self._heading = True
        if tag == "meta" and attributes.get("name", "").lower() == "description":
            self.description = attributes.get("content")
        if tag == "link" and attributes.get("rel", "").lower() == "canonical":
            self.canonical = attributes.get("href")
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav", "footer", "header", "aside", "noscript", "svg"} and self._ignored:
            self._ignored -= 1
        if tag == "title":
            self._title = False
        if tag in {"h1", "h2", "h3"}:
            self._heading = False

    def handle_data(self, data: str) -> None:
        if self._ignored:
            return
        value = data.strip()
        if not value:
            return
        if self._title:
            self.title += f" {value}"
        elif self._heading:
            self.headings.append(value)
            self.text.append(value)
        else:
            self.text.append(value)


def extract_html(html: bytes | str, base_url: str) -> dict[str, object]:
    parser = _ContentParser()
    parser.feed(html.decode("utf-8", errors="replace") if isinstance(html, bytes) else html)
    links = tuple(urljoin(base_url, link) for link in parser.links)
    return {"title": clean_text(parser.title) or base_url, "description": clean_text(parser.description or "") or None, "headings": tuple(parser.headings), "content": clean_text("\n".join(parser.text)), "canonical_url": urljoin(base_url, parser.canonical) if parser.canonical else base_url, "links": links}