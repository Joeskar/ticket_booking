from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, status

from routers.v1.dependencies import SessionDep
from schemas import BookingCreate, BookingRead
from services import bookings as bookings_service

router = APIRouter(prefix="/bookings", tags=["Bbookings"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_booking(body: BookingCreate, session: SessionDep) -> BookingRead:
    booking = await bookings_service.create_booking(session, body.screening_id, body.seat_id)
    return BookingRead.model_validate(booking)


@router.get("/{booking_id}")
async def get_booking_by_id(booking_id: Annotated[UUID, Path()], session: SessionDep) -> BookingRead:
    booking = await bookings_service.get_booking(session, booking_id)
    return BookingRead.model_validate(booking)
