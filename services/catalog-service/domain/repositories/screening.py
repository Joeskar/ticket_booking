from typing import Protocol

from domain.shared.ids import ScreeningId
from domain.entities.screening import ScreeningEntity


class ScreeningRepository(Protocol):
    async def get(self, screening_id: ScreeningId) -> ScreeningEntity:
        ...
    
    async def create(self, screening) -> ScreeningEntity:
        ...
        
    async def overlap(self, screening) -> ScreeningEntity:
        ...
    
    