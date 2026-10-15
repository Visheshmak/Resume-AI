from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user, get_db
from app.models import Resume, User
from app.resume.engine import ResumeIntelligenceEngine
from app.schemas.common import MessageResponse
from app.schemas.resources import ResumeDetailResponse, ResumeResponse
from app.services.file_validation import validate_and_stage_upload
from app.services.resources import create_resume, get_resume_for_user

router = APIRouter()


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED, summary="Upload a PDF or DOCX resume")
async def upload_resume(
    file: UploadFile = File(..., description="PDF or DOCX resume, up to the configured size limit"),
    title: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Resume:
    staged = await validate_and_stage_upload(file)
    try:
        extraction, extracted_text = ResumeIntelligenceEngine().parse_bytes(staged.content, staged.extension)
    except (OSError, ValueError, RuntimeError) as exc:
        staged.safe_path.unlink(missing_ok=True)
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="The resume could not be parsed") from exc
    return await create_resume(
        db,
        user,
        title=title.strip() if title else staged.original_filename,
        original_filename=staged.original_filename,
        file_type=staged.extension,
        size_bytes=len(staged.content),
        storage_path=str(staged.safe_path),
        extracted_text=extracted_text,
        structured_data=extraction.as_json(),
    )


@router.get("", response_model=list[ResumeResponse], summary="List the current user's resumes")
async def list_resumes(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[Resume]:
    result = await db.execute(select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{resume_id}", response_model=ResumeDetailResponse, summary="Get a resume with structured extraction")
async def get_resume(resume_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Resume).options(selectinload(Resume.versions)).where(Resume.id == resume_id, Resume.user_id == user.id))
    resume = result.scalar_one_or_none()
    if resume is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Resume not found")
    latest = max(resume.versions, key=lambda version: version.version_number, default=None)
    return {
        "id": resume.id,
        "title": resume.title,
        "original_filename": resume.original_filename,
        "file_type": resume.file_type,
        "size_bytes": resume.size_bytes,
        "status": resume.status,
        "created_at": resume.created_at,
        "extraction": latest.structured_data if latest else None,
        "extracted_text": latest.extracted_text if latest else None,
    }


@router.delete("/{resume_id}", response_model=MessageResponse, summary="Delete a resume")
async def delete_resume(resume_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> MessageResponse:
    resume = await get_resume_for_user(db, user, resume_id)
    storage_path = Path(resume.storage_path)
    if storage_path.exists():
        storage_path.unlink()
    await db.delete(resume)
    await db.commit()
    return MessageResponse(message="Resume deleted")
