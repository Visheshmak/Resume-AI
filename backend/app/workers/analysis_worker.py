from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.jd.schemas import JobDescriptionExtraction
from app.matching.engine import ResumeJDMatcher
from app.models import Analysis, AnalysisEvidence, AnalysisJob, Resume
from app.resume.schemas import ResumeExtraction


async def process_analysis_job(job_id: str) -> None:
    async with AsyncSessionLocal() as db:
        job = await claim_job(db, job_id)
        if job is None:
            return
        try:
            await set_progress(db, job, 25, "Parsing resume")
            result = await db.execute(select(Analysis).options(selectinload(Analysis.resume).selectinload(Resume.versions), selectinload(Analysis.job_description)).where(Analysis.id == job.analysis_id))
            analysis = result.scalar_one()
            latest = max(analysis.resume.versions, key=lambda version: version.version_number, default=None)
            if latest is None or not latest.structured_data or not analysis.job_description.structured_data:
                raise ValueError("Resume and job description extraction data is unavailable")
            await set_progress(db, job, 55, "Matching skills")
            report = ResumeJDMatcher().match(ResumeExtraction.model_validate(latest.structured_data), JobDescriptionExtraction.model_validate(analysis.job_description.structured_data))
            analysis.score_summary = report.model_dump(mode="json")
            analysis.status = "completed"
            analysis.completed_at = datetime.now(UTC)
            job.status = "completed"
            job.progress = 100
            job.current_step = "Completed"
            job.completed_at = analysis.completed_at
            for match in [*report.matched_skills, *report.partial_matches, *report.missing_skills]:
                for source in [*match.jd_evidence, *match.resume_evidence]:
                    db.add(AnalysisEvidence(analysis_id=analysis.id, kind=match.status, source_id=source.id, excerpt=source.text, confidence=match.confidence))
            await db.commit()
        except Exception as exc:
            await fail_or_retry(db, job, str(exc))


async def claim_job(db: AsyncSession, job_id: str) -> AnalysisJob | None:
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None or job.status not in {"queued", "retrying"}:
        return None
    job.status = "processing"
    job.attempts += 1
    job.started_at = datetime.now(UTC)
    job.current_step = "Starting analysis"
    await db.commit()
    return job


async def set_progress(db: AsyncSession, job: AnalysisJob, progress: int, step: str) -> None:
    job.progress = progress
    job.current_step = step
    await db.commit()


async def fail_or_retry(db: AsyncSession, job: AnalysisJob, message: str) -> None:
    analysis = await db.get(Analysis, job.analysis_id)
    job.error_message = message[:2000]
    if job.attempts < settings.analysis_max_retries:
        job.status = "retrying"
        if analysis:
            analysis.status = "queued"
    else:
        job.status = "permanently_failed"
        if analysis:
            analysis.status = "failed"
            analysis.error_message = job.error_message
    await db.commit()