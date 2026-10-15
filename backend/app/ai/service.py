import asyncio
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.ai.context import AIContext
from app.ai.errors import AIServiceError
from app.ai.providers import LLMProvider
from app.ai.schemas import (
    AchievementAnalysisResponse,
    BulletImprovementAnalysis,
    InterviewQuestionResponse,
    JDAlignmentResponse,
    KeywordRecommendationResponse,
    MissingSkillResponse,
    ResumeSummaryAnalysis,
)

T = TypeVar("T", bound=BaseModel)
TASK_SCHEMAS: dict[str, type[BaseModel]] = {
    "resume-summary": ResumeSummaryAnalysis,
    "bullet-improvement": BulletImprovementAnalysis,
    "achievement-analysis": AchievementAnalysisResponse,
    "jd-alignment": JDAlignmentResponse,
    "missing-skill-explanation": MissingSkillResponse,
    "keyword-recommendation": KeywordRecommendationResponse,
    "interview-questions": InterviewQuestionResponse,
}


class AIAnalysisService:
    def __init__(self, provider: LLMProvider, *, max_retries: int = 2, retry_delay_seconds: float = 0.05):
        self.provider = provider
        self.max_retries = max(0, max_retries)
        self.retry_delay_seconds = retry_delay_seconds

    async def run(self, task: str, context: AIContext) -> BaseModel:
        schema = TASK_SCHEMAS.get(task)
        if schema is None:
            raise AIServiceError("AI task is not supported", code="unsupported_task")
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                raw = await self.provider.generate(task, context, schema.model_json_schema())
                result = schema.model_validate(raw)
                self._validate_grounding(result, context)
                return result
            except (ValidationError, AIServiceError) as exc:
                last_error = exc
                if isinstance(exc, AIServiceError) and exc.code in {"provider_not_configured", "unsupported_provider"}:
                    break
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay_seconds * (attempt + 1))
            except TimeoutError:
                last_error = AIServiceError("AI provider timed out", code="provider_timeout")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay_seconds * (attempt + 1))
            except Exception:
                last_error = AIServiceError("AI provider failed", code="provider_error")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay_seconds * (attempt + 1))
        if isinstance(last_error, AIServiceError):
            raise last_error
        raise AIServiceError("AI output failed schema or grounding validation", code="invalid_grounded_output") from last_error

    def _validate_grounding(self, result: BaseModel, context: AIContext) -> None:
        evidence_map = context.evidence_map()
        evidence_ids = _evidence_ids(result)
        unknown = evidence_ids - set(evidence_map)
        if unknown:
            raise AIServiceError("AI output referenced unavailable evidence", code="ungrounded_evidence")
        for evidence_id in evidence_ids:
            if not evidence_map[evidence_id].strip():
                raise AIServiceError("AI output referenced empty evidence", code="empty_evidence")
        if isinstance(result, MissingSkillResponse):
            resume_skills = context.resume_skill_names()
            invented = {item.skill.casefold() for item in result.missing_skills if item.skill.casefold() in resume_skills}
            if invented:
                raise AIServiceError("AI output misclassified an extracted resume skill as missing", code="grounding_conflict")
        if isinstance(result, KeywordRecommendationResponse):
            resume_skills = context.resume_skill_names()
            invented = {item.keyword.casefold() for item in result.recommendations if item.status == "missing" and item.keyword.casefold() in resume_skills}
            if invented:
                raise AIServiceError("AI output marked an extracted resume skill as missing", code="grounding_conflict")
        if isinstance(result, BulletImprovementAnalysis):
            for item in result.improvements:
                if item.preserves_facts and not any(item.original_text.strip() in text or text in item.original_text.strip() for text in evidence_map.values()):
                    raise AIServiceError("Bullet improvement has no matching source evidence", code="ungrounded_bullet")


def _evidence_ids(value: object) -> set[str]:
    if isinstance(value, BaseModel):
        return _evidence_ids(value.model_dump())
    if isinstance(value, dict):
        ids: set[str] = set()
        for key, nested in value.items():
            if key == "evidence_ids" and isinstance(nested, list):
                ids.update(str(item) for item in nested)
            else:
                ids.update(_evidence_ids(nested))
        return ids
    if isinstance(value, list):
        ids: set[str] = set()
        for nested in value:
            ids.update(_evidence_ids(nested))
        return ids
    return set()
