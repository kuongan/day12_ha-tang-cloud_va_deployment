"""Sliding-window rate limiting with Redis backend and memory fallback."""
import time
from collections import defaultdict, deque

from fastapi import HTTPException

from app.config import settings
from app.storage import get_redis_client

_memory_windows: dict[str, deque] = defaultdict(deque)


def check_rate_limit(user_id: str) -> None:
    now = time.time()
    window_seconds = 60
    limit = settings.rate_limit_per_minute

    redis_client = get_redis_client()
    if redis_client:
        key = f"rate:{user_id}"
        pipeline = redis_client.pipeline()
        pipeline.zremrangebyscore(key, 0, now - window_seconds)
        pipeline.zcard(key)
        _, current = pipeline.execute()

        if int(current) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limit} req/min",
                headers={"Retry-After": "60"},
            )

        pipeline = redis_client.pipeline()
        pipeline.zadd(key, {str(now): now})
        pipeline.expire(key, window_seconds + 5)
        pipeline.execute()
        return

    # Fallback for local environments without Redis.
    bucket = _memory_windows[user_id]
    while bucket and bucket[0] < now - window_seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limit} req/min",
            headers={"Retry-After": "60"},
        )
    bucket.append(now)
