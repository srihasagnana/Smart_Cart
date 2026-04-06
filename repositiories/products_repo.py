from db.connection import Mysql
from models.products import Products

class ProductsRepo:
    def __init__(self,db:Mysql):
        self.db=db

    def insert_product(self, product):
        query = """
            INSERT INTO products 
            (product_name, product_description, category, price, qty, weight, created_at, barcode,min_weight, max_weight)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s,%s)
        """

        cursor = self.db.cursor()
        cursor.execute(query, (
            product.product_name,
            product.product_description,
            product.category,
            product.price,
            product.qty,
            product.weight,
            product.created_at,
            product.barcode,
            product.min_weight,
            product.max_weight
        ))

        self.db.commit() # 🔥 THIS IS CRITICAL

    def update_quantity(self, product_id, qty):
        self.db.execute(
            "UPDATE products SET qty=%s WHERE product_id=%s",
            (qty, product_id),
            commit=True
        )

    def product_by_barcode_from_db(self,barcode: str):
        return self.db.query(Products).filter(Products.barcode == barcode).first()
