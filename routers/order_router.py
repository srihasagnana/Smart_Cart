from fastapi import APIRouter
from db.connection import Mysql

router = APIRouter(prefix="/order", tags=["Order"])


@router.post("/checkout")
def checkout(user_id: int):
    db = Mysql()

    # get cart items
    items = db.fetchall("""
        SELECT c.product_id, c.qty, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s
    """, (user_id,))

    if not items:
        return {"message": "Cart is empty"}

    # calculate total
    total = sum(i[1] * i[2] for i in items)

    # create order
    db.execute("""
        INSERT INTO orders (user_id, total_amount)
        VALUES (%s, %s)
    """, (user_id, total),commit=True)

    order_id = db.fetchone("SELECT LAST_INSERT_ID()")[0]

    # insert order items
    for i in items:
        db.execute("""
            INSERT INTO order_items (order_id, product_id, qty, price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, i[0], i[1], i[2]),commit=True)

    # clear cart
    db.execute("DELETE FROM cart WHERE user_id = %s", (user_id,),commit=True)

    return {"message": "Order placed", "order_id": order_id}


@router.get("/orders/{user_id}")

def get_order_history(user_id: int):
    db = Mysql()
    rows = db.fetchall("""
        SELECT 
            o.order_id,
            o.created_at,
            p.product_name,
            oi.qty,
            oi.price,
            (oi.qty * oi.price) AS total
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC
    """, (user_id,))

    return [
        {
            "order_id": r[0],
            "date": str(r[1]),
            "product_name": r[2],
            "quantity": r[3],
            "price": float(r[4]),
            "total": float(r[5])
        }
        for r in rows
    ]