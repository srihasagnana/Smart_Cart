from fastapi import APIRouter
from services.recommendation_service import recommend_products
from db.connection import Mysql

router = APIRouter()

@router.get("/recommend/{product_id}")
def get_recommendations(product_id: int):
    recommendations = recommend_products(product_id)
    return {
        "recommended_products": recommendations
    }

@router.get("/recommend/user/{user_id}")
def get_user_recommendations(user_id: int):
    db = Mysql()

    cart_items = db.fetchall(
        "SELECT product_id FROM cart WHERE user_id = %s",
        (user_id,)
    )

    if not cart_items:
        return {"recommended_products": []}

    product_ids = [item[0] for item in cart_items]

    recommendations = set()

    for pid in product_ids:
        recs = recommend_products(pid)
        recommendations.update(recs)

    if not recommendations:
        return {"recommended_products": []}

    # 🔥 FETCH FULL PRODUCT DATA HERE
    placeholders = ",".join(["%s"] * len(recommendations))

    rows = db.fetchall(
        f"""
        SELECT product_id, product_name, price
        FROM products
        WHERE product_id IN ({placeholders})
        """,
        tuple(recommendations)
    )

    # 🔥 RETURN AS DICT (NOT LIST OF LISTS)
    result = []
    for r in rows:
        result.append({
            "product_id": r[0],
            "product_name": r[1],
            "price": r[2]
        })

    return {
        "recommended_products": result
    }

from db.connection import Mysql

def recommend_products(product_id: int):
    db = Mysql()

    # Step 1: get category of selected product
    result = db.fetchone(
        "SELECT category FROM products WHERE product_id = %s",
        (product_id,)
    )

    if not result:
        return []

    category = result[0]

    # Step 2: get similar products from same category
    rows = db.fetchall(
        """
        SELECT product_id 
        FROM products 
        WHERE category = %s AND product_id != %s
        LIMIT 5
        """,
        (category, product_id)
    )

    return [r[0] for r in rows]