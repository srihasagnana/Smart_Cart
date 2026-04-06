from pydantic import BaseModel
from typing import List

class Products(BaseModel):
    product_name: str
    product_description: str
    category: str
    price: float
    qty: int
    weights: List[float]
    barcode: str