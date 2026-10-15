import re
from collections import Counter

from app.jd.schemas import JDRequirement, JobDescriptionExtraction
from app.resume.schemas import Evidence
from app.resume.taxonomy import SKILL_DEFINITIONS, SkillDefinition

REQUIRED_MARKERS = ("required", "must have", "must be", "you have", "need to have", "essential")
PREFERRED_MARKERS = ("preferred", "nice to have", "bonus", "plus", "ideally")
RESPONSIBILITY_MARKERS = ("responsibilities", "what you will do", "you will", "duties")
QUALIFICATION_MARKERS = ("qualifications", "requirements", "education", "experience")
SOFT_SKILLS = {"communication", "leadership", "collaboration", "teamwork", "problem solving", "adaptability", "mentoring"}
DOMAIN_TERMS = {"fintech", "healthcare", "e-commerce", "ecommerce", "saas", "cybersecurity", "distributed systems", "data platform"}


class JobDescriptionIntelligenceEngine:
    def parse(self, text: str, title_hint: str | None = None) -> JobDescriptionExtraction:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        evidence = [self._evidence(index, line, "jd") for index, line in enumerate(lines, start=1)]
        title, company = self._title_company(lines, title_hint)
        requirements: list[JDRequirement] = []
        for index, line in enumerate(lines, start=1):
            if self._is_heading(line):
                continue
            line_evidence = [evidence[index - 1]]
            classification = self._classify(line, lines, index)
            extracted_skills = self._skills_in_text(line)
            if extracted_skills:
                for skill, definition in extracted_skills:
                    requirement = JDRequirement(
                        id=f"jd-line-{index}-{skill.lower().replace(' ', '-')}",
                        text=line,
                        requirement_type=classification,
                        skill=skill,
                        category=definition.category,
                        evidence=line_evidence,
                        confidence=0.95,
                    )
                    requirements.append(requirement)
            elif classification in {"responsibility", "qualification", "soft_skill", "domain"} and index != 1:
                requirements.append(JDRequirement(id=f"jd-line-{index}", text=line, requirement_type=classification, evidence=line_evidence, confidence=0.8))
        required_skills = self._unique(item.skill for item in requirements if item.requirement_type == "required" and item.skill)
        preferred_skills = self._unique(item.skill for item in requirements if item.requirement_type == "preferred" and item.skill)
        categories = {category: self._unique(item.skill for item in requirements if item.skill and item.category == category) for category in {definition.category for definition in SKILL_DEFINITIONS}}
        responsibilities = [item.text for item in requirements if item.requirement_type == "responsibility"]
        experience = [item.text for item in requirements if item.requirement_type == "qualification" and self._has_experience_signal(item.text)]
        education = [item.text for item in requirements if item.requirement_type == "qualification" and self._has_education_signal(item.text)]
        soft_skills = [item.text for item in requirements if item.requirement_type == "soft_skill"]
        domains = [item.text for item in requirements if item.requirement_type == "domain"]
        keywords = self._keywords(lines, requirements)
        return JobDescriptionExtraction(
            job_title=title,
            company=company,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            programming_languages=categories["Programming Languages"],
            frameworks=categories["Frameworks"],
            databases=categories["Databases"],
            cloud_technologies=categories["Cloud"],
            experience_requirements=experience,
            education_requirements=education,
            responsibilities=responsibilities,
            keywords=keywords,
            soft_skills=soft_skills,
            domain_knowledge=domains,
            requirements=requirements,
            evidence=evidence,
        )

    def _title_company(self, lines: list[str], title_hint: str | None) -> tuple[str | None, str | None]:
        title = title_hint or (lines[0] if lines and not self._is_heading(lines[0]) else None)
        company = None
        for line in lines[:8]:
            match = re.search(r"(?:company|employer)\s*[:\-]\s*(.+)", line, re.I)
            if match:
                company = match.group(1).strip()
                break
        if title and re.search(r"\s+at\s+", title, re.I):
            title, company = re.split(r"\s+at\s+", title, maxsplit=1, flags=re.I)
        return title, company

    def _classify(self, line: str, lines: list[str], index: int) -> str:
        lower = line.lower()
        previous = lines[index - 2].lower() if index > 1 else ""
        context = f"{previous} {lower}"
        if any(marker in context for marker in PREFERRED_MARKERS):
            return "preferred"
        if any(marker in context for marker in REQUIRED_MARKERS):
            return "required"
        if any(marker in context for marker in RESPONSIBILITY_MARKERS) or line.startswith(("-", "•", "*")) and any(word in lower for word in ("build", "develop", "design", "lead", "manage", "create", "maintain", "implement")):
            return "responsibility"
        if any(marker in context for marker in QUALIFICATION_MARKERS) or self._has_experience_signal(line) or self._has_education_signal(line):
            return "qualification"
        if any(term in lower for term in SOFT_SKILLS):
            return "soft_skill"
        if any(term in lower for term in DOMAIN_TERMS):
            return "domain"
        return "required" if self._skills_in_text(line) else "domain"

    def _skills_in_text(self, text: str) -> list[tuple[str, SkillDefinition]]:
        result: list[tuple[str, SkillDefinition]] = []
        for definition in SKILL_DEFINITIONS:
            if any(re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", text, re.I) for alias in definition.aliases):
                result.append((definition.canonical, definition))
        return result

    def _keywords(self, lines: list[str], requirements: list[JDRequirement]) -> list[str]:
        words = re.findall(r"[A-Za-z][A-Za-z+#./-]{2,}", " ".join(lines).lower())
        counts = Counter(words)
        skill_names = {skill.lower() for skill, _ in self._skills_in_text(" ".join(lines))}
        return [word for word, count in counts.most_common() if count >= 2 and word not in {"the", "and", "with", "for", "you", "our"} or word in skill_names][:30]

    def _has_experience_signal(self, text: str) -> bool:
        return bool(re.search(r"\b\d+\+?\s+years?\b|experience with|experience in", text, re.I))

    def _has_education_signal(self, text: str) -> bool:
        return bool(re.search(r"bachelor|master|degree|computer science|engineering|education|ph\.?d", text, re.I))

    def _is_heading(self, text: str) -> bool:
        lower = text.lower().strip(" :")
        return len(text) < 60 and (text.isupper() or lower in {"responsibilities", "requirements", "qualifications", "preferred qualifications", "about the role"})

    def _evidence(self, line_number: int, text: str, source_type: str) -> Evidence:
        return Evidence(id=f"{source_type}-line-{line_number}", source_type=source_type, line_number=line_number, section=None, text=text)

    def _unique(self, values) -> list[str]:
        result = []
        for value in values:
            if value and value not in result:
                result.append(value)
        return result
