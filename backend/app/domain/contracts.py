from enum import StrEnum

from pydantic import BaseModel, Field


class EvidenceKind(StrEnum):
    RESUME_FACT = "resume_fact"
    JOB_REQUIREMENT = "job_requirement"
    MATCHED = "matched"
    MISSING = "missing"
    GENERATED_RECOMMENDATION = "generated_recommendation"


class EvidenceReference(BaseModel):
    kind: EvidenceKind
    source_id: str = Field(description="Stable identifier for the source fact or requirement")
    excerpt: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class ScoreComponent(BaseModel):
    key: str
    label: str
    value: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    evidence: list[EvidenceReference] = []


class AnalysisStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
