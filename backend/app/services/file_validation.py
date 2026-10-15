import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.services.storage import ObjectStorageService


@dataclass(frozen=True)
class ValidatedUpload:
    content: bytes
    extension: str
    safe_path: Path
    original_filename: str


async def validate_and_stage_upload(upload: UploadFile) -> ValidatedUpload:
    original_filename = Path(upload.filename or "").name
    extension = Path(original_filename).suffix.lower()
    if extension not in {".pdf", ".docx"}:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only PDF and DOCX files are supported")

    content = await upload.read(settings.max_upload_size_bytes + 1)
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Uploaded file exceeds the size limit")

    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is not a valid PDF")
    if extension == ".docx" and not _is_valid_docx(content):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is not a valid DOCX document")

        safe_path = ObjectStorageService().upload(content, extension.removeprefix("."))
    return ValidatedUpload(content, extension.removeprefix("."), safe_path, original_filename)


def _is_valid_docx(content: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            if archive.testzip() is not None or not {"[Content_Types].xml", "word/document.xml"}.issubset(archive.namelist()):
                return False
            total_uncompressed = sum(info.file_size for info in archive.infolist())
            if total_uncompressed > settings.max_upload_size_bytes * 20:
                return False
            if any(info.filename.startswith(("/", "\\")) or ".." in Path(info.filename).parts for info in archive.infolist()):
                return False
            from docx import Document

            Document(io.BytesIO(content))
            return True
    except (AttributeError, KeyError, OSError, ValueError, zipfile.BadZipFile):
        return False
