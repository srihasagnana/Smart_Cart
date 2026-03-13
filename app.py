from fastapi import FastAPI
from db.connection import Mysql
from schemas.init import init_all
from seed_data.products import SeedData

app = FastAPI()

db = Mysql()


@app.get("/init-db")
def initialize_database():
    init_all()
    return {"message": "Tables created"}


@app.post("/seed-products")
def seed_products():
    data = SeedData(db)
    data.insert_products()
    return {"message": "Products inserted"}


@app.get("/product/{product_id}")
def get_product(product_id: int):
    data = SeedData(db)
    product = data.get_product_by_id(product_id)
    return product