from uuid import uuid4

from application.ports import UnitOfWork
from application.dtos import CreateShowCommand
from domain.entities.show import ShowEntity
from domain.shared.ids import ShowId
from domain.value_objects import Duration, AgeRating

class CreateShow:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow
    
    async def __call__(self, cmd: CreateShowCommand):
        async with self._uow:
            duration = Duration(minutes=cmd.duration_minutes)
            age_rating = AgeRating(cmd.age_rating)
            
            show = ShowEntity(
                id=ShowId(uuid4()),
                title=cmd.title,
                description=cmd.description,
                age_rating=age_rating,
                poster_url=cmd.poster_url,
                duration=duration              
            )
            
            await self._uow.shows_repo.add(show)
            await self._uow.commit()
            
            return show.id
        