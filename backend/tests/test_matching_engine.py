from app.jd.engine import JobDescriptionIntelligenceEngine
from app.matching.engine import ResumeJDMatcher
from app.resume.engine import ResumeIntelligenceEngine
from tests.test_resume_engine import make_pdf


def resume_from_lines(lines: list[str]):
    extraction, _ = ResumeIntelligenceEngine().parse_bytes(make_pdf(lines), "pdf")
    return extraction


def test_strong_match_has_exact_evidence_and_transparent_scores() -> None:
    resume = resume_from_lines([
        "Taylor Morgan",
        "EXPERIENCE",
        "Backend Engineer | Acme | 2022 - Present",
        "- Built FastAPI services with Python and PostgreSQL for 10,000 users.",
        "SKILLS",
        "Python, FastAPI, PostgreSQL, AWS, Docker",
        "EDUCATION",
        "B.S. Computer Science, State University, 2021",
    ])
    job = JobDescriptionIntelligenceEngine().parse("Backend Engineer at Acme\nRequired skills: Python, FastAPI, PostgreSQL\nPreferred: AWS and Docker\nResponsibilities\n- Build RESTful backend services.")

    report = ResumeJDMatcher().match(resume, job)

    assert report.overall_match > 50
    assert {item.skill for item in report.matched_skills} >= {"Python", "FastAPI", "PostgreSQL", "AWS", "Docker"}
    assert all(item.resume_evidence for item in report.matched_skills)
    assert any(score.category == "Required Skills" and score.matched == 3 for score in report.scores)


def test_partial_match_keeps_missing_skill_missing() -> None:
    resume = resume_from_lines(["Taylor Morgan", "EXPERIENCE", "Backend Engineer | Acme | 2022 - Present", "- Built Python services with Flask.", "SKILLS", "Python, Flask, Docker"])
    job = JobDescriptionIntelligenceEngine().parse("Backend Engineer\nRequired skills: Python, FastAPI, Kubernetes\nResponsibilities\n- Build RESTful backend services.")

    report = ResumeJDMatcher().match(resume, job)

    missing = {item.skill for item in report.missing_skills}
    partial = {item.skill for item in report.partial_matches}
    assert "Kubernetes" not in {item.skill for item in report.matched_skills}
    assert "Kubernetes" in missing | partial
    assert "FastAPI" in partial
    assert "FastAPI" not in missing
    assert all(item.resume_evidence for item in report.partial_matches)


def test_unrelated_resume_does_not_hallucinate_skills() -> None:
    resume = resume_from_lines(["Morgan Lee", "EXPERIENCE", "Office Coordinator", "- Coordinated schedules and welcomed visitors.", "EDUCATION", "High School Diploma, 2020"])
    job = JobDescriptionIntelligenceEngine().parse("Data Engineer\nRequired skills: Python, Spark, AWS\nQualifications\n- Bachelor's degree in Computer Science.")

    report = ResumeJDMatcher().match(resume, job)

    assert {item.skill for item in report.missing_skills} >= {"Python", "Spark", "AWS"}
    assert not report.matched_skills


def test_concept_match_is_not_specific_skill_match() -> None:
    resume = resume_from_lines(["Taylor Morgan", "EXPERIENCE", "Backend Engineer", "- Developed APIs using Flask.", "SKILLS", "Python, Flask"])
    job = JobDescriptionIntelligenceEngine().parse("Backend Engineer\nRequired skills: FastAPI\nResponsibilities\n- Build RESTful backend services.")

    report = ResumeJDMatcher().match(resume, job)

    fastapi = next(item for item in report.partial_matches if item.skill == "FastAPI")
    assert fastapi.status == "partial"
    assert "specific technology" in fastapi.explanation
