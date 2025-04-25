# routes/background.py

import threading
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services.background import process_data_background

router = APIRouter()

@router.post("/process_data/{product_id}")
async def process_data(product_id: str, data: dict):
    thread = threading.Thread(target=process_data_background, args=(product_id, data))
    thread.start()
    return JSONResponse(status_code=202, content={"status": "Processing started"})
