from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.screening import ScreeningEntity
from domain.exceptions import ScreeningNotFoundException
from domain.shared.ids import ScreeningId
from infrastructure.db.mappers import screening_to_entity, screening_to_row
from infrastructure.db.models import Screening


class SqlAlchemyScreeningRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_for_update(self, screening_id: ScreeningId) -> ScreeningEntity:
        row = await self._session.get(Screening, screening_id, with_for_update=True)
        if row is None:
            raise ScreeningNotFoundException(screening_id)
        return screening_to_entity(row)

    async def add(self, screening: ScreeningEntity) -> None:
        self._session.add(screening_to_row(screening))

    async def save(self, screening: ScreeningEntity) -> None:
        await self._session.merge(screening_to_row(screening))
