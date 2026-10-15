
import pytest

from app.ai.context import AIContext
from app.ai.errors import AIServiceError
from app.ai.providers import MockProvider
from app.ai.schemas import ResumeSummaryAnalysis
from app.ai.service import AIAnalysisService
from app.jd.schemas import JobDescriptionExtraction
from app.resume.schemas import Evidence, ExtractedValue, ResumeExtraction, SkillEntry


def make_context() -> AIContext:
    python_evidence = Evidence(id="resume-line-1", text="Built REST APIs using Python and FastAPI.", line_number=1)
    resume = ResumeExtraction(
        summary=ExtractedValue(value="Backend engineer", evidence=[python_evidence]),
        skills={"Programming Languages": [SkillEntry(name="Python", category="Programming Languages", evidence=[python_evidence])]},
        evidence=[python_evidence],
    )
    return AIContext(resume=resume, job_description=JobDescriptionExtraction())


def valid_summary() -> dict:
    return {
        "summary": {
            "text": "Backend engineer with Python API experience.",
            "evidence_ids": ["resume-line-1"],
            "confidence": 0.9,
            "reasoning_summary": "This statement is supported by the supplied resume line.",
        },
        "strengths": [],
        "limitations": [],
    }


@pytest.mark.asyncio
async def test_valid_ai_response_is_typed_and_grounded() -> None:
    provider = MockProvider({"resume-summary": valid_summary()})

    result = await AIAnalysisService(provider).run("resume-summary", make_context())

    assert isinstance(result, ResumeSummaryAnalysis)
    assert result.summary.evidence_ids == ["resume-line-1"]


@pytest.mark.asyncio
async def test_invalid_output_retries_then_succeeds() -> None:
    class RetryProvider(MockProvider):
        def __init__(self):
            super().__init__()
            self.attempt = 0

        async def generate(self, task, context, output_schema):
            self.attempt += 1
            return {"invalid": True} if self.attempt == 1 else valid_summary()

    provider = RetryProvider()
    result = await AIAnalysisService(provider, max_retries=1, retry_delay_seconds=0).run("resume-summary", make_context())

    assert isinstance(result, ResumeSummaryAnalysis)
    assert provider.attempt == 2


@pytest.mark.asyncio
async def test_unknown_evidence_is_rejected_after_retry() -> None:
    invalid = valid_summary()
    invalid["summary"]["evidence_ids"] = ["not-in-resume"]

    with pytest.raises(AIServiceError, match="unavailable evidence"):
        await AIAnalysisService(MockProvider({"resume-summary": invalid}), max_retries=1, retry_delay_seconds=0).run("resume-summary", make_context())


@pytest.mark.asyncio
async def test_missing_skill_cannot_conflict_with_extracted_skill() -> None:
    response = {"missing_skills": [{"skill": "Python", "explanation": {"text": "Python is missing.", "evidence_ids": ["resume-line-1"], "confidence": 0.9, "reasoning_summary": "Unsupported claim."}}]}

    with pytest.raises(AIServiceError, match="misclassified"):
        await AIAnalysisService(MockProvider({"missing-skill-explanation": response})).run("missing-skill-explanation", make_context())


@pytest.mark.asyncio
async def test_provider_timeout_is_controlled_and_retried() -> None:
    provider = MockProvider(error=TimeoutError())

    with pytest.raises(AIServiceError, match="timed out"):
        await AIAnalysisService(provider, max_retries=1, retry_delay_seconds=0).run("resume-summary", make_context())
    assert provider.calls == ["resume-summary", "resume-summary"]


@pytest.mark.asyncio
async def test_provider_failure_is_controlled() -> None:
    with pytest.raises(AIServiceError, match="AI provider failed"):
        await AIAnalysisService(MockProvider(error=RuntimeError("secret provider detail"))).run("resume-summary", make_context())