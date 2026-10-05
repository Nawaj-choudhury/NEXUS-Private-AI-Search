from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    document_id: str
    filename: str
    file_type: str
    source_path: str
    file_size: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Document:
    document_id: str
    filename: str
    file_type: str
    source_path: str
    content: str
    metadata: DocumentMetadata


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    document_id: str
    chunk_id: str
    filename: str
    content: str
    position: int