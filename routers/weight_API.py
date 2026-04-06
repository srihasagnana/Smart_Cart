from fastapi import APIRouter
from db.connection import Mysql

router = APIRouter()

@router.post("/set-weight-range")
def set_weight_range(product_id: int, weights: list[float]):
    db = Mysql()

    if len(weights) < 5:
        return {"error": "Give at least 5 weights"}

    min_w = min(weights)
    max_w = max(weights)

    db.execute("""
        UPDATE products 
        SET min_weight=%s, max_weight=%s 
        WHERE product_id=%s
    """, (min_w, max_w, product_id), commit=True)

    return {
        "msg": "Weight range set",
        "min": min_w,
        "max": max_w
    }

@router.post("/check-weight")
def check_weight(product_id: int, weight: float):
    db = Mysql()

    product = db.fetchone("""
        SELECT min_weight, max_weight 
        FROM products 
        WHERE product_id=%s
    """, (product_id,))

    if not product:
        return {"error": "Product not found"}

    min_w = product[0]
    max_w = product[1]

    if min_w <= weight <= max_w:
        return {"status": "valid"}
    else:
        return {"status": "invalid"}