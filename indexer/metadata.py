from datetime import datetime, timezone
from pathlib import Path
import hashlib

from .models import DocumentMetadata


def metadata_for_file(path: Path, vault_root: Path, user_id: str | None = None) -> DocumentMetadata:
    stat = path.stat()
    relative_path = path.relative_to(vault_root).as_posix()
    source_path = f"users/{user_id}/{relative_path}" if user_id is not None else relative_path
    document_id = hashlib.sha256(source_path.encode("utf-8")).hexdigest()[:24]
    return DocumentMetadata(
        document_id=document_id,
        filename=path.name,
        file_type=path.suffix.lower().lstrip("."),
        source_path=source_path,
        file_size=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
        updated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
    )