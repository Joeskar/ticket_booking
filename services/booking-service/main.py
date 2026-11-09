from fastapi import FastAPI

from routers.v1 import api_router

app = FastAPI(
    docs_url="/api/booking/v1/docs",
    openapi_url="/api/booking/v1/openapi",
    redoc_url="/api/booking/v1/redoc",
)

app.include_router(api_router, prefix="/api/booking/v1")
