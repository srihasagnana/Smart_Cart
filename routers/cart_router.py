from fastapi import APIRouter
from db.connection import Mysql
from repositiories.cart_repo import CartRepo

router = APIRouter()
db = Mysql()

@router.post("/cart")
def add_to_cart(user_id: int, product_id: int, qty: int, weight: float):
    db = Mysql()

    product = db.fetchone("""
        SELECT weight FROM products 
        WHERE product_id=%s
    """, (product_id,))

    if not product:
        return {"error": "Product not found"}

    avg_weight = float(product[0])

    TOLERANCE = 10

    if abs(weight - avg_weight) > TOLERANCE:
        return {"error": "INVALID_WEIGHT"}

    repo = CartRepo(db)
    repo.add_to_cart(user_id, product_id, qty,weight)

    return {"message": "Added to cart"}


@router.get("/cart")
def view_cart(user_id: int):
    db = Mysql()
    print("DEBUG USER:", user_id)   # 👈 ADD HERE

    repo = CartRepo(db)
    data = repo.get_cart(user_id)

    print("DEBUG CART DATA:", data)  # 👈 ALSO ADD THIS

    return data


@router.delete("/cart/{cart_id}")
def delete_cart_item(cart_id: int, barcode: str = None):
    # 1. Get item to delete
    item = db.fetchone("""
        SELECT c.product_id, p.weight, p.barcode
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.cart_id = %s
    """, (cart_id,))

    if not item:
        return {"error": "Item not found"}

    product_id, weight, real_barcode = item

    # 2. Check same weight items
    same_weight = db.fetchall("""
        SELECT COUNT(*)
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = (
            SELECT user_id FROM cart WHERE cart_id = %s
        )
        AND c.weight = %s
    """, (cart_id, weight))

    count = same_weight[0][0]

    # 3. If more than 1 → require barcode
    if count > 1:
        if not barcode:
            return {"error": "SCAN_REQUIRED"}

        if barcode != real_barcode:
            return {"error": "WRONG_ITEM"}

    # 4. Delete
    db.execute(
        "DELETE FROM cart WHERE cart_id = %s",
        (cart_id,),
        commit=True
    )

    return {"message": "Item removed"}


@router.get("/cart/total")
def get_cart_total(user_id: int):

    rows = db.fetchall("""
        SELECT p.price, c.qty
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s
    """, (user_id,))

    print("DEBUG ROWS:", rows)  # 🔥 add this

    total = 0

    for r in rows:
        price = float(r[0])
        qty = int(r[1])
        total += price * qty

    return {"total": total}

@router.post("/checkout")
def checkout(user_id: int, payment_method: str):
    # 1. Get total
    total = db.fetchone("""
        SELECT SUM(p.price * c.qty)
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s
    """, (user_id,))[0] or 0

    # 2. Create order
    db.execute(
        "INSERT INTO orders (user_id, total_amount) VALUES (%s, %s)",
        (user_id, total),
        commit=True
    )

    order_id = db.fetchone("SELECT LAST_INSERT_ID()")[0]

    # 3. Move cart → order_items
    items = db.fetchall("""
        SELECT product_id, qty
        FROM cart WHERE user_id = %s
    """, (user_id,))

    for item in items:
        db.execute("""
            INSERT INTO order_items (order_id, product_id, qty, price)
            SELECT %s, product_id, qty, price
            FROM products WHERE product_id = %s
        """, (order_id, item[0]), commit=True)

    # 4. Clear cart
    db.execute("DELETE FROM cart WHERE user_id = %s", (user_id,), commit=True)

    return {"message": "Order placed", "order_id": order_id}