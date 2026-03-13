from db.connection import Mysql
from repositiories.products_repo import ProductsRepo
from models.products import Products
from datetime import datetime

class SeedData:
    def __init__(self,db:Mysql):
        self.db=db
        self.products=ProductsRepo(db)


    def insert_products(self):
        products = [
            Products('Lays Classic Chips', 'Salted potato chips', 'Snacks', 20.00, 100, 50.00000, datetime.now()),
            Products('Good Day Biscuit', 'Butter biscuits', 'Snacks', 30.00, 120, 70.00000, datetime.now()),
            Products('Dairy Milk Chocolate', 'Milk chocolate bar', 'Confectionery', 40.00, 80, 45.00000,
                     datetime.now()),
            Products('Lux Soap', 'Bath soap bar', 'Personal Care', 45.00, 60, 120.00000, datetime.now()),
            Products('Colgate Toothpaste', 'Strong teeth toothpaste', 'Personal Care', 95.00, 50, 150.00000,
                     datetime.now()),
            Products('Maggi Noodles', 'Instant noodles pack', 'Food', 15.00, 200, 70.00000, datetime.now()),
            Products('Amul Butter', 'Salted butter pack', 'Dairy', 55.00, 70, 100.00000, datetime.now()),
            Products('Sprite 500ml', 'Lemon flavored soft drink', 'Beverages', 40.00, 90, 520.00000, datetime.now()),
            Products('Parle-G Biscuit', 'Glucose biscuits', 'Snacks', 10.00, 150, 60.00000, datetime.now()),
            Products('Surf Excel Detergent', 'Washing powder', 'Household', 120.00, 40, 500.00000, datetime.now())
        ]
        for pro in products:
            self.products.insert_product(pro)

    def get_product_by_id(self,product_id:int):
        return self.db.fetchone("""
            select * from products where product_id=%s
        """,(product_id,))