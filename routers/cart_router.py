from fastapi import APIRouter, HTTPException
from db.connection import Mysql
from repositiories.cart_repo import CartRepo
import math

router = APIRouter()
db = Mysql()


@router.post("/cart")
def add_to_cart(user_id: int, product_id: int, qty: int, weight: float):
    db = Mysql()

    # Get product weight range
    product = db.fetchone("""
        SELECT weight, min_weight, max_weight, product_name FROM products 
        WHERE product_id=%s
    """, (product_id,))

    if not product:
        return {"error": "Product not found"}

    avg_weight = float(product[0])
    min_weight = float(product[1]) if product[1] else avg_weight * 0.9
    max_weight = float(product[2]) if product[2] else avg_weight * 1.1
    product_name = product[3]

    # weight here is the DIFFERENCE (delta), not total weight
    if weight > 0 and avg_weight > 0:
        diff_percent = abs(weight - avg_weight) / avg_weight * 100

        # Check if the weight DIFFERENCE matches the product
        if weight < min_weight or weight > max_weight:
            return {
                "error": "INVALID_WEIGHT",
                "expected_min": min_weight,
                "expected_max": max_weight,
                "expected_avg": avg_weight,
                "detected": weight,
                "difference_percent": round(diff_percent, 1),
                "message": f"Weight mismatch! Expected ~{avg_weight:.0f}g (±{((max_weight - min_weight) / 2):.0f}g), got {weight:.1f}g ({diff_percent:.1f}% off)"
            }

    repo = CartRepo(db)
    repo.add_to_cart(user_id, product_id, qty, weight)

    return {
        "message": "Added to cart",
        "product_name": product_name,
        "weight_verified": True,
        "detected_weight": weight,
        "expected_weight": avg_weight
    }


@router.get("/cart")
def view_cart(user_id: int):
    db = Mysql()
    repo = CartRepo(db)
    data = repo.get_cart(user_id)
    return data


@router.get("/cart/total-weight")
def get_cart_total_weight(user_id: int):
    """Get total weight of all items in cart"""
    rows = db.fetchall("""
        SELECT SUM(weight * qty)
        FROM cart
        WHERE user_id = %s
    """, (user_id,))

    total_weight = rows[0][0] if rows[0][0] else 0
    return {"total_weight": total_weight}


@router.delete("/cart/{cart_id}")
def delete_cart_item(cart_id: int, barcode: str = None):
    # Get item to delete
    item = db.fetchone("""
        SELECT c.product_id, p.weight, p.barcode, c.user_id, c.weight, c.qty
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.cart_id = %s
    """, (cart_id,))

    if not item:
        return {"error": "Item not found"}

    product_id, weight, real_barcode, user_id, cart_weight, qty = item

    # Check same weight items for this user
    same_weight = db.fetchall("""
        SELECT COUNT(*)
        FROM cart c
        WHERE c.user_id = %s
        AND c.weight = %s
        AND c.cart_id != %s
    """, (user_id, cart_weight, cart_id))

    count = same_weight[0][0] if same_weight else 0

    # If more than 1 → require barcode
    if count > 0:
        if not barcode:
            return {"error": "SCAN_REQUIRED"}

        # Get product barcode
        product = db.fetchone("SELECT barcode FROM products WHERE product_id = %s", (product_id,))
        if barcode != product[0]:
            return {"error": "WRONG_ITEM"}

    # Delete
    db.execute(
        "DELETE FROM cart WHERE cart_id = %s",
        (cart_id,),
        commit=True
    )

    return {"message": "Item removed", "removed_weight": cart_weight * qty}


@router.get("/cart/total")
def get_cart_total(user_id: int):
    rows = db.fetchall("""
        SELECT p.price, c.qty
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s
    """, (user_id,))

    total = 0
    for r in rows:
        price = float(r[0])
        qty = int(r[1])
        total += price * qty

    return {"total": total}


@router.post("/checkout")
def checkout(user_id: int, payment_method: str = "cash"):
    # Get total
    total = db.fetchone("""
        SELECT SUM(p.price * c.qty)
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s
    """, (user_id,))[0] or 0

    # Create order with payment method
    db.execute(
        "INSERT INTO orders (user_id, total_amount, payment_method) VALUES (%s, %s, %s)",
        (user_id, total, payment_method),
        commit=True
    )

    order_id = db.fetchone("SELECT LAST_INSERT_ID()")[0]

    # Move cart → order_items
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

    # Clear cart
    db.execute("DELETE FROM cart WHERE user_id = %s", (user_id,), commit=True)

    return {"message": "Order placed", "order_id": order_id, "total": total}


@router.get("/cart/total-weight")
def get_cart_total_weight(user_id: int):
    """Get total weight of all items in cart"""
    try:
        rows = db.fetchall("""
            SELECT c.weight, c.qty
            FROM cart c
            WHERE c.user_id = %s
        """, (user_id,))

        total_weight = 0
        for row in rows:
            weight = float(row[0]) if row[0] else 0
            qty = int(row[1]) if row[1] else 0
            total_weight += weight * qty

        print(f"DEBUG - Cart total weight for user {user_id}: {total_weight}g")  # Debug
        return {"total_weight": total_weight}
    except Exception as e:
        print(f"Error calculating total weight: {e}")
        return {"total_weight": 0}