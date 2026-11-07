from fastapi import APIRouter

from presentation.rest.v1 import halls, screenings, shows, venues

api_router = APIRouter()
api_router.include_router(venues.router)
api_router.include_router(halls.router)
api_router.include_router(shows.router)
api_router.include_router(screenings.router)
