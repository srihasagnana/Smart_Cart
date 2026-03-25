from fastapi import APIRouter
from db.connection import Mysql

router = APIRouter(prefix="/order", tags=["Order"])

@router.post("/checkout")
def checkout(user_id: int):
    db = Mysql()

    # get cart items
    items = db.fetch_all("""
        SELECT c.product_id, c.qty, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s
    """, (user_id,))

    if not items:
        return {"message": "Cart is empty"}

    # calculate total
    total = sum(i["qty"] * i["price"] for i in items)

    # create order
    db.execute("""
        INSERT INTO orders (user_id, total_amount)
        VALUES (%s, %s)
    """, (user_id, total))

    order_id = db.last_insert_id()

    # insert order items
    for i in items:
        db.execute("""
            INSERT INTO order_items (order_id, product_id, qty, price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, i["product_id"], i["qty"], i["price"]))

    # clear cart
    db.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))

    return {"message": "Order placed", "order_id": order_id}