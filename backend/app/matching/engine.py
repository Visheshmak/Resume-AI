import re

from app.jd.schemas import (
    JDRequirement,
    JobDescriptionExtraction,
    JobFitReport,
    MatchingWeights,
    RequirementMatch,
    ScoreExplanation,
)
from app.resume.schemas import Evidence, ResumeExtraction

CONCEPTS = {
    "restful backend services": {"api", "apis", "rest", "restful", "fastapi", "flask", "django", "backend services"},
    "data analysis": {"pandas", "numpy", "data analysis", "analytics", "analysis"},
    "cloud deployment": {"aws", "azure", "gcp", "cloud", "docker", "kubernetes", "deployment"},
}


class ResumeJDMatcher:
    def __init__(self, weights: MatchingWeights | None = None):
        self.weights = weights or MatchingWeights()

    def match(self, resume: ResumeExtraction, job: JobDescriptionExtraction) -> JobFitReport:
        resume_skill_map = {skill.name.lower(): skill for skills in resume.skills.values() for skill in skills}
        resume_text = self._resume_text(resume).lower()
        matches: list[RequirementMatch] = []
        for requirement in job.requirements:
            if requirement.skill:
                match = self._match_skill(requirement, resume_skill_map)
            else:
                match = self._match_concept(requirement, resume_text, resume)
            matches.append(match)
        required = [item for item in matches if item.requirement_type == "required"]
        preferred = [item for item in matches if item.requirement_type == "preferred"]
        responsibilities = [item for item in matches if item.requirement_type == "responsibility"]
        qualification = [item for item in matches if item.requirement_type == "qualification"]
        keyword_matches = self._keyword_matches(job, resume_text)
        category_scores = [
            self._score("Required Skills", required),
            self._score("Preferred Skills", preferred),
            self._score("Experience", [item for item in qualification if "experience" in item.explanation.lower()]),
            self._score("Projects", self._project_matches(matches)),
            self._score("Education", [item for item in qualification if "education" in item.explanation.lower() or "degree" in item.explanation.lower()]),
            self._score("Keywords", keyword_matches),
            self._score("Responsibilities", responsibilities),
        ]
        overall = round(sum(score.score * weight for score, weight in zip(category_scores, self._weights(), strict=True)), 1)
        matched = [item for item in matches if item.status == "matched"]
        partial = [item for item in matches if item.status == "partial" or item.status == "concept_match"]
        missing = [item for item in matches if item.status == "missing"]
        improvements = self._improvements(missing, partial)
        return JobFitReport(
            overall_match=overall,
            scores=category_scores,
            keyword_matches=keyword_matches,
            matched_skills=matched,
            missing_skills=missing,
            partial_matches=partial,
            strong_evidence=[item for item in matched if item.confidence >= 0.85],
            weak_evidence=[item for item in matches if item.confidence < 0.85],
            recommended_improvements=improvements,
            priority_improvements=[{"priority": "High Priority", "recommendation": item} for item in improvements[:3]],
            explanation=f"Overall match is {overall}/100 from weighted evidence categories; no missing skill is treated as present.",
        )

    def _match_skill(self, requirement: JDRequirement, resume_skill_map: dict[str, object]) -> RequirementMatch:
        assert requirement.skill is not None
        skill = resume_skill_map.get(requirement.skill.lower())
        if skill is not None:
            evidence = skill.evidence
            return RequirementMatch(skill=requirement.skill, status="matched", requirement_type=requirement.requirement_type, resume_evidence=evidence, jd_evidence=requirement.evidence, confidence=0.98, explanation="Exact normalized skill match with resume evidence.")
        concept_evidence = self._concept_evidence(requirement.skill, resume_skill_map)
        if concept_evidence:
            return RequirementMatch(skill=requirement.skill, status="partial", requirement_type=requirement.requirement_type, resume_evidence=concept_evidence, jd_evidence=requirement.evidence, confidence=0.58, explanation="Related concept evidence exists, but the specific technology was not explicitly detected.")
        return RequirementMatch(skill=requirement.skill, status="missing", requirement_type=requirement.requirement_type, jd_evidence=requirement.evidence, confidence=0.98, explanation="No explicit normalized skill evidence was found in the resume.")

    def _match_concept(self, requirement: JDRequirement, resume_text: str, resume: ResumeExtraction) -> RequirementMatch:
        tokens = set(re.findall(r"[a-z][a-z-]+", requirement.text.lower()))
        best_name, best_overlap = None, 0
        for name, concept_tokens in CONCEPTS.items():
            overlap = len(tokens & concept_tokens) / max(1, len(tokens & concept_tokens | concept_tokens))
            if overlap > best_overlap:
                best_name, best_overlap = name, overlap
        resume_overlap = sum(1 for token in (CONCEPTS.get(best_name or "", set())) if token in resume_text)
        if resume_overlap:
            evidence = resume.evidence[:3]
            return RequirementMatch(skill=best_name or requirement.text, status="concept_match", requirement_type=requirement.requirement_type, resume_evidence=evidence, jd_evidence=requirement.evidence, confidence=min(0.75, 0.45 + resume_overlap * 0.08), explanation="Conceptually relevant resume evidence was found; this does not prove a specific technology.")
        return RequirementMatch(skill=best_name or requirement.text, status="missing", requirement_type=requirement.requirement_type, jd_evidence=requirement.evidence, confidence=0.7, explanation="No relevant resume evidence was found for this responsibility or concept.")

    def _score(self, category: str, items: list[RequirementMatch]) -> ScoreExplanation:
        if not items:
            return ScoreExplanation(category=category, score=0, reason="No structured requirements were available for this category.")
        points = sum(1 if item.status == "matched" else 0.5 if item.status in {"partial", "concept_match"} else 0 for item in items)
        score = round(points / len(items) * 100, 1)
        return ScoreExplanation(category=category, score=score, reason=f"{points:g}/{len(items)} evidence-weighted requirements detected.", matched=int(points), total=len(items))

    def _keyword_matches(self, job: JobDescriptionExtraction, resume_text: str) -> list[RequirementMatch]:
        return [RequirementMatch(skill=keyword, status="matched" if keyword.lower() in resume_text else "missing", requirement_type="domain", confidence=0.85, explanation="Keyword present in normalized resume text." if keyword.lower() in resume_text else "Keyword not found in normalized resume text.") for keyword in job.keywords]

    def _project_matches(self, matches: list[RequirementMatch]) -> list[RequirementMatch]:
        return [item for item in matches if item.requirement_type == "responsibility" and item.status in {"matched", "concept_match", "partial"}]

    def _concept_evidence(self, skill: str, resume_skill_map: dict[str, object]) -> list[Evidence]:
        related = {"Kubernetes": {"Docker"}, "FastAPI": {"Python", "Flask", "Django"}, "AWS": {"Azure", "GCP"}}
        evidence = []
        for related_skill in related.get(skill, set()):
            candidate = resume_skill_map.get(related_skill.lower())
            if candidate:
                evidence.extend(candidate.evidence)
        return evidence

    def _resume_text(self, resume: ResumeExtraction) -> str:
        fragments = [resume.summary.value if resume.summary else ""]
        fragments.extend(item.text for item in resume.bullet_analysis)
        fragments.extend(item.description or "" for item in resume.projects)
        fragments.extend(item.role or "" for item in resume.experience)
        fragments.extend(skill.name for skills in resume.skills.values() for skill in skills)
        return " ".join(fragments)

    def _weights(self) -> list[float]:
        return [self.weights.required_skills, self.weights.preferred_skills, self.weights.experience, self.weights.projects, self.weights.education, self.weights.keywords, self.weights.responsibilities]

    def _improvements(self, missing: list[RequirementMatch], partial: list[RequirementMatch]) -> list[str]:
        improvements = [f"Add explicit evidence for {item.skill} if you have used it; otherwise leave it marked as missing." for item in missing if item.requirement_type in {"required", "preferred"}]
        improvements.extend(f"Clarify related experience for {item.skill} without implying the exact technology was used." for item in partial)
        return improvements
