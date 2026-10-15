from typing import Any

from pydantic import BaseModel, ConfigDict

from app.jd.schemas import JobDescriptionExtraction, JobFitReport
from app.resume.schemas import ResumeExtraction


class AIContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resume: ResumeExtraction
    job_description: JobDescriptionExtraction | None = None
    matching_report: JobFitReport | None = None

    def as_payload(self) -> dict[str, Any]:
        return {
            "resume": self.resume.model_dump(mode="json"),
            "job_description": self.job_description.model_dump(mode="json") if self.job_description else None,
            "matching_report": self.matching_report.model_dump(mode="json") if self.matching_report else None,
            "grounding_rule": "Only factual claims supported by supplied resume evidence may be made.",
        }

    def evidence_map(self) -> dict[str, str]:
        result = {item.id: item.text for item in self.resume.evidence}
        if self.job_description:
            result.update({item.id: item.text for item in self.job_description.evidence})
            for requirement in self.job_description.requirements:
                result.update({item.id: item.text for item in requirement.evidence})
        return result

    def resume_skill_names(self) -> set[str]:
        return {skill.name.casefold() for skills in self.resume.skills.values() for skill in skills}
