from db.connection import Mysql
from models.products import Products

class ProductsRepo:
    def __init__(self,db:Mysql):
        self.db=db

    def insert_product(self,p:Products):
        self.db.execute(
            """insert into products(product_name,product_description,
            category,price,qty,weight,created_at) values(%s,%s,%s,%s,%s,%s,%s)""",
            (p.product_name,p.product_description,p.category,p.price,p.qty,p.weight,p.created_at),
            commit=True
        )