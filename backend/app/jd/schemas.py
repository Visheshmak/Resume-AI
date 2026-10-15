from typing import Literal

from pydantic import BaseModel, Field

from app.resume.schemas import Evidence

RequirementType = Literal["required", "preferred", "responsibility", "qualification", "soft_skill", "domain"]


class JDRequirement(BaseModel):
    id: str
    text: str
    requirement_type: RequirementType
    skill: str | None = None
    category: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0, le=1)


class JobDescriptionExtraction(BaseModel):
    schema_version: str = "1.0"
    job_title: str | None = None
    company: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    cloud_technologies: list[str] = Field(default_factory=list)
    experience_requirements: list[str] = Field(default_factory=list)
    education_requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    domain_knowledge: list[str] = Field(default_factory=list)
    requirements: list[JDRequirement] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    def as_json(self) -> dict:
        return self.model_dump(mode="json")


class RequirementMatch(BaseModel):
    skill: str
    status: Literal["matched", "partial", "missing", "concept_match"]
    requirement_type: RequirementType
    resume_evidence: list[Evidence] = Field(default_factory=list)
    jd_evidence: list[Evidence] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    explanation: str


class ScoreExplanation(BaseModel):
    category: str
    score: float = Field(ge=0, le=100)
    reason: str
    matched: int = 0
    total: int = 0


class JobFitReport(BaseModel):
    overall_match: float = Field(ge=0, le=100)
    scores: list[ScoreExplanation] = Field(default_factory=list)
    keyword_matches: list[RequirementMatch] = Field(default_factory=list)
    matched_skills: list[RequirementMatch] = Field(default_factory=list)
    missing_skills: list[RequirementMatch] = Field(default_factory=list)
    partial_matches: list[RequirementMatch] = Field(default_factory=list)
    strong_evidence: list[RequirementMatch] = Field(default_factory=list)
    weak_evidence: list[RequirementMatch] = Field(default_factory=list)
    recommended_improvements: list[str] = Field(default_factory=list)
    priority_improvements: list[dict[str, str]] = Field(default_factory=list)
    explanation: str


class MatchingWeights(BaseModel):
    required_skills: float = 0.30
    preferred_skills: float = 0.10
    experience: float = 0.15
    projects: float = 0.15
    education: float = 0.10
    keywords: float = 0.10
    responsibilities: float = 0.10
