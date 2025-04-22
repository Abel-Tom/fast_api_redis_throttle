import asyncio
import pytest
import httpx

BASE_URL = "http://localhost:8000"
HEADERS = {
    "X-Client-Region": "US",
    "X-Customer-ID": "cust123"
}

@pytest.mark.asyncio
async def test_full_product_flow():
    async with httpx.AsyncClient(headers=HEADERS) as client:

        # Create product
        create_resp = await client.post(f"{BASE_URL}/products", json={
            "name": "Test Item",
            "description": "A product for testing.",
            "price": 29.99
        })
        assert create_resp.status_code == 200
        product = create_resp.json()
        product_id = product["id"]

        # Get product
        get_resp = await client.get(f"{BASE_URL}/products/{product_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Test Item"

        # Update product
        update_resp = await client.put(f"{BASE_URL}/products/{product_id}", json={
            "name": "Updated Test Item",
            "description": "Updated description",
            "price": 39.99
        })
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated Test Item"

        # Increment views multiple times
        for _ in range(5):
            inc_resp = await client.post(f"{BASE_URL}/products/{product_id}/increment_views")
            assert inc_resp.status_code == 200

        # Get updated views
        views_resp = await client.post(f"{BASE_URL}/products/{product_id}/increment_views")
        assert views_resp.status_code == 200
        assert views_resp.json()["views"] == 6

        # Trigger background processing
        bg_resp = await client.post(f"{BASE_URL}/process_data/{product_id}", json={
            "name": "Background Processed Product",
            "description": "Handled in background",
            "price": 49.99
        })
        assert bg_resp.status_code == 202
        assert bg_resp.json()["status"] == "Processing started"

        # Wait for background thread to finish
        await asyncio.sleep(6)

        # Confirm product was updated by background thread
        post_process_resp = await client.get(f"{BASE_URL}/products/{product_id}")
        assert post_process_resp.status_code == 200
        assert post_process_resp.json()["name"] == "Background Processed Product"

        # Delete product
        delete_resp = await client.delete(f"{BASE_URL}/products/{product_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["status"] == "deleted"

        # Verify deletion
        get_after_delete = await client.get(f"{BASE_URL}/products/{product_id}")
        assert get_after_delete.status_code == 404
