from fastapi import FastAPI

from routers.v1 import api_router

app = FastAPI(
    docs_url="/api/payment/v1/docs",
    openapi_url="/api/payment/v1/openapi",
    redoc_url="/api/payment/v1/redoc",
)

app.include_router(api_router, prefix="/api/payment/v1")
