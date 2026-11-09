from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path

from routers.v1.dependencies import SessionDep
from schemas import SeatRead
from services import screenings as screenings_service

router = APIRouter(prefix="/screenings", tags=["Screenings"])


@router.get("/{screening_id}/seats")
async def get_seats_by_screening(screening_id: Annotated[UUID, Path()], session: SessionDep) -> list[SeatRead]:
    return await screenings_service.list_seats(session, screening_id)
