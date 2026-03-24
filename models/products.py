from datetime import datetime
from dataclasses import dataclass

@dataclass
class Products:
    product_name: str
    product_description: str
    category: str
    price: float
    qty: int
    weight: float
    created_at: datetime
    barcode:str