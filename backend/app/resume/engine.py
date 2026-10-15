import re
from collections import Counter, defaultdict
from collections.abc import Iterable

from app.resume.document import DocumentLine, ExtractedDocument, extract_document
from app.resume.schemas import (
    BulletAnalysis,
    CandidateInfo,
    ContactInfo,
    DocumentSignals,
    EducationEntry,
    Evidence,
    ExperienceEntry,
    ExtractedValue,
    ProjectEntry,
    QualitySignal,
    ResumeExtraction,
    SectionInfo,
    SkillEntry,
)
from app.resume.taxonomy import SKILL_DEFINITIONS

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "professional summary", "profile", "objective", "career objective"),
    "education": ("education", "academic background", "academic experience"),
    "experience": ("experience", "work experience", "professional experience", "employment", "internships", "internship"),
    "projects": ("projects", "personal projects", "academic projects", "selected projects"),
    "skills": ("skills", "technical skills", "core skills", "competencies", "technologies"),
    "certifications": ("certifications", "certificates", "licenses", "licenses & certifications"),
    "achievements": ("achievements", "awards", "honors", "accomplishments"),
    "publications": ("publications", "research", "papers"),
    "leadership": ("leadership", "leadership experience"),
    "extracurricular": ("extracurricular activities", "activities", "volunteering", "volunteer experience"),
}

EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d().\-\s]{7,}\d)(?!\d)")
URL_PATTERN = re.compile(r"(?:https?://|www\.|(?:linkedin|github)\.com/)[^\s<>()]+", re.I)
DATE_RANGE_PATTERN = re.compile(
    r"(?P<start>(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{1,2}/)?\s*\d{4})\s*(?:-|–|—|to)\s*(?P<end>Present|Current|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{1,2}/)?\s*\d{4})",
    re.I,
)
YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
METRIC_PATTERN = re.compile(r"(?:\b\d+(?:\.\d+)?\s*%|\$\s*\d[\d,.]*|\b\d[\d,.]*\s*(?:x|users|customers|records|projects|people|ms|seconds|hours|days|months|years)\b|\b(?:increased|decreased|reduced|improved|grew|saved)\b)", re.I)

ACTION_VERBS = {
    "built", "created", "designed", "developed", "implemented", "automated", "optimized", "launched", "led", "managed",
    "delivered", "migrated", "architected", "integrated", "deployed", "analyzed", "improved", "reduced", "increased",
    "engineered", "wrote", "programmed", "mentored", "coordinated", "owned", "streamlined", "configured",
}
WEAK_VERBS = {"worked", "helped", "assisted", "responsible", "involved", "participated", "did", "handled"}
BUZZWORDS = {"results-driven", "synergy", "dynamic", "go-getter", "team player", "hardworking", "passionate", "strategic thinker"}


