from __future__ import annotations

import asyncio
import logging

from app.core.config import settings

logger = logging.getLogger("resumeiq.jobs")
_local_queue: asyncio.Queue[str] = asyncio.Queue()


async def enqueue_analysis(job_id: str) -> None:
    """Publish a job to Redis when configured, with a development fallback."""
    if settings.redis_url:
        try:
            from redis.asyncio import Redis

            client = Redis.from_url(settings.redis_url, decode_responses=True)
            try:
                await client.rpush("resumeiq:analysis", job_id)
            finally:
                await client.aclose()
            return
        except Exception:
            logger.exception("Redis enqueue failed; using local fallback", extra={"job_id": job_id})
    await _local_queue.put(job_id)


async def get_local_job() -> str:
    return await _local_queue.get()