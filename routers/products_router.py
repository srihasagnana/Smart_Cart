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
    result = db.fetchone("SELECT * FROM products WHERE product_id = %s", (product_id,))
    if result:
        return {
            "product_id": result[0],
            "product_name": result[1],
            "price": result[4],
            "qty": result[5],
            "weight": result[6],
            "min_weight": result[7],
            "max_weight": result[8],
            "barcode": result[9],
            "image": result[11]
        }
    return {"error": "Product not found"}


@router.get("/products")
def get_all_products():
    products = db.fetchall("SELECT * FROM products")

    return [
        {
            "product_id": p[0],
            "product_name": p[1],
            "product_description": p[2],
            "category": p[3],
            "price": p[4],
            "qty": p[5],
            "weight": p[6],
            "min_weight": p[7],
            "max_weight": p[8],
            "barcode": p[9],
            "created_at": p[10],
            "image": p[11]  # 👈 ADD
        }
        for p in products
    ]


@router.post("/product")
def add_product(data: Products):
    repo = ProductsRepo(db)

    if len(data.weights) < 5:
        return {"error": "Minimum 5 weights required"}

    # Calculate weight with outlier removal
    weights = sorted(data.weights)

    # Remove outliers (min and max)
    trimmed_weights = weights[2:-2] if len(weights) > 4 else weights[1:-1] if len(weights) > 2 else weights

    avg_weight = sum(trimmed_weights) / len(trimmed_weights)

    # Use 10% tolerance (more realistic)
    TOLERANCE_PERCENTAGE = 0.10  # 10% tolerance
    TOLERANCE_GRAMS = max(avg_weight * TOLERANCE_PERCENTAGE, 10)  # At least 10g

    min_w = avg_weight - TOLERANCE_GRAMS
    max_w = avg_weight + TOLERANCE_GRAMS

    query = """
        INSERT INTO products 
        (product_name, product_description, category, price, qty, weight, min_weight, max_weight, created_at, barcode,image)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
    """

    db.execute(query, (
        data.product_name,
        data.product_description,
        data.category,
        data.price,
        data.qty,
        avg_weight,
        min_w,
        max_w,
        datetime.now(),
        data.barcode,
        data.image
    ), commit=True)

    return {
        "message": "Product inserted",
        "avg_weight": avg_weight,
        "min_weight": min_w,
        "max_weight": max_w,
        "tolerance_percentage": f"{TOLERANCE_PERCENTAGE * 100}%"
    }

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
        "product_description": result[2],
        "category": result[3],
        "price": result[4],
        "qty": result[5],
        "weight": result[6],
        "min_weight": result[7],
        "max_weight": result[8],
        "barcode": result[9],
        "created_at": result[10],
        "image": result[11]
    }