from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Path

from routers.v1.dependencies import SessionDep
from schemas import AttemptRead, PaymentRead, PayRequest
from services import payments as payments_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/{booking_id}/pay")
async def pay(
    booking_id: Annotated[UUID, Path()],
    body: PayRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=255)],
    session: SessionDep,
) -> AttemptRead:
    attempt = await payments_service.pay(session, booking_id, idempotency_key, body)
    return AttemptRead.model_validate(attempt)


@router.get("/{booking_id}")
async def get_payment(booking_id: Annotated[UUID, Path()], session: SessionDep) -> PaymentRead:
    return await payments_service.get_payment(session, booking_id)
