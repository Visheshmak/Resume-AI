from app.ai.context import AIContext
from app.ai.errors import AIServiceError
from app.ai.schemas import (
    AchievementAnalysisResponse,
    BulletImprovementAnalysis,
    InterviewQuestionResponse,
    JDAlignmentResponse,
    KeywordRecommendationResponse,
    MissingSkillResponse,
    ResumeSummaryAnalysis,
)
from app.ai.service import AIAnalysisService


async def analyze_resume_summary(service: AIAnalysisService, context: AIContext) -> ResumeSummaryAnalysis:
    return await service.run("resume-summary", context)  # type: ignore[return-value]


async def improve_bullets(service: AIAnalysisService, context: AIContext) -> BulletImprovementAnalysis:
    return await service.run("bullet-improvement", context)  # type: ignore[return-value]


async def analyze_achievements(service: AIAnalysisService, context: AIContext) -> AchievementAnalysisResponse:
    return await service.run("achievement-analysis", context)  # type: ignore[return-value]


async def explain_jd_alignment(service: AIAnalysisService, context: AIContext) -> JDAlignmentResponse:
    if context.job_description is None or context.matching_report is None:
        raise AIServiceError("Job description and matching report are required", code="missing_ai_context")
    return await service.run("jd-alignment", context)  # type: ignore[return-value]


async def explain_missing_skills(service: AIAnalysisService, context: AIContext) -> MissingSkillResponse:
    if context.matching_report is None:
        raise AIServiceError("Matching report is required", code="missing_ai_context")
    return await service.run("missing-skill-explanation", context)  # type: ignore[return-value]


async def recommend_keywords(service: AIAnalysisService, context: AIContext) -> KeywordRecommendationResponse:
    if context.job_description is None or context.matching_report is None:
        raise AIServiceError("Job description and matching report are required", code="missing_ai_context")
    return await service.run("keyword-recommendation", context)  # type: ignore[return-value]


async def generate_interview_questions(service: AIAnalysisService, context: AIContext) -> InterviewQuestionResponse:
    if context.job_description is None:
        raise AIServiceError("Job description is required", code="missing_ai_context")
    return await service.run("interview-questions", context)  # type: ignore[return-value]
