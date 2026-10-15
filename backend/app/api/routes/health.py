from fastapi import APIRouter

from app.core.config import settings
from app.db.session import engine

router = APIRouter()


@router.get("/ready")
async def readiness() -> dict[str, str]:
    database = "ok"
    try:
        async with engine.connect() as connection:
            await connection.exec_driver_sql("SELECT 1")
    except Exception:
        database = "unavailable"
    redis = "not_configured"
    if settings.redis_url:
        try:
            from redis.asyncio import Redis

            client = Redis.from_url(settings.redis_url)
            try:
                await client.ping()
            finally:
                await client.aclose()
            redis = "ok"
        except Exception:
            redis = "unavailable"
    return {"status": "ready" if database == "ok" and redis != "unavailable" else "degraded", "database": database, "redis": redis}
