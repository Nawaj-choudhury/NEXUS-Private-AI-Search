import re


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    cleaned: list[str] = []
    for line in lines:
        if line and (not cleaned or line != cleaned[-1]):
            cleaned.append(line)
    return "\n\n".join(cleaned)