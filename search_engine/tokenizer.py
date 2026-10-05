import re

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Normalize text into deterministic lowercase word and number tokens."""
    return TOKEN_PATTERN.findall(text.lower())