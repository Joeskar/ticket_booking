from dataclasses import dataclass
from typing import final
from uuid import UUID


@final
@dataclass(frozen=True, kw_only=True, slots=True)
class SeatInfo:
    seat_id: UUID
    row_no: int
    seat_no: int
    seat_type: str
