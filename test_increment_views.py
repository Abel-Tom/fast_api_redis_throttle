import asyncio
import httpx

BASE_URL = "http://localhost:8000"
PRODUCT_ID = None
NUM_REQUESTS = 50

async def create_product():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/products", json={
            "name": "Race Test Product",
            "description": "Testing concurrent updates",
            "price": 9.99
        })
        return response.json()["id"]

async def increment_view():
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/products/{PRODUCT_ID}/increment_views")

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
    tasks = [increment_view() for _ in range(NUM_REQUESTS)]
    await asyncio.gather(*tasks)

    # Retrieve the final view count
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/products/{PRODUCT_ID}/increment_views")
        print("Final view count:", response.json()["views"])

if __name__ == "__main__":
    asyncio.run(main())
