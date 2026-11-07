from typing import Protocol

from domain.shared.ids import HallId
from domain.value_objects.seat import SeatInfo


class SeatReader(Protocol):
    async def get_seats(self, hall_id: HallId) -> list[SeatInfo]:
        ...
        