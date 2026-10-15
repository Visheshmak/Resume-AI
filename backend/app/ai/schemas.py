from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GroundedItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=2000)
    evidence_ids: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    reasoning_summary: str = Field(min_length=1, max_length=500)


class ResumeSummaryAnalysis(BaseModel):
    summary: GroundedItem
    strengths: list[GroundedItem] = Field(default_factory=list)
    limitations: list[GroundedItem] = Field(default_factory=list)


class BulletImprovement(BaseModel):
    original_text: str = Field(min_length=1)
    improved_text: str = Field(min_length=1)
    preserves_facts: bool
    evidence_ids: list[str] = Field(min_length=1)
    note: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)


class BulletImprovementAnalysis(BaseModel):
    improvements: list[BulletImprovement] = Field(default_factory=list)


class AchievementAnalysis(BaseModel):
    bullet: GroundedItem
    has_measurable_impact: bool
    missing_detail: str | None = None


class AchievementAnalysisResponse(BaseModel):
    achievements: list[AchievementAnalysis] = Field(default_factory=list)


class JDAlignmentExplanation(BaseModel):
    requirement_id: str
    explanation: GroundedItem


class JDAlignmentResponse(BaseModel):
    alignments: list[JDAlignmentExplanation] = Field(default_factory=list)


class MissingSkillExplanation(BaseModel):
    skill: str
    explanation: GroundedItem


class MissingSkillResponse(BaseModel):
    missing_skills: list[MissingSkillExplanation] = Field(default_factory=list)


class KeywordRecommendation(BaseModel):
    keyword: str
    recommendation: GroundedItem
    status: Literal["missing", "partial", "matched"]


class KeywordRecommendationResponse(BaseModel):
    recommendations: list[KeywordRecommendation] = Field(default_factory=list)


QuestionCategory = Literal["technical", "project", "behavioral", "role-specific", "resume-verification"]
QuestionDifficulty = Literal["easy", "medium", "hard"]


class InterviewQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    category: QuestionCategory
    difficulty: QuestionDifficulty
    why_relevant: str = Field(min_length=1, max_length=500)
    evidence_ids: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class InterviewQuestionResponse(BaseModel):
    questions: list[InterviewQuestion] = Field(default_factory=list)


class AIAnalysisBundle(BaseModel):
    summary: ResumeSummaryAnalysis | None = None
    bullet_improvements: BulletImprovementAnalysis | None = None
    achievements: AchievementAnalysisResponse | None = None
    jd_alignment: JDAlignmentResponse | None = None
    missing_skills: MissingSkillResponse | None = None
    keyword_recommendations: KeywordRecommendationResponse | None = None
    interview_questions: InterviewQuestionResponse | None = None

    def all_evidence_ids(self) -> set[str]:
        return {
            evidence_id
            for item in self.model_dump().values()
            if item
            for evidence_id in _nested_evidence_ids(item)
        }


def _nested_evidence_ids(value: object):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "evidence_ids" and isinstance(nested, list):
                yield from nested
            else:
                yield from _nested_evidence_ids(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _nested_evidence_ids(nested)
