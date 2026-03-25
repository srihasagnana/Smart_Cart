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

    # get products in user's cart
    cart_items = db.fetchall(
        "SELECT product_id FROM cart WHERE user_id = %s",
        (user_id,)
    )

    if not cart_items:
        return {"recommended_products": []}

    # take product_ids
    product_ids = [item[0] for item in cart_items]

    # collect recommendations
    recommendations = set()

    for pid in product_ids:
        recs = recommend_products(pid)
        recommendations.update(recs)

    return {
        "recommended_products": list(recommendations)
    }