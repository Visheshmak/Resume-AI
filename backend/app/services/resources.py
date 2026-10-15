from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import JobDescription, Resume, ResumeVersion, User
from app.schemas.resources import JobCreateRequest


async def create_resume(db: AsyncSession, user: User, *, title: str, original_filename: str, file_type: str, size_bytes: int, storage_path: str, extracted_text: str = "", structured_data: dict | None = None) -> Resume:
    resume = Resume(user_id=user.id, title=title, original_filename=original_filename, file_type=file_type, size_bytes=size_bytes, storage_path=storage_path, status="parsed")
    resume.versions.append(ResumeVersion(version_number=1, extracted_text=extracted_text, structured_data=structured_data or {}))
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


async def get_resume_for_user(db: AsyncSession, user: User, resume_id: str) -> Resume:
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id))
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


async def create_job(db: AsyncSession, user: User, request: JobCreateRequest, structured_data: dict | None = None) -> JobDescription:
    job = JobDescription(user_id=user.id, title=request.title.strip(), raw_text=request.raw_text.strip(), structured_data=structured_data or {})
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def get_job_for_user(db: AsyncSession, user: User, job_id: str) -> JobDescription:
    result = await db.execute(select(JobDescription).where(JobDescription.id == job_id, JobDescription.user_id == user.id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")
    return job


async def get_counts(db: AsyncSession, user: User) -> dict[str, int]:
    from app.models import Analysis

    resume_count = await db.scalar(select(func.count()).select_from(Resume).where(Resume.user_id == user.id))
    job_count = await db.scalar(select(func.count()).select_from(JobDescription).where(JobDescription.user_id == user.id))
    analysis_count = await db.scalar(select(func.count()).select_from(Analysis).where(Analysis.user_id == user.id))
    completed_count = await db.scalar(select(func.count()).select_from(Analysis).where(Analysis.user_id == user.id, Analysis.status == "completed"))
    return {"resume_count": resume_count or 0, "job_count": job_count or 0, "analysis_count": analysis_count or 0, "completed_analysis_count": completed_count or 0}
