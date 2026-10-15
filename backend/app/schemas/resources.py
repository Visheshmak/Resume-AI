from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_filename: str
    file_type: str
    size_bytes: int
    status: str
    created_at: datetime


class ResumeDetailResponse(ResumeResponse):
    extraction: dict[str, Any] | None = None
    extracted_text: str | None = None


class JobCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    raw_text: str = Field(min_length=20, max_length=100_000)


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    raw_text: str
    structured_data: dict[str, Any]
    created_at: datetime


class AnalysisCreateRequest(BaseModel):
    resume_id: str
    job_description_id: str


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resume_id: str
    job_description_id: str
    status: str
    score_summary: dict[str, Any]
    created_at: datetime
    completed_at: datetime | None
    error_message: str | None
    job_id: str | None = None


class AnalysisJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    analysis_id: str
    status: str
    progress: int
    current_step: str
    attempts: int
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: str
    source_id: str
    excerpt: str | None
    confidence: float | None


class DashboardOverview(BaseModel):
    resume_count: int
    job_count: int
    analysis_count: int
    completed_analysis_count: int
