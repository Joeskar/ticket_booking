from uuid import uuid4

from fastapi import APIRouter, status

from infrastructure.db.models import Hall, HallSeat
from presentation.dependencies import SessionDep
from presentation.rest.v1.schemas import HallCreate, IdResponse

router = APIRouter(prefix="/halls", tags=["halls"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_hall(body: HallCreate, session: SessionDep) -> IdResponse:
    hall = Hall(id=uuid4(), venue_id=body.venue_id, name=body.name)
    session.add(hall)
    session.add_all(
        HallSeat(
            hall_id=hall.id,
            name=f"R{row}-S{seat}",
            row_no=row,
            seat_no=seat,
            seat_type="STANDARD",
        )
        for row in range(1, body.rows + 1)
        for seat in range(1, body.seats_per_row + 1)
    )
    await session.commit()
    return IdResponse(id=hall.id)
