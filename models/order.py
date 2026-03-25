from dataclasses import dataclass
from datetime import datetime

@dataclass
class Order:
    order_id: int
    user_id: int
    total_amount: float
    created_at: datetime