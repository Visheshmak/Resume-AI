from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.core.config import settings


class ObjectStorageService:
    """Storage boundary; replace the local adapter with S3/Azure/Supabase in production."""

    def __init__(self, root: str | None = None):
        self.root = Path(root or settings.upload_dir).resolve()

    def upload(self, content: bytes, extension: str) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{uuid4()}.{extension}"
        path.write_bytes(content)
        return path

    def download(self, storage_key: str) -> bytes:
        return Path(storage_key).read_bytes()

    def delete(self, storage_key: str) -> None:
        Path(storage_key).unlink(missing_ok=True)

    def generate_signed_url(self, storage_key: str, expires_seconds: int = 900) -> str:
        raise NotImplementedError("Signed URLs require a configured object-storage adapter")
