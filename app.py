from fastapi import FastAPI
from schemas.init import init_all
from db.connection import Mysql
from routers.products_router import router as products_router
from routers.cart_router import router as cart_router
from routers.user_router import router as user_router
from routers.order_router import router as order_router
from routers.recommendation_routes import router as recommendation_router

app = FastAPI()

@app.on_event("startup")
def startup():
    init_all()

db = Mysql()

app.include_router(products_router)
app.include_router(cart_router)
app.include_router(user_router)
app.include_router(order_router)
app.include_router(recommendation_router)