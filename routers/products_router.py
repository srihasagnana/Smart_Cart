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

    # 🔥 STEP 1: sort weights
    weights = sorted(data.weights)

    # 🔥 STEP 2: find most stable cluster
    best_group = []
    min_range = float("inf")

    for i in range(len(weights) - 2):
        group = weights[i:i+3]   # window of 3
        current_range = max(group) - min(group)

        if current_range < min_range:
            min_range = current_range
            best_group = group

    # 🔥 STEP 3: compute avg weight
    avg_weight = sum(best_group) / len(best_group)

    # 🔥 STEP 4: tolerance
    TOLERANCE = 5

    min_w = avg_weight - TOLERANCE
    max_w = avg_weight + TOLERANCE

    # 🔥 INSERT
    query = """
        INSERT INTO products 
        (product_name, product_description, category, price, qty, weight, min_weight, max_weight, created_at, barcode)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        data.barcode
    ), commit=True)

    return {
        "message": "Product inserted",
        "avg_weight": avg_weight,
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
import time

def get_stable_weight():
    readings = []
    stable_count = 0

    last_value = None

    for _ in range(20):   # max attempts (but will stop early)
        w = get_weight()

        if not w or w <= 0:
            continue

        readings.append(w)

        if last_value is not None:
            if abs(w - last_value) < 1:   # stability threshold
                stable_count += 1
            else:
                stable_count = 0

        last_value = w

        # 🔥 STOP EARLY if stable
        if stable_count >= 3:
            return sum(readings[-3:]) / 3

        time.sleep(0.03)   # very small delay

    # fallback
    if readings:
        return sum(readings[-5:]) / min(5, len(readings))

    return None

@router.get("/weight")
def read_weight():
    weight = get_stable_weight()

    if weight is None:
        return {"error": "No weight"}

    return {"weight": weight}