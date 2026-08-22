from fastapi import FastAPI


app = FastAPI(
    docs_url="/api/catalog/v1/docs",
    openapi_url="/api/catalog/v1/openapi",
    redoc_url="/api/catalog/v1/redoc",
)

