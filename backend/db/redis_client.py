"""
NBA Enterprise AI Platform — Redis Async Client
Used for session cache, rate limiting, job queues, and
embedding cache.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

_redis_client: Optional[Redis] = None


async def init_redis() -> Redis:
    """Initialise and return the Redis connection pool."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    _redis_client = aioredis.from_url(
        settings.db.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=50,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )
    await _redis_client.ping()
    logger.info("Redis connected")
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis disconnected")


def get_redis() -> Redis:
    """FastAPI dependency: return the active Redis client."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialised. Call init_redis() first.")
    return _redis_client


# ----------------------------------------------------------------
# Cache helpers
# ----------------------------------------------------------------

async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Serialise value to JSON and store with TTL (seconds)."""
    client = get_redis()
    await client.setex(key, ttl, json.dumps(value))


async def cache_get(key: str) -> Optional[Any]:
    """Retrieve and deserialise a cached value. Returns None on miss."""
    client = get_redis()
    raw = await client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_delete(key: str) -> None:
    client = get_redis()
    await client.delete(key)


async def cache_delete_pattern(pattern: str) -> int:
    """Delete all keys matching a glob pattern. Returns count deleted."""
    client = get_redis()
    keys = await client.keys(pattern)
    if not keys:
        return 0
    return await client.delete(*keys)


# ----------------------------------------------------------------
# Rate limiting helpers
# ----------------------------------------------------------------

async def rate_limit_check(identifier: str, limit: int, window_seconds: int) -> bool:
    """
    Sliding-window rate limit check.
    Returns True if the request is allowed, False if rate-limited.
    """
    client = get_redis()
    key = f"rate_limit:{identifier}"
    pipe = client.pipeline()
    await pipe.incr(key)
    await pipe.expire(key, window_seconds)
    results = await pipe.execute()
    count = results[0]
    return count <= limit


# ----------------------------------------------------------------
# Session helpers
# ----------------------------------------------------------------

async def session_set(session_id: str, data: dict, ttl: int = 3600) -> None:
    await cache_set(f"session:{session_id}", data, ttl)


async def session_get(session_id: str) -> Optional[dict]:
    return await cache_get(f"session:{session_id}")


async def session_delete(session_id: str) -> None:
    await cache_delete(f"session:{session_id}")
