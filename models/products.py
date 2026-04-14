from pydantic import BaseModel
from typing import List, Optional


class Products(BaseModel):
    product_name: str
    product_description: str
    category: str
    price: float
    qty: int
    weights: List[float]
    barcode: str
    image: Optional[str] = None