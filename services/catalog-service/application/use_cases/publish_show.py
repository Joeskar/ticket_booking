from application.ports import UnitOfWork
from application.dtos import PublishShowCommand
from domain.shared.ids import ShowId


class PublishShow:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow
    
    async def __call__(self, cmd: PublishShowCommand):
        async with self._uow:
            show = await self._uow.shows_repo.get(ShowId(cmd.show_id))
            show.publish()
            await self._uow.shows_repo.save(show)
            await self._uow.commit()
    