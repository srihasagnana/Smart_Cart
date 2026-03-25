from fastapi import FastAPI
from schemas.init import init_all
from db.connection import Mysql
from routers.products_router import router as products_router
from routers.cart_router import router as cart_router

app = FastAPI()

db = Mysql()

@app.on_event("startup")
def startup():
    init_all()
app.include_router(products_router)
app.include_router(cart_router)