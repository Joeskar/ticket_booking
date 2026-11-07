from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.shared.ids import HallId
from domain.value_objects.seat import SeatInfo
from infrastructure.db.models import HallSeat


class SqlAlchemySeatReader:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_seats(self, hall_id: HallId) -> list[SeatInfo]:
        rows = await self._session.scalars(
            select(HallSeat)
            .where(HallSeat.hall_id == hall_id)
            .order_by(HallSeat.row_no, HallSeat.seat_no)
        )
        return [
            SeatInfo(seat_id=r.id, row_no=r.row_no, seat_no=r.seat_no, seat_type=r.seat_type)
            for r in rows
        ]
