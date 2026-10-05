from pathlib import Path

from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}
MAX_DOCUMENT_CHARS = 20_000_000


def load_text_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if len(text) > MAX_DOCUMENT_CHARS:
        raise ValueError("Document exceeds the configured size limit")
    return text


def load_pdf_file(path: Path) -> str:
    reader = PdfReader(str(path))
    if len(reader.pages) > 1_000:
        raise ValueError("PDF exceeds the configured page limit")
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if len(text) > MAX_DOCUMENT_CHARS:
        raise ValueError("Document exceeds the configured size limit")
    return text


def load_document(path: Path) -> str:
    extension = path.suffix.lower()
    if extension in {".txt", ".md"}:
        return load_text_file(path)
    if extension == ".pdf":
        return load_pdf_file(path)
    raise ValueError(f"Unsupported document type: {extension}")