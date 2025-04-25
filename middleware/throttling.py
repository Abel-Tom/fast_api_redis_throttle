# middleware/throttling.py

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis.asyncio as redis

# Redis client
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Configuration for throttling
THROTTLE_LIMITS = {
    "ip": (100, 60),            # 100 requests per minute
    "region": (1000, 3600),     # 1000 requests per hour
    "customer": (500, 3600),    # 500 requests per hour
}

# Helper function to check and apply rate limits
async def check_rate_limit(identifier: str, limit: int, window: int):
    key = f"rate_limit:{identifier}"
    current = await redis_client.incr(key)
    if current == 1:
        await redis_client.expire(key, window)
    if current > limit:
        retry_after = await redis_client.ttl(key)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds."
        )

# Middleware function
async def throttle_middleware(request: Request, call_next):
    ip = request.client.host
    region = request.headers.get("X-Client-Region", "default")
    customer = request.headers.get("X-Customer-ID")

    try:
        await check_rate_limit(f"ip:{ip}", *THROTTLE_LIMITS["ip"])
        await check_rate_limit(f"region:{region}", *THROTTLE_LIMITS["region"])
        if customer:
            await check_rate_limit(f"customer:{customer}", *THROTTLE_LIMITS["customer"])
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

    response = await call_next(request)
    return response
