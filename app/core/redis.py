import redis.asyncio as aioredis

from app.core.config import get_settings

_redis_client: aioredis.Redis | None = None


async def init_redis() -> None:
    global _redis_client
    settings = get_settings()
    _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    if _redis_client:
        await _redis_client.aclose()


def get_redis() -> aioredis.Redis | None:
    return _redis_client
