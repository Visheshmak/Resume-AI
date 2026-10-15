from io import BytesIO

import pytest
from httpx import ASGITransport, AsyncClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.main import app
from app.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite://"
test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


def make_pdf_bytes() -> bytes:
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=letter)
    for index, line in enumerate(["Jordan Doe", "jordan@example.com", "EXPERIENCE", "Engineer | Acme | 2022 - Present", "- Built Python services.", "SKILLS", "Python"]):
        pdf.drawString(40, 740 - index * 24, line)
    pdf.save()
    return output.getvalue()


@pytest.fixture(scope="session", autouse=True)
async def database():
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def client(tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    async with TestSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(delete(table))
        await session.commit()

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
async def registered_user(client):
    response = await client.post("/api/v1/auth/register", json={"email": "jordan@example.com", "full_name": "Jordan Doe", "password": "correct-horse-battery"})
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def auth_headers(client, registered_user):
    response = await client.post("/api/v1/auth/login", json={"email": "jordan@example.com", "password": "correct-horse-battery"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
