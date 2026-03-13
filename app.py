from fastapi import FastAPI
from schemas.init import init_all
from db.connection import Mysql
from routers.products_router import router as products_router

app = FastAPI()

db = Mysql()

app.include_router(products_router)