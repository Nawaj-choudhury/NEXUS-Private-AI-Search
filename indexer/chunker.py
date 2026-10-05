from .models import DocumentChunk


def chunk_document(
    document_id: str,
    filename: str,
    content: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[DocumentChunk]:
    if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and chunk_overlap must be smaller than chunk_size")

    chunks: list[DocumentChunk] = []
    start = 0
    position = 0
    while start < len(content):
        end = min(start + chunk_size, len(content))
        chunk_content = content[start:end].strip()
        if chunk_content:
            chunks.append(DocumentChunk(document_id, f"{document_id}:{position}", filename, chunk_content, position))
            position += 1
        if end == len(content):
            break
        start = end - chunk_overlap
    return chunks