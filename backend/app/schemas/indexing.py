from pydantic import BaseModel


class IndexingResponse(BaseModel):
    files_discovered: int
    files_indexed: int
    files_failed: int
    chunks_created: int
    files_removed: int