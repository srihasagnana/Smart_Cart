from fastapi import APIRouter
from db.connection import Mysql

router = APIRouter(prefix="/order", tags=["Order"])



# ============================
# ORDER HISTORY
# ============================
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
            (oi.qty * oi.price) AS item_total
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC
    """, (user_id,))

    if not rows:
        return []

    orders = {}

    for r in rows:
        order_id = r[0]

        # Create order if not exists
        if order_id not in orders:
            orders[order_id] = {
                "order_id": order_id,
                "created_at": str(r[1]),
                "items": [],
                "total_amount": 0
            }

        item_total = float(r[5])

        # Add item
        orders[order_id]["items"].append({
            "product_name": r[2],
            "quantity": r[3],
            "price": float(r[4]),
            "total": item_total
        })

        # Add to order total
        orders[order_id]["total_amount"] += item_total

    return list(orders.values())


@router.post("/create-bill")
def create_bill(user_id: int):
    db = Mysql()

    items = db.fetchall("""
        SELECT c.product_id, c.qty, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s
    """, (user_id,))

    if not items:
        return {"message": "Cart is empty"}

    total = sum(i[1] * i[2] for i in items)

    return {
        "total_amount": total,
        "message": "Proceed to payment"
    }

@router.post("/confirm-payment")
def confirm_payment(user_id: int, payment_method: str = "upi"):
    db = Mysql()

    items = db.fetchall("""
        SELECT c.product_id, c.qty, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s
    """, (user_id,))

    if not items:
        return {"message": "Cart is empty"}

    total = sum(i[1] * i[2] for i in items)

    db.execute("""
        INSERT INTO orders (user_id, total_amount, payment_method)
        VALUES (%s, %s, %s)
    """, (user_id, total, payment_method), commit=True)

    order_id = db.fetchone("SELECT LAST_INSERT_ID()")[0]

    for i in items:
        db.execute("""
            INSERT INTO order_items (order_id, product_id, qty, price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, i[0], i[1], i[2]), commit=True)

    db.execute("DELETE FROM cart WHERE user_id=%s", (user_id,), commit=True)

    return {
        "order_id": order_id,
        "total_amount": total
    }

import razorpay

@router.post("/create-razorpay-order")
def create_razorpay_order(user_id: int):
    db = Mysql()

    items = db.fetchall("""
        SELECT c.product_id, c.qty, p.price
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s
    """, (user_id,))

    if not items:
        return {"error": "Cart is empty"}

    total = sum(i[1] * i[2] for i in items)

    import razorpay
    client = razorpay.Client(auth=("rzp_test_ScUj55hZVBL9QE", "lUCyyYkocDTlfNLWNbkEozVj"))

    order = client.order.create({
        "amount": int(total * 100),
        "currency": "INR",
        "payment_capture": 1
    })

    return {
        "order_id": order["id"],
        "amount": total
    }

@router.get("/receipt/{order_id}")
def get_receipt(order_id: int):
    db = Mysql()

    rows = db.fetchall("""
        SELECT 
            o.order_id,
            o.created_at,
            o.total_amount,
            p.product_name,
            oi.qty,
            oi.price,
            (oi.qty * oi.price) AS item_total
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE o.order_id = %s
    """, (order_id,))

    if not rows:
        return {"error": "No receipt found"}

    receipt = {
        "order_id": rows[0][0],
        "date": str(rows[0][1]),
        "total_amount": float(rows[0][2]),
        "items": []
    }

    for r in rows:
        receipt["items"].append({
            "product_name": r[3],
            "qty": r[4],
            "price": float(r[5]),
            "total": float(r[6])
        })

    return receipt

