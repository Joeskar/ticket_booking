from application.ports import Clock, UnitOfWork
from application.dtos import PublishScreeningCommand
from domain.shared.ids import ScreeningId

class PublishScreening:
    def __init__(self, uow: UnitOfWork, clock: Clock):
        self._uow = uow
        self._clock = clock

    async def __call__(self, cmd: PublishScreeningCommand):
        async with self._uow:
            screening = await self._uow.screenings_repo.get_for_update(ScreeningId(cmd.screening_id))

            show = await self._uow.shows_repo.get(screening.show_id)
            show.ensure_accepts_screenings()

            seats = await self._uow.seats.get_seats(screening.hall_id)
            screening.publish(self._clock.now(), seats)

            await self._uow.screenings_repo.save(screening)
            await self._uow.outbox.put(screening.pull_events())
            await self._uow.commit()
