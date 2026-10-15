import asyncio
import logging

import httpx
from httpx import ASGITransport

from app.main import app

logging.basicConfig(level=logging.DEBUG)


async def main() -> None:
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "debug194625461@example.com", "password": "correct-horse-battery"},
        )
        print("login", login.status_code, login.text)
        token = login.json()["access_token"]
        with open("data/uploads/055b5fb6-8fbe-4143-a916-564e5a0a34e2.pdf", "rb") as file:
            response = await client.post(
                "/api/v1/resumes/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("debug.pdf", file, "application/pdf")},
            )
        print("upload", response.status_code, response.text)


asyncio.run(main())
