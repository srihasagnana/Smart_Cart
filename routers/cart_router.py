from fastapi import APIRouter
from db.connection import Mysql
from repositiories.cart_repo import CartRepo

router = APIRouter()
db = Mysql()

@router.post("/cart")
def add_to_cart(product_id: int, qty: int):
    repo = CartRepo(db)
    repo.add_to_cart(product_id, qty)
    return {"message": "Added to cart"}

@router.get("/cart")
def view_cart():
    repo = CartRepo(db)
    return repo.get_cart()

@router.delete("/cart/{cart_id}")
def delete_cart_item(cart_id: int):
    repo = CartRepo(db)
    repo.delete_cart_item(cart_id)
    return {"message": "Item removed"}