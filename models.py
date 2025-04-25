# models.py

from pydantic import BaseModel

# Pydantic model for a simple Product
class Product(BaseModel):
    name: str
    description: str
    price: float
