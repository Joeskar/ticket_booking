from uuid import uuid4

from fastapi import APIRouter, status

from infrastructure.db.models import Venue
from presentation.dependencies import SessionDep
from presentation.rest.v1.schemas import IdResponse, VenueCreate

router = APIRouter(prefix="/venues", tags=["venues"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_venue(body: VenueCreate, session: SessionDep) -> IdResponse:
    venue = Venue(id=uuid4(), name=body.name, city=body.city, address=body.address)
    session.add(venue)
    await session.commit()
    return IdResponse(id=venue.id)
