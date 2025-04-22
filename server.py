import threading
import uuid
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Use redis.asyncio to avoid SSL-related issues in some environments
import redis.asyncio as redis
from redis.exceptions import WatchError

app = FastAPI()

# Redis setup
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Configuration for throttling
THROTTLE_LIMITS = {
    "ip": (100, 60),            # 100 req/min
    "region": (1000, 3600),     # 1000 req/hour
    "customer": (500, 3600),    # 500 req/hour
}

# Pydantic model for a simple Product
class Product(BaseModel):
    name: str
    description: str = ""
    price: float

# Helper function for rate limiting
async def check_rate_limit(identifier: str, limit: int, window: int):
    key = f"rate_limit:{identifier}"
    current = await redis_client.incr(key)
    if current == 1:
        await redis_client.expire(key, window)
    if current > limit:
        retry_after = await redis_client.ttl(key)
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Retry after {retry_after} seconds.")

# Middleware for throttling
@app.middleware("http")
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

# CRUD endpoints for Product
@app.post("/products")
async def create_product(product: Product):
    product_id = str(uuid.uuid4())
    await redis_client.hset(f"product:{product_id}", mapping=product.dict())
    return {"id": product_id, **product.dict()}

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    product = await redis_client.hgetall(f"product:{product_id}")
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"id": product_id, **product}

@app.put("/products/{product_id}")
async def update_product(product_id: str, product: Product):
    exists = await redis_client.exists(f"product:{product_id}")
    if not exists:
        raise HTTPException(status_code=404, detail="Product not found")
    await redis_client.hset(f"product:{product_id}", mapping=product.dict())
    return {"id": product_id, **product.dict()}

@app.delete("/products/{product_id}")
async def delete_product(product_id: str):
    await redis_client.delete(f"product:{product_id}")
    return {"status": "deleted"}

# Endpoint to increment a product view counter with race condition protection
@app.post("/products/{product_id}/increment_views")
async def increment_views(product_id: str):
    key = f"product:{product_id}:views"
    for _ in range(5):  # Retry up to 5 times
        try:
            async with redis_client.pipeline() as pipe:
                await pipe.watch(key)
                current = await pipe.get(key)
                new_val = int(current or 0) + 1
                pipe.multi()
                pipe.set(key, new_val)
                await pipe.execute()
                return {"views": new_val}
        except WatchError:
            await asyncio.sleep(0.1)
            continue
    raise HTTPException(status_code=500, detail="Could not update view count due to high contention")

# Background processing thread function
def process_data_background(product_id: str, data: dict):
    print(f"[Background] Processing data for {product_id}: {data}")
    time.sleep(5)
    redis_sync = redis.Redis(host='localhost', port=6379, decode_responses=True)
    redis_sync.hset(f"product:{product_id}", mapping=data)
    print(f"[Background] Processing complete for {product_id}")

# Endpoint to trigger background processing
@app.post("/process_data/{product_id}")
async def process_data(product_id: str, data: dict):
    thread = threading.Thread(target=process_data_background, args=(product_id, data))
    thread.start()
    return JSONResponse(status_code=202, content={"status": "Processing started"})
