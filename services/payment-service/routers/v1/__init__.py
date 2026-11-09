from fastapi import APIRouter

from routers.v1 import payments

api_router = APIRouter()
api_router.include_router(payments.router)
