from uuid import UUID

from fastapi import APIRouter, status

from application.dtos import CreateScreeningCommand, PublishScreeningCommand
from application.use_cases.create_screening import CreateScreening
from application.use_cases.publish_screening import PublishScreening
from infrastructure.clock import SystemClock
from presentation.dependencies import UowDep
from presentation.rest.v1.schemas import IdResponse, ScreeningCreate

router = APIRouter(prefix="/screenings", tags=["screenings"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_screening(body: ScreeningCreate, uow: UowDep) -> IdResponse:
    screening_id = await CreateScreening(uow)(CreateScreeningCommand(
        show_id=body.show_id,
        hall_id=body.hall_id,
        starts_at=body.starts_at,
        price_amount=body.price_amount,
        price_currency=body.price_currency,
    ))
    return IdResponse(id=screening_id)


@router.post("/{screening_id}/publish", status_code=status.HTTP_204_NO_CONTENT)
async def publish_screening(screening_id: UUID, uow: UowDep) -> None:
    await PublishScreening(uow, SystemClock())(PublishScreeningCommand(screening_id=screening_id))
