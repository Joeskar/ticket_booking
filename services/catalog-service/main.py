from fastapi import FastAPI

from presentation.rest.errors import install_exception_handlers
from presentation.rest.v1 import api_router

app = FastAPI(
    docs_url="/api/catalog/v1/docs",
    openapi_url="/api/catalog/v1/openapi",
    redoc_url="/api/catalog/v1/redoc",
)

install_exception_handlers(app)
app.include_router(api_router, prefix="/api/catalog/v1")
