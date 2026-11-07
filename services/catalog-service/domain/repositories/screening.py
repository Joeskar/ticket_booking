from typing import Protocol

from domain.shared.ids import ScreeningId
from domain.entities.screening import ScreeningEntity


class ScreeningRepository(Protocol):
    async def get_for_update(self, screening_id: ScreeningId) -> ScreeningEntity:
        ...
    
    async def add(self, screening: ScreeningEntity) -> None:
        ...
    
    async def save(self, screening: ScreeningEntity) -> None:
        ...
        
    