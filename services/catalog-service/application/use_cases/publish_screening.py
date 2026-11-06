from application.ports import Clock, UnitOfWork
from application.dtos import PublishScreeningCommand
from domain.value_objects import ShowStatus
from domain.exceptions import ShowNotPublishedException
from domain.events.screening import ScreeningPublished
from domain.shared.ids import ShowId, ScreeningId

class PublishScreening:
    def __init__(self, uow: UnitOfWork, clock: Clock):
        self._uow = uow
        self._clock = clock

    async def __call__(self, cmd: PublishScreeningCommand):
        async with self._uow:
            screening = await self._uow.screenings_repo.get(ScreeningId(cmd.screening_id))

            show = await self._uow.shows_repo.get(ShowId(screening.show_id))

            if show.status is not ShowStatus.PUBLISHED:
                raise ShowNotPublishedException

            screening.publish(self._clock.now())

            await self._uow.screenings_repo.save(screening)
            await self._uow.outbox.put(screening.pull_events())
            await self._uow.commit()
