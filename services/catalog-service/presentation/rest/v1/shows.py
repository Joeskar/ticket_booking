from uuid import UUID

from fastapi import APIRouter, status

from application.dtos import CreateShowCommand, PublishShowCommand
from application.use_cases.create_show import CreateShow
from application.use_cases.publish_show import PublishShow
from presentation.dependencies import UowDep
from presentation.rest.v1.schemas import IdResponse, ShowCreate

router = APIRouter(prefix="/shows", tags=["shows"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_show(body: ShowCreate, uow: UowDep) -> IdResponse:
    show_id = await CreateShow(uow)(CreateShowCommand(
        title=body.title,
        description=body.description,
        duration_minutes=body.duration_minutes,
        age_rating=int(body.age_rating),
        poster_url=body.poster_url,
    ))
    return IdResponse(id=show_id)


@router.post("/{show_id}/publish", status_code=status.HTTP_204_NO_CONTENT)
async def publish_show(show_id: UUID, uow: UowDep) -> None:
    await PublishShow(uow)(PublishShowCommand(show_id=show_id))
