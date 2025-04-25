# services/background.py

import time
import redis

def process_data_background(product_id: str, data: dict):
    print(f"[Background] Starting background processing for product {product_id}")
    time.sleep(5)  # Simulate long-running task

    # Use synchronous Redis client in threads
    redis_sync = redis.Redis(host='localhost', port=6379, decode_responses=True)

    # Update product data in Redis
    redis_sync.hset(f"product:{product_id}", mapping=data)
    print(f"[Background] Processing complete for product {product_id}")
