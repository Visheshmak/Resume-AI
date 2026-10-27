import io
from pathlib import Path

import pytest
from docx import Document

from tests.conftest import make_pdf_bytes


@pytest.mark.asyncio
async def test_authentication_and_logout(client, registered_user, auth_headers):
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["email"] == "jordan@example.com"

    logout = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout.status_code == 200
    assert (await client.get("/api/v1/auth/me", headers=auth_headers)).status_code == 401


@pytest.mark.asyncio
async def test_auth_invalid_requests(client):
    invalid = await client.post("/api/v1/auth/register", json={"email": "bad", "full_name": "", "password": "short"})
    assert invalid.status_code == 422

    missing = await client.get("/api/v1/auth/me")
    assert missing.status_code == 401


@pytest.mark.asyncio
async def test_resume_upload_job_analysis_and_dashboard(client, auth_headers):
    pdf = await client.post(
        "/api/v1/resumes/upload",
        headers=auth_headers,
        files={"file": ("resume.pdf", make_pdf_bytes(), "application/pdf")},
    )
    assert pdf.status_code == 201
    resume = pdf.json()
    assert resume["file_type"] == "pdf"
    detail = await client.get(f"/api/v1/resumes/{resume['id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["extraction"]["document_signals"]["page_count"] == 1

    job = await client.post("/api/v1/jobs", headers=auth_headers, json={"title": "Backend Engineer", "raw_text": "Build reliable Python services with FastAPI and PostgreSQL."})
    assert job.status_code == 201

    analysis = await client.post("/api/v1/analysis", headers=auth_headers, json={"resume_id": resume["id"], "job_description_id": job.json()["id"]})
    assert analysis.status_code == 202
    assert analysis.json()["status"] in {"queued", "completed"}

    completed = await client.get(f"/api/v1/analysis/{analysis.json()['id']}", headers=auth_headers)
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["score_summary"]["overall_match"] >= 0

    evidence = await client.get(f"/api/v1/analysis/{analysis.json()['id']}/evidence", headers=auth_headers)
    assert evidence.status_code == 200
    assert evidence.json()

    dashboard = await client.get("/api/v1/dashboard/overview", headers=auth_headers)
    assert dashboard.status_code == 200
    assert dashboard.json() == {"resume_count": 1, "job_count": 1, "analysis_count": 1, "completed_analysis_count": 1}


@pytest.mark.asyncio
async def test_file_validation_and_authorization(client, auth_headers):
    unsupported = await client.post("/api/v1/resumes/upload", headers=auth_headers, files={"file": ("resume.txt", b"plain text", "text/plain")})
    assert unsupported.status_code == 415

    corrupt_pdf = await client.post("/api/v1/resumes/upload", headers=auth_headers, files={"file": ("resume.pdf", b"not a pdf", "application/pdf")})
    assert corrupt_pdf.status_code == 400

    docx_content = io.BytesIO()
    document = Document()
    document.add_paragraph("Jordan Doe")
    document.save(docx_content)
    valid_docx = await client.post("/api/v1/resumes/upload", headers=auth_headers, files={"file": ("resume.docx", docx_content.getvalue(), "application/octet-stream")})
    assert valid_docx.status_code == 201

    other_user = await client.post("/api/v1/auth/register", json={"email": "other@example.com", "full_name": "Other User", "password": "correct-horse-battery"})
    assert other_user.status_code == 201
    other_login = await client.post("/api/v1/auth/login", json={"email": "other@example.com", "password": "correct-horse-battery"})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    hidden = await client.get(f"/api/v1/resumes/{valid_docx.json()['id']}", headers=other_headers)
    assert hidden.status_code == 404


@pytest.mark.asyncio
async def test_malformed_pdf_is_rejected_and_not_stored(client, auth_headers, tmp_path):
    from app.core.config import settings

    response = await client.post(
        "/api/v1/resumes/upload",
        headers=auth_headers,
        files={"file": ("resume.pdf", b"%PDF-not actually a PDF", "application/pdf")},
    )
    assert response.status_code == 422
    assert not [path for path in Path(settings.upload_dir).rglob("*") if path.is_file()]