class ResumeIntelligenceEngine:
    """Deterministic resume extraction with source evidence and conservative fallbacks."""

    def parse_bytes(self, content: bytes, file_type: str) -> tuple[ResumeExtraction, str]:
        document = extract_document(content, file_type)
        extraction = self.parse_document(document)
        return extraction, document.text

    def parse_document(self, document: ExtractedDocument) -> ResumeExtraction:
        sections = self._detect_sections(document.lines)
        evidence: list[Evidence] = []
        for section in sections:
            evidence.extend(section.evidence)
        candidate = self._extract_candidate(document.lines, sections, evidence)
        contact = self._extract_contact(document.lines, sections, evidence)
        summary = self._extract_summary(document.lines, sections, evidence)
        skills = self._extract_skills(document.lines, sections, evidence)
        education = self._extract_education(document.lines, sections, evidence)
        experience = self._extract_experience(document.lines, sections, skills, evidence)
        projects = self._extract_projects(document.lines, sections, skills, evidence)
        certifications = self._extract_values(document.lines, sections, "certifications", evidence)
        achievements = self._extract_values(document.lines, sections, "achievements", evidence)
        bullets = self._analyze_bullets(document.lines, sections, skills, evidence)
        quality = self._quality_signals(document, sections, bullets, evidence)
        signal = DocumentSignals(
            page_count=document.page_count,
            character_count=len(document.text),
            line_count=len(document.lines),
            bullet_count=sum(line.is_bullet for line in document.lines),
            table_count=document.table_count,
            heading_count=len(sections),
            layout="mixed/table" if document.table_count else "standard reading order",
            notes=list(document.notes),
        )
        return ResumeExtraction(
            candidate=candidate,
            contact=contact,
            summary=summary,
            sections=sections,
            education=education,
            experience=experience,
            projects=projects,
            skills=dict(skills),
            certifications=certifications,
            achievements=achievements,
            bullet_analysis=bullets,
            quality_signals=quality,
            evidence=evidence,
            document_signals=signal,
        )

    def _detect_sections(self, lines: list[DocumentLine]) -> list[SectionInfo]:
        found: list[tuple[int, str, str]] = []
        for index, line in enumerate(lines):
            canonical = self._section_name(line.text)
            if canonical:
                found.append((index, canonical, line.text))
        sections: list[SectionInfo] = []
        for position, (index, canonical, heading) in enumerate(found):
            end_index = found[position + 1][0] - 1 if position + 1 < len(found) else len(lines) - 1
            heading_line = lines[index]
            sections.append(
                SectionInfo(
                    name=canonical,
                    heading=heading,
                    start_line=index + 1,
                    end_line=end_index + 1,
                    evidence=[self._evidence(heading_line, canonical)],
                )
            )
        return sections

    def _section_name(self, text: str) -> str | None:
        cleaned = re.sub(r"[:|\-]+$", "", " ".join(text.lower().split())).strip()
        for canonical, aliases in SECTION_ALIASES.items():
            if cleaned in aliases:
                return canonical
            if any(cleaned.startswith(f"{alias} ") for alias in aliases):
                return canonical
        if len(cleaned) <= 45 and cleaned.upper() == cleaned and cleaned.lower() in {alias.lower() for aliases in SECTION_ALIASES.values() for alias in aliases}:
            for canonical, aliases in SECTION_ALIASES.items():
                if cleaned.lower() in aliases:
                    return canonical
        return None

    def _extract_candidate(self, lines: list[DocumentLine], sections: list[SectionInfo], evidence: list[Evidence]) -> CandidateInfo:
        first_section = sections[0].start_line - 1 if sections else min(len(lines), 8)
        for line in lines[:first_section]:
            if self._is_header_noise(line.text):
                continue
            candidate_text = re.split(r"\s+(?=[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", line.text, maxsplit=1)[0].strip(" |,-")
            if 1 < len(candidate_text.split()) <= 5 and not EMAIL_PATTERN.search(candidate_text) and not URL_PATTERN.search(candidate_text) and not PHONE_PATTERN.search(candidate_text):
                item = ExtractedValue(value=candidate_text, evidence=[self._evidence(line, "header")], confidence=0.8, uncertain=True)
                evidence.extend(item.evidence)
                return CandidateInfo(name=item)
        return CandidateInfo()

    def _extract_contact(self, lines: list[DocumentLine], sections: list[SectionInfo], evidence: list[Evidence]) -> ContactInfo:
        header_lines = lines[: (sections[0].start_line - 1 if sections else min(len(lines), 12))]
        contact = ContactInfo()
        for line in header_lines:
            self._set_contact(contact, "email", EMAIL_PATTERN.search(line.text), line, evidence)
            self._set_contact(contact, "phone", self._phone_match(line.text), line, evidence)
            urls = URL_PATTERN.findall(line.text)
            for url in urls:
                clean_url = url.rstrip(".,;)")
                field = "linkedin" if "linkedin.com" in clean_url.lower() else "github" if "github.com" in clean_url.lower() else "portfolio"
                if getattr(contact, field) is None:
                    value = ExtractedValue(value=clean_url, evidence=[self._evidence(line, "contact")])
                    setattr(contact, field, value)
                    evidence.extend(value.evidence)
            if contact.location is None and "," in line.text:
                location_candidate = EMAIL_PATTERN.sub("", line.text)
                location_candidate = PHONE_PATTERN.sub("", location_candidate)
                location_candidate = URL_PATTERN.sub("", location_candidate)
                location_candidate = location_candidate.strip(" |,-")
                if location_candidate:
                    value = ExtractedValue(value=location_candidate, evidence=[self._evidence(line, "contact")], confidence=0.55, uncertain=True)
                    contact.location = value
                    evidence.extend(value.evidence)
        return contact

    def _set_contact(self, contact: ContactInfo, field: str, match: re.Match[str] | None, line: DocumentLine, evidence: list[Evidence]) -> None:
        if match is not None and getattr(contact, field) is None:
            value = ExtractedValue(value=match.group(0).strip(), evidence=[self._evidence(line, "contact")])
            setattr(contact, field, value)
            evidence.extend(value.evidence)

    def _extract_summary(self, lines: list[DocumentLine], sections: list[SectionInfo], evidence: list[Evidence]) -> ExtractedValue | None:
        content = self._section_lines(lines, sections, "summary")
        if not content:
            return None
        selected = content[:8]
        values = [line.text for line in selected]
        item = ExtractedValue(value=" ".join(values), evidence=[self._evidence(line, "summary") for line in selected])
        evidence.extend(item.evidence)
        return item

    def _extract_skills(self, lines: list[DocumentLine], sections: list[SectionInfo], evidence: list[Evidence]) -> dict[str, list[SkillEntry]]:
        found: dict[str, dict[str, SkillEntry]] = defaultdict(dict)
        search_lines = self._section_lines(lines, sections, "skills") or lines
        for definition in SKILL_DEFINITIONS:
            aliases: list[str] = []
            line_evidence: list[Evidence] = []
            for line in search_lines:
                for alias in sorted(definition.aliases, key=len, reverse=True):
                    if self._contains_term(line.text, alias):
                        if alias not in aliases:
                            aliases.append(alias)
                        line_evidence.append(self._evidence(line, "skills"))
                        break
            if line_evidence:
                unique_evidence = self._unique_evidence(line_evidence)
                item = SkillEntry(name=definition.canonical, category=definition.category, aliases_detected=aliases, evidence=unique_evidence)
                found[definition.category][definition.canonical] = item
                evidence.extend(unique_evidence)
        return {category: list(items.values()) for category, items in found.items()}

    def _extract_education(self, lines: list[DocumentLine], sections: list[SectionInfo], evidence: list[Evidence]) -> list[EducationEntry]:
        content = self._section_lines(lines, sections, "education")
        if not content:
            return []
        entries: list[EducationEntry] = []
        for line in content:
            if line.is_bullet and entries:
                entries[-1].details.append(self._strip_bullet(line.text))
                entries[-1].evidence.append(self._evidence(line, "education"))
                continue
            years = YEAR_PATTERN.findall(line.text)
            degree = self._find_degree(line.text)
            institution = line.text if not degree else line.text.replace(degree, "").strip(" ,-|")
            item = EducationEntry(institution=institution or None, degree=degree, dates=" - ".join(years) if years else None, evidence=[self._evidence(line, "education")], uncertain=not bool(degree or years))
            entries.append(item)
            evidence.extend(item.evidence)
        return entries

    def _extract_experience(self, lines: list[DocumentLine], sections: list[SectionInfo], skills: dict[str, list[SkillEntry]], evidence: list[Evidence]) -> list[ExperienceEntry]:
        content = self._section_lines(lines, sections, "experience")
        entries: list[ExperienceEntry] = []
        current: ExperienceEntry | None = None
        for line in content:
            match = DATE_RANGE_PATTERN.search(line.text)
            if current is None:
                current = ExperienceEntry()
            current.evidence.append(self._evidence(line, "experience"))
            if match:
                if current.start_date and self._has_content(current):
                    entries.append(current)
                    current = ExperienceEntry(evidence=[self._evidence(line, "experience")])
                current.start_date = match.group("start").strip()
                current.end_date = match.group("end").strip()
                current.duration = self._duration(current.start_date, current.end_date)
                prefix = line.text[: match.start()].strip(" ,-|")
                if prefix:
                    parts = [part.strip() for part in prefix.split("|") if part.strip()]
                    if len(parts) >= 2:
                        current.role = parts[0]
                        current.company = parts[1]
                    else:
                        current.role = prefix if current.role is None else current.company
            elif line.is_bullet:
                text = self._strip_bullet(line.text)
                current.responsibilities.append(text)
                if METRIC_PATTERN.search(text):
                    current.achievements.append(text)
            elif not current.role:
                current.role = line.text
            elif not current.company and not current.responsibilities:
                current.company = line.text
            else:
                current.responsibilities.append(line.text)
            current.technologies = self._skills_in_text(" ".join(current.responsibilities + [current.role or "", current.company or ""]), skills)
        if current and self._has_content(current):
            entries.append(current)
        for item in entries:
            evidence.extend(item.evidence)
        return entries

    def _extract_projects(self, lines: list[DocumentLine], sections: list[SectionInfo], skills: dict[str, list[SkillEntry]], evidence: list[Evidence]) -> list[ProjectEntry]:
        content = self._section_lines(lines, sections, "projects")
        entries: list[ProjectEntry] = []
        current: ProjectEntry | None = None
        for line in content:
            urls = [url.rstrip(".,;)") for url in URL_PATTERN.findall(line.text)]
            if current is None or (not line.is_bullet and current.name and (urls or line.text != current.name) and current.description):
                if current is not None:
                    entries.append(current)
                current = ProjectEntry(name=line.text if not line.is_bullet else None, evidence=[])
            current.evidence.append(self._evidence(line, "projects"))
            if urls:
                current.links.extend(urls)
            elif line.is_bullet:
                text = self._strip_bullet(line.text)
                current.description = f"{current.description} {text}".strip() if current.description else text
            elif current.name != line.text:
                current.description = f"{current.description} {line.text}".strip() if current.description else line.text
            current.technologies = self._skills_in_text(current.description or current.name or "", skills)
            current.measurable_result_present = bool(METRIC_PATTERN.search(current.description or ""))
        if current is not None:
            entries.append(current)
        for item in entries:
            if not item.measurable_result_present:
                item.uncertain_fields.append("impact")
            evidence.extend(item.evidence)
        return entries

    def _extract_values(self, lines: list[DocumentLine], sections: list[SectionInfo], section_name: str, evidence: list[Evidence]) -> list[ExtractedValue]:
        values: list[ExtractedValue] = []
        for line in self._section_lines(lines, sections, section_name):
            value = ExtractedValue(value=self._strip_bullet(line.text), evidence=[self._evidence(line, section_name)])
            values.append(value)
            evidence.extend(value.evidence)
        return values

    def _analyze_bullets(self, lines: list[DocumentLine], sections: list[SectionInfo], skills: dict[str, list[SkillEntry]], evidence: list[Evidence]) -> list[BulletAnalysis]:
        analyses: list[BulletAnalysis] = []
        seen: Counter[str] = Counter(self._normalize(line.text) for line in lines if line.is_bullet)
        for line in lines:
            if not line.is_bullet:
                continue
            text = self._strip_bullet(line.text)
            first_word = text.split(maxsplit=1)[0].lower().rstrip(",:") if text else ""
            has_metric = bool(METRIC_PATTERN.search(text))
            technicality = min(1.0, len(self._skills_in_text(text, skills)) / 3)
            ownership = first_word in ACTION_VERBS
            clarity = min(1.0, max(0.2, len(text.split()) / 18))
            weak = first_word in WEAK_VERBS or (not has_metric and len(text.split()) < 8)
            recommendation = None
            if weak:
                recommendation = "Use a specific action verb, name the technology or output, and add a measurable result when one exists in your source facts."
            item = BulletAnalysis(
                text=text,
                section=self._section_for_line(line.line_number, sections),
                action_verb=first_word if first_word in ACTION_VERBS | WEAK_VERBS else None,
                has_metric=has_metric,
                technical_specificity=technicality,
                ownership_signal=ownership,
                clarity_score=clarity,
                redundant=seen[self._normalize(line.text)] > 1,
                weak=weak,
                recommendation=recommendation,
                evidence=[self._evidence(line, self._section_for_line(line.line_number, sections))],
            )
            analyses.append(item)
            evidence.extend(item.evidence)
        return analyses

    def _quality_signals(self, document: ExtractedDocument, sections: list[SectionInfo], bullets: list[BulletAnalysis], evidence: list[Evidence]) -> list[QualitySignal]:
        signals: list[QualitySignal] = []
        expected = {"education", "experience", "skills"}
        present = {section.name for section in sections}
        for missing in sorted(expected - present):
            signals.append(QualitySignal(code=f"missing_{missing}", severity="warning", message=f"No {missing} section was confidently detected."))
        counts = Counter(self._normalize(line.text) for line in document.lines if line.text)
        for line in document.lines:
            if counts[self._normalize(line.text)] > 1 and len(line.text) > 20:
                signals.append(QualitySignal(code="repeated_information", severity="warning", message="Repeated text may reduce clarity.", evidence=[self._evidence(line, self._section_for_line(line.line_number, sections))]))
                break
        for section in sections:
            length = section.end_line - section.start_line + 1
            if length > 24:
                signals.append(QualitySignal(code="long_section", severity="info", message=f"The {section.name} section is unusually long."))
        buzzword_lines = [line for line in document.lines if any(word in line.text.lower() for word in BUZZWORDS)]
        if buzzword_lines:
            signals.append(QualitySignal(code="buzzword_usage", severity="info", message="Generic buzzwords were detected; replace them with evidence where possible.", evidence=[self._evidence(buzzword_lines[0], "quality")]))
        weak_bullets = [item for item in bullets if item.weak]
        if weak_bullets:
            signals.append(QualitySignal(code="weak_bullets", severity="warning", message=f"{len(weak_bullets)} bullet(s) may need stronger action, specificity, or impact evidence.", evidence=weak_bullets[0].evidence))
        malformed_links = [line for line in document.lines if "http" in line.text.lower() and not URL_PATTERN.search(line.text)]
        if malformed_links:
            signals.append(QualitySignal(code="malformed_link", severity="warning", message="A possible link does not match a recognizable URL format.", evidence=[self._evidence(malformed_links[0], "quality")]))
        for signal in signals:
            evidence.extend(signal.evidence)
        return signals

    def _section_lines(self, lines: list[DocumentLine], sections: list[SectionInfo], name: str) -> list[DocumentLine]:
        ranges = [(section.start_line, section.end_line) for section in sections if section.name == name]
        return [line for line in lines if any(start <= line.line_number <= end for start, end in ranges)]

    def _section_for_line(self, line_number: int, sections: list[SectionInfo]) -> str | None:
        for section in sections:
            if section.start_line <= line_number <= section.end_line:
                return section.name
        return None

    def _evidence(self, line: DocumentLine, section: str | None) -> Evidence:
        return Evidence(id=f"line-{line.line_number}", page_number=line.page_number, line_number=line.line_number, section=section, text=line.text)

    def _unique_evidence(self, items: Iterable[Evidence]) -> list[Evidence]:
        result: list[Evidence] = []
        seen: set[str] = set()
        for item in items:
            if item.id not in seen:
                result.append(item)
                seen.add(item.id)
        return result

    def _contains_term(self, text: str, term: str) -> bool:
        return bool(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, re.I))

    def _skills_in_text(self, text: str, skills: dict[str, list[SkillEntry]]) -> list[str]:
        return [item.name for items in skills.values() for item in items if self._contains_term(text, item.name) or any(self._contains_term(text, alias) for alias in item.aliases_detected)]

    def _phone_match(self, text: str) -> re.Match[str] | None:
        match = PHONE_PATTERN.search(text)
        if match and len(re.sub(r"\D", "", match.group(0))) >= 8:
            return match
        return None

    def _find_degree(self, text: str) -> str | None:
        match = re.search(r"\b(?:B\.?(?:S|A)|M\.?(?:S|A)|Ph\.?D|Bachelor|Master|Doctorate|Associate)[^,|\n]*", text, re.I)
        return match.group(0).strip() if match else None

    def _duration(self, start: str, end: str) -> str | None:
        start_year = re.search(r"\d{4}", start)
        end_year = re.search(r"\d{4}", end)
        if not start_year or not end_year:
            if end.lower() in {"present", "current"}:
                return "ongoing (exact duration uncertain)"
            return None
        years = int(end_year.group()) - int(start_year.group())
        return f"approximately {max(years, 0)} year(s)"

    def _has_content(self, item: ExperienceEntry) -> bool:
        return bool(item.role or item.company or item.responsibilities or item.start_date)

    def _strip_bullet(self, text: str) -> str:
        return re.sub(r"^[\-*•‣▪◦]\s*", "", text).strip()

    def _normalize(self, text: str) -> str:
        return re.sub(r"\W+", " ", text.lower()).strip()

    def _is_header_noise(self, text: str) -> bool:
        return bool(EMAIL_PATTERN.search(text) or PHONE_PATTERN.search(text) or URL_PATTERN.search(text))
