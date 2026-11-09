from fastapi import APIRouter

from routers.v1 import bookings, screenings

api_router = APIRouter()
api_router.include_router(bookings.router)
api_router.include_router(screenings.router)