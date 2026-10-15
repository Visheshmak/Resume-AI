from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.jd.engine import JobDescriptionIntelligenceEngine
from app.models import JobDescription, User
from app.schemas.resources import JobCreateRequest, JobResponse
from app.services.resources import create_job, get_job_for_user

router = APIRouter()


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED, summary="Create a job description")
async def create_job_description(request: JobCreateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> JobDescription:
    extraction = JobDescriptionIntelligenceEngine().parse(request.raw_text, request.title)
    return await create_job(db, user, request, extraction.as_json())


@router.get("", response_model=list[JobResponse], summary="List the current user's job descriptions")
async def list_jobs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[JobDescription]:
    result = await db.execute(select(JobDescription).where(JobDescription.user_id == user.id).order_by(JobDescription.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{job_id}", response_model=JobResponse, summary="Get a job description")
async def get_job(job_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> JobDescription:
    return await get_job_for_user(db, user, job_id)
