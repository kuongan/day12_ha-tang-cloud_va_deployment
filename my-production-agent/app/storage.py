"""Shared storage helpers for Redis-backed stateless state."""
import json
import uuid
from datetime import datetime, timezone

import redis

from app.config import settings

_redis_client = None
_memory_store: dict[str, list[dict]] = {}


def get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not settings.redis_url:
        return None
    try:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception:
        _redis_client = None
        return None


def redis_ready() -> bool:
    client = get_redis_client()
    if not client:
        return False
    try:
        client.ping()
        return True
    except Exception:
        return False


def new_session_id() -> str:
    return str(uuid.uuid4())


def append_message(session_id: str, role: str, content: str) -> None:
    payload = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    client = get_redis_client()
    if client:
        key = f"history:{session_id}"
        client.rpush(key, json.dumps(payload))
        client.expire(key, settings.session_ttl_seconds)
        return

    _memory_store.setdefault(session_id, []).append(payload)


def get_history(session_id: str) -> list[dict]:
    client = get_redis_client()
    if client:
        key = f"history:{session_id}"
        return [json.loads(x) for x in client.lrange(key, 0, -1)]
    return _memory_store.get(session_id, [])
