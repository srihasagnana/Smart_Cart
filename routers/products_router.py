from fastapi import APIRouter
from db.connection import Mysql
from seed_data.products import SeedData
from repositiories.products_repo import ProductsRepo
from models.products import Products
from datetime import datetime

router = APIRouter()

db = Mysql()


@router.get("/product/{product_id}")
def get_product(product_id: int):
    data = SeedData(db)
    return data.get_product_by_id(product_id)

@router.get("/products")
def get_all_products():
    return db.fetchall("SELECT * FROM products")

@router.post("/product")
def add_product(
    product_name: str,
    product_description: str,
    category: str,
    price: float,
    qty: int,
    weight: float
):
    repo = ProductsRepo(db)

    p = Products(
        product_name,
        product_description,
        category,
        price,
        qty,
        weight,
        datetime.now()
    )

    repo.insert_product(p)

    return {"message": "Product inserted"}