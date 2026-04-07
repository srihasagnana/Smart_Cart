from typing import Optional

from fastapi import APIRouter
from db.connection import Mysql
from seed_data.products import SeedData
from repositiories.products_repo import ProductsRepo
from models.products import Products
from datetime import datetime
from serial_reader import get_weight

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
def add_product(data: Products):
    repo = ProductsRepo(db)

    if len(data.weights) < 5:
        return {"error": "Minimum 5 weights required"}

    min_w = min(data.weights)
    max_w = max(data.weights)

    # optional tolerance
    min_w -= 2
    max_w += 2

    avg_weight = sum(data.weights) / len(data.weights)

    query = """
        INSERT INTO products 
        (product_name, product_description, category, price, qty, weight, created_at, barcode)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    product_id = db.execute(query, (
        data.product_name,
        data.product_description,
        data.category,
        data.price,
        data.qty,
        avg_weight,
        datetime.now(),
        data.barcode
    ), commit=True)


    db.execute("""
        UPDATE products 
        SET min_weight=%s, max_weight=%s 
        WHERE product_id=%s
    """, (min_w, max_w, product_id),commit=True)

    return {
        "message": "Product inserted",
        "min_weight": min_w,
        "max_weight": max_w
    }

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
        "barcode": result[8],
        "weight": result[6],
    }

@router.get("/weight")
def read_weight():
    weight = get_weight()

    if weight is None:
        return {"error": "No weight"}

    return {"weight": weight}