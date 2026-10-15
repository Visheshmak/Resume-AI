from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.services.job_queue import get_local_job
from app.workers.analysis_worker import process_analysis_job

logger = logging.getLogger("resumeiq.worker")


async def run() -> None:
    if not settings.redis_url:
        while True:
            await process_analysis_job(await get_local_job())
    else:
        from redis.asyncio import Redis

        client = Redis.from_url(settings.redis_url, decode_responses=True)
        try:
            while True:
                _, job_id = await client.blpop("resumeiq:analysis", timeout=0)
                await process_analysis_job(job_id)
        finally:
            await client.aclose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())