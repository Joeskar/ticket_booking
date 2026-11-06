from uuid import uuid4

from application.ports import UnitOfWork
from application.dtos import CreateScreeningCommand
from domain.value_objects import Period, Money
from domain.entities.screening import ScreeningEntity
from domain.shared.ids import ScreeningId, ShowId


class CreateScreening:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow
    
    async def __call__(self, cmd: CreateScreeningCommand):
        async with self._uow:
            show = await self._uow.shows_repo.get(ShowId(cmd.show_id))
            show.ensure_accepts_screenings()
            
            period = Period(start=cmd.starts_at, end=cmd.starts_at + show.duration.as_timedelta())
            price = Money(value=cmd.price_amount, currency=cmd.price_currency)
            
            screening = ScreeningEntity(
                id=ScreeningId(uuid4()),
                hall_id=cmd.hall_id,
                show_id=cmd.show_id,
                money=price,
                period=period,
            )
            await self._uow.screenings_repo.add(screening)
            await self._uow.commit()
            
            return screening.id
            