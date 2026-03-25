from fastapi import APIRouter
from db.connection import Mysql

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/create")
def create_user(name: str, phone: str):
    db = Mysql()

    # insert or update
    db.execute("""
        INSERT INTO users (name, phone)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE name = VALUES(name)
    """, (name, phone),commit=True)

    # get user_id
    user = db.fetchone("""
        SELECT user_id FROM users WHERE phone = %s
    """, (phone,))

    return {"user_id": user[0]}