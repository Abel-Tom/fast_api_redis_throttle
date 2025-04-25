import uuid
import asyncio
from fastapi import APIRouter, HTTPException
from models import Product
import redis.asyncio as redis
from redis.exceptions import WatchError

router = APIRouter()
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)


@router.get("/products")
async def get_all_products():
    keys = await redis_client.keys("product:*")
    product_ids = [k for k in keys if not k.endswith(":views")]

    products = []
    for key in product_ids:
        product_id = key.split(":")[1]
        data = await redis_client.hgetall(key)
        products.append({"id": product_id, **data})

    return products


@router.post("/products")
async def create_product(product: Product):
    product_id = str(uuid.uuid4())
    await redis_client.hset(f"product:{product_id}", mapping=product.dict())
    return {"id": product_id, **product.dict()}

@router.get("/products/{product_id}")
async def get_product(product_id: str):
    product = await redis_client.hgetall(f"product:{product_id}")
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"id": product_id, **product}

@router.put("/products/{product_id}")
async def update_product(product_id: str, product: Product):
    exists = await redis_client.exists(f"product:{product_id}")
    if not exists:
        raise HTTPException(status_code=404, detail="Product not found")
    await redis_client.hset(f"product:{product_id}", mapping=product.dict())
    return {"id": product_id, **product.dict()}

@router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    await redis_client.delete(f"product:{product_id}")
    return {"status": "deleted"}

# Endpoint to increment a product view counter with race condition protection
@router.post("/products/{product_id}/increment_views")
async def increment_views(product_id: str):
    key = f"product:{product_id}:views"
    for _ in range(15):  # Retry up to 5 times
        try:
            async with redis_client.pipeline() as pipe:
                await pipe.watch(key)
                # time.sleep(5)
                current = await pipe.get(key)
                print('current ', current)
                new_val = int(current or 0) + 1
                pipe.multi()
                pipe.set(key, new_val)
                await pipe.execute()
                return {"views": new_val}
        except WatchError:
            await asyncio.sleep(0.1)
            continue
    raise HTTPException(status_code=500, detail="Could not update view count due to high contention")