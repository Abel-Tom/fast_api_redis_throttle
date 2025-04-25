import random

import asyncio
import httpx

BASE_URL = "http://localhost:8000"
PRODUCT_ID = None
NUM_REQUESTS = 25

PRODUCT_NAMES = ["Backpack", "Headphones", "Coffee Mug", "Notebook", "Desk Lamp", "Wireless Mouse"]
ADJECTIVES = ["Stylish", "Compact", "Durable", "Sleek", "Modern", "Classic"]
USES = ["perfect for everyday use", "ideal for students", "great for office setups", "a must-have at home", "designed for comfort", "engineered for efficiency"]

async def create_product():
    random_name = f"{random.choice(ADJECTIVES)} {random.choice(PRODUCT_NAMES)}"
    random_description = f"A {random_name.lower()} that's {random.choice(USES)}."
    random_price = round(random.uniform(3, 100), 2)

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/products", json={
            "name": random_name,
            "description": random_description,
            "price": random_price
        })
        return response.json()["id"]

async def increment_view(num):
    print('request id ', num)
    # async with httpx.AsyncClient(timeout=10.0) as client:
    #     resp = await client.post(f"{BASE_URL}/products/{PRODUCT_ID}/increment_views")
    #     print(resp.json())

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{BASE_URL}/products/{PRODUCT_ID}/increment_views")
            resp.raise_for_status()
            # print(resp.json())
    except httpx.HTTPStatusError as e:
        print(f"Server error: {e.response.status_code}")
        print(e.response.text, ' request id ', num) 

async def get_views():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/products/{PRODUCT_ID}")
        return int(response.json().get("views", 0))

async def main():
    global PRODUCT_ID
    PRODUCT_ID = await create_product()

    # Ensure view count starts at 0
    print(f"Created Product ID: {PRODUCT_ID}")

    # Run concurrent increment requests
    tasks = [increment_view(_) for _ in range(NUM_REQUESTS)]
    await asyncio.gather(*tasks)

    # Retrieve the final view count
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/products/{PRODUCT_ID}/increment_views")
        print("Final view count:", response.json())

if __name__ == "__main__":
    asyncio.run(main())
