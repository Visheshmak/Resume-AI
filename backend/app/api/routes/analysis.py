import hashlib

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai import AIAnalysisService, build_provider
from app.ai.context import AIContext
from app.ai.errors import AIServiceError
from app.ai.tasks import generate_interview_questions
from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.jd.schemas import JobDescriptionExtraction, JobFitReport
from app.models import Analysis, AnalysisEvidence, AnalysisJob, Resume, User
from app.resume.schemas import ResumeExtraction
from app.schemas.resources import AnalysisCreateRequest, AnalysisJobResponse, AnalysisResponse, EvidenceResponse
from app.services.job_queue import enqueue_analysis
from app.services.resources import get_job_for_user
from app.workers.analysis_worker import process_analysis_job

router = APIRouter()


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED, summary="Queue an evidence-based analysis")
async def create_analysis(request: AnalysisCreateRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    resume_result = await db.execute(select(Resume).options(selectinload(Resume.versions)).where(Resume.id == request.resume_id, Resume.user_id == user.id))
    resume = resume_result.scalar_one_or_none()
    job = await get_job_for_user(db, user, request.job_description_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    latest = max(resume.versions, key=lambda version: version.version_number, default=None)
    if latest is None or not latest.structured_data or not job.structured_data:
        raise HTTPException(status_code=422, detail="Resume and job description must have structured extraction data")
    analysis_key = hashlib.sha256(f"{latest.id}:{request.job_description_id}:{settings.analysis_version}".encode()).hexdigest()
    existing_result = await db.execute(select(AnalysisJob).where(AnalysisJob.user_id == user.id, AnalysisJob.idempotency_key == analysis_key))
    existing_job = existing_result.scalar_one_or_none()
    if existing_job:
        existing_analysis = await db.get(Analysis, existing_job.analysis_id)
        if existing_analysis is None:
            raise HTTPException(status_code=409, detail="Analysis job is inconsistent")
        return _analysis_payload(existing_analysis, existing_job)

    analysis = Analysis(user_id=user.id, resume_id=request.resume_id, job_description_id=request.job_description_id, status="queued", score_summary={})
    db.add(analysis)
    await db.flush()
    analysis_job = AnalysisJob(user_id=user.id, analysis_id=analysis.id, idempotency_key=analysis_key)
    db.add(analysis_job)
    await db.commit()
    await db.refresh(analysis)
    await db.refresh(analysis_job)
    background_tasks.add_task(enqueue_analysis if settings.redis_url else process_analysis_job, analysis_job.id)
    return _analysis_payload(analysis, analysis_job)


@router.get("/{analysis_id}", response_model=AnalysisResponse, summary="Get analysis status and stored results")
async def get_analysis(analysis_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Analysis).options(selectinload(Analysis.job)).where(Analysis.id == analysis_id, Analysis.user_id == user.id))
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _analysis_payload(analysis, analysis.job)


@router.get("/jobs/{job_id}", response_model=AnalysisJobResponse, summary="Get asynchronous analysis job status")
async def get_analysis_job(job_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> AnalysisJob:
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id, AnalysisJob.user_id == user.id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return _job_payload(job)


@router.post("/jobs/{job_id}/retry", response_model=AnalysisJobResponse, summary="Retry a failed analysis job")
async def retry_analysis_job(job_id: str, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id, AnalysisJob.user_id == user.id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    if job.status not in {"failed", "permanently_failed"}:
        raise HTTPException(status_code=409, detail="Only failed jobs can be retried")
    job.status = "retrying"
    job.error_message = None
    await db.commit()
    background_tasks.add_task(enqueue_analysis if settings.redis_url else process_analysis_job, job.id)
    return _job_payload(job)


def _analysis_payload(analysis: Analysis, job: AnalysisJob) -> dict:
    return {
        "id": analysis.id,
        "resume_id": analysis.resume_id,
        "job_description_id": analysis.job_description_id,
        "status": analysis.status,
        "score_summary": analysis.score_summary,
        "created_at": analysis.created_at,
        "completed_at": analysis.completed_at,
        "error_message": analysis.error_message,
        "job_id": job.id if job else None,
    }


def _job_payload(job: AnalysisJob) -> dict:
    return {
        "job_id": job.id,
        "analysis_id": job.analysis_id,
        "status": job.status,
        "progress": job.progress,
        "current_step": job.current_step,
        "attempts": job.attempts,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
    }


@router.get("/{analysis_id}/evidence", response_model=list[EvidenceResponse], summary="Get analysis evidence")
async def get_analysis_evidence(analysis_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[AnalysisEvidence]:
    result = await db.execute(select(AnalysisEvidence).join(Analysis).where(AnalysisEvidence.analysis_id == analysis_id, Analysis.user_id == user.id).order_by(AnalysisEvidence.id))
    return list(result.scalars().all())


@router.post("/{analysis_id}/interview-questions", summary="Generate grounded interview questions")
async def interview_questions(analysis_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Analysis).options(selectinload(Analysis.resume), selectinload(Analysis.job_description)).where(Analysis.id == analysis_id, Analysis.user_id == user.id))
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    versions_result = await db.execute(select(Resume).options(selectinload(Resume.versions)).where(Resume.id == analysis.resume_id))
    resume = versions_result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code=422, detail="Resume source is unavailable")
    latest = max(resume.versions, key=lambda version: version.version_number, default=None)
    if latest is None:
        raise HTTPException(status_code=422, detail="Resume extraction is unavailable")
    try:
        context = AIContext(resume=ResumeExtraction.model_validate(latest.structured_data), job_description=JobDescriptionExtraction.model_validate(analysis.job_description.structured_data), matching_report=JobFitReport.model_validate(analysis.score_summary))
        response = await generate_interview_questions(AIAnalysisService(build_provider()), context)
        return response.model_dump(mode="json")
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail="Interview generation is currently unavailable") from exc
