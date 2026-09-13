from typing import Protocol

from domain.shared.ids import ShowId
from domain.entities.show import ShowEntity


class ShowRepository(Protocol):
    async def get(self, show_id: ShowId) -> ShowEntity:
        ...
        
    async def create(self, show) -> ShowEntity:
        ...
        