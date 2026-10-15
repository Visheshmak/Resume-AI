from app.jd.engine import JobDescriptionIntelligenceEngine


def test_jd_parser_classifies_requirements_and_normalizes_aliases() -> None:
    job = JobDescriptionIntelligenceEngine().parse(
        "Senior Backend Engineer at Acme\n"
        "Required Qualifications\n"
        "- Python and Amazon Web Services required\n"
        "- Experience with PostgreSQL\n"
        "Preferred Qualifications\n"
        "- Kubernetes and ReactJS are a plus\n"
        "Responsibilities\n"
        "- Build RESTful backend services\n"
        "- Communicate with product and engineering teams\n"
        "Education\n"
        "- Bachelor's degree in Computer Science"
    )

    assert job.job_title == "Senior Backend Engineer"
    assert job.company == "Acme"
    assert "Python" in job.required_skills
    assert "AWS" in job.required_skills
    assert "PostgreSQL" in job.required_skills
    assert "Kubernetes" in job.preferred_skills
    assert "React" in job.preferred_skills
    assert job.responsibilities
    assert job.education_requirements
    assert all(item.evidence[0].source_type == "jd" for item in job.requirements)


def test_jd_parser_does_not_make_every_word_a_skill() -> None:
    job = JobDescriptionIntelligenceEngine().parse("Product Designer\nWe value thoughtful collaboration and user empathy.")

    assert not job.required_skills
    assert not job.preferred_skills
    assert job.soft_skills or job.domain_knowledge
