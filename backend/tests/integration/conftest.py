import os
from uuid import uuid4

import pytest
import pytest_asyncio
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config.settings import Settings
from app.shared.jobs.redis import RedisJobStore


@pytest.fixture
def redis_integration_timeout() -> float:
    return float(os.getenv("FLUXIUM_REDIS_INTEGRATION_TIMEOUT_SECONDS", "5"))


@pytest.fixture
def redis_integration_enabled() -> None:
    if os.getenv("FLUXIUM_RUN_REDIS_INTEGRATION") != "1":
        pytest.skip("Set FLUXIUM_RUN_REDIS_INTEGRATION=1 to run Redis integration tests")


@pytest_asyncio.fixture
async def redis_job_store(redis_integration_enabled: None) -> RedisJobStore:
    settings = Settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.ping()
    except RedisError as exc:
        await client.aclose()
        pytest.skip(f"Redis is unavailable at FLUXIUM_REDIS_URL: {exc}")

    store = RedisJobStore(client, key_prefix=f"fluxium:test:readiness:{uuid4()}")
    try:
        yield store
    finally:
        keys = [key async for key in client.scan_iter(f"{store._key_prefix}:*")]
        if keys:
            await client.delete(*keys)
        await client.aclose()