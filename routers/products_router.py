from typing import Optional

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
    weight: float,
    barcode: str
):
    repo = ProductsRepo(db)

    p = Products(
        product_name,
        product_description,
        category,
        price,
        qty,
        weight,
        datetime.now(),
        barcode
    )

    repo.insert_product(p)

    return {"message": "Product inserted"}

@router.put("/product/{product_id}/quantity")
def update_quantity(product_id: int, qty: int):
    repo = ProductsRepo(db)
    repo.update_quantity(product_id, qty)
    return {"message": "Quantity updated"}

@router.get("/product/barcode/{barcode}")
def get_product_by_barcode(barcode: str):
    db = Mysql()

    query = "SELECT * FROM products WHERE barcode = %s"
    result = db.fetchone(query, (barcode,))

    if not result:
        return {"error": "Product not found"}

    return {
        "product_id": result[0],
        "product_name": result[1],
        "price": result[4],
        "barcode": result[8]
    }