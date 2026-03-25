from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    user_id: int
    name: str
    phone: str
    created_at: datetime