from fastapi import FastAPI

from middleware.throttling import throttle_middleware
from routes import products, background


app = FastAPI()

app.middleware("http")(throttle_middleware)

app.include_router(products.router)
app.include_router(background.router)
