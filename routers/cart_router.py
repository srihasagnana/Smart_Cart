from fastapi import APIRouter
from db.connection import Mysql
from repositiories.cart_repo import CartRepo

router = APIRouter()
db = Mysql()

@router.post("/cart")
def add_to_cart(user_id: int, product_id: int, qty: int):
    print("DEBUG → user_id:", user_id, "product_id:", product_id, "qty:", qty)

    # 🔥 VALIDATION (VERY IMPORTANT)
    product = db.fetchone(
        "SELECT product_id FROM products WHERE product_id = %s",
        (product_id,)
    )

    if not product:
        return {"error": f"Invalid product_id: {product_id}"}

    repo = CartRepo(db)
    repo.add_to_cart(user_id, product_id, qty)

    return {"message": "Added to cart"}


@router.get("/cart")
def view_cart(user_id: int):
    repo = CartRepo(db)
    return repo.get_cart(user_id)


@router.delete("/cart/{cart_id}")
def delete_cart_item(cart_id: int):
    repo = CartRepo(db)
    repo.delete_cart_item(cart_id)
    return {"message": "Item removed"}