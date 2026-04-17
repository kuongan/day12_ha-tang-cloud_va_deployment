"""Per-user monthly budget checks backed by Redis."""
from datetime import datetime, timezone

from fastapi import HTTPException

from app.config import settings
from app.storage import get_redis_client

PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
    output_cost = (output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
    return round(input_cost + output_cost, 6)


def _month_key(user_id: str) -> str:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    return f"budget:{user_id}:{month}"


def check_budget(user_id: str, estimated_cost_usd: float) -> None:
    redis_client = get_redis_client()
    if not redis_client:
        return

    key = _month_key(user_id)
    current = float(redis_client.get(key) or 0.0)
    if current + estimated_cost_usd > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Monthly budget exceeded",
                "used_usd": round(current, 4),
                "estimated_next_usd": round(estimated_cost_usd, 4),
                "budget_usd": settings.monthly_budget_usd,
            },
        )


def record_usage(user_id: str, input_tokens: int, output_tokens: int) -> float:
    cost = estimate_cost_usd(input_tokens, output_tokens)
    redis_client = get_redis_client()
    if not redis_client:
        return cost

    key = _month_key(user_id)
    new_total = redis_client.incrbyfloat(key, cost)
    # Keep one year; key name separates months already.
    redis_client.expire(key, 366 * 24 * 3600)
    return float(new_total)
