from fastapi import APIRouter
from db.connection import Mysql

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/create")
def create_user(name: str, phone: str):
    db = Mysql()

    # Check if user already exists
    existing = db.fetchone("SELECT user_id FROM users WHERE phone = %s", (phone,))

    if existing:
        # User exists, return their ID
        return {"user_id": existing[0]}

    # Create new user
    db.execute("""
        INSERT INTO users (name, phone)
        VALUES (%s, %s)
    """, (name, phone), commit=True)

    # Get new user ID
    user = db.fetchone("SELECT user_id FROM users WHERE phone = %s", (phone,))

    return {"user_id": user[0]}