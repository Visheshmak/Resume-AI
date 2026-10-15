from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_type: str = "resume"
    page_number: int | None = Field(default=None, ge=1)
    line_number: int | None = Field(default=None, ge=1)
    section: str | None = None
    text: str
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)


class ExtractedValue(BaseModel):
    value: str
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0, le=1)
    uncertain: bool = False


class ContactInfo(BaseModel):
    email: ExtractedValue | None = None
    phone: ExtractedValue | None = None
    location: ExtractedValue | None = None
    linkedin: ExtractedValue | None = None
    github: ExtractedValue | None = None
    portfolio: ExtractedValue | None = None


class CandidateInfo(BaseModel):
    name: ExtractedValue | None = None


class SectionInfo(BaseModel):
    name: str
    heading: str
    start_line: int
    end_line: int
    evidence: list[Evidence] = Field(default_factory=list)


class EducationEntry(BaseModel):
    institution: str | None = None
    degree: str | None = None
    dates: str | None = None
    details: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    uncertain: bool = False


class ExperienceEntry(BaseModel):
    company: str | None = None
    role: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    uncertain_fields: list[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    problem: str | None = None
    solution: str | None = None
    impact: str | None = None
    links: list[str] = Field(default_factory=list)
    measurable_result_present: bool = False
    evidence: list[Evidence] = Field(default_factory=list)
    uncertain_fields: list[str] = Field(default_factory=list)


class SkillEntry(BaseModel):
    name: str
    category: str
    aliases_detected: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class BulletAnalysis(BaseModel):
    text: str
    section: str | None = None
    action_verb: str | None = None
    has_metric: bool = False
    technical_specificity: float = Field(default=0, ge=0, le=1)
    ownership_signal: bool = False
    clarity_score: float = Field(default=0, ge=0, le=1)
    redundant: bool = False
    weak: bool = False
    recommendation: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class QualitySignal(BaseModel):
    code: str
    severity: str
    message: str
    evidence: list[Evidence] = Field(default_factory=list)


class DocumentSignals(BaseModel):
    page_count: int
    character_count: int
    line_count: int
    bullet_count: int
    table_count: int
    heading_count: int
    layout: str
    notes: list[str] = Field(default_factory=list)


class ResumeExtraction(BaseModel):
    schema_version: str = "1.0"
    candidate: CandidateInfo = Field(default_factory=CandidateInfo)
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: ExtractedValue | None = None
    sections: list[SectionInfo] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    skills: dict[str, list[SkillEntry]] = Field(default_factory=dict)
    certifications: list[ExtractedValue] = Field(default_factory=list)
    achievements: list[ExtractedValue] = Field(default_factory=list)
    bullet_analysis: list[BulletAnalysis] = Field(default_factory=list)
    quality_signals: list[QualitySignal] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    document_signals: DocumentSignals | None = None

    def as_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
