from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.show import ShowEntity
from domain.exceptions import ShowNotFoundException
from domain.shared.ids import ShowId
from infrastructure.db.mappers import show_to_entity, show_to_row
from infrastructure.db.models import Show


class SqlAlchemyShowRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, show_id: ShowId) -> ShowEntity:
        row = await self._session.get(Show, show_id)
        if row is None:
            raise ShowNotFoundException(show_id)
        return show_to_entity(row)

    async def add(self, show: ShowEntity) -> None:
        self._session.add(show_to_row(show))

    async def save(self, show: ShowEntity) -> None:
        await self._session.merge(show_to_row(show))
