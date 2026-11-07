from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from application.ports.outbox import OutBox
from application.ports.seats import SeatReader
from domain.repositories.screening import ScreeningRepository
from domain.repositories.show import ShowRepository
from infrastructure.db.repositories.screening import SqlAlchemyScreeningRepository
from infrastructure.db.repositories.show import SqlAlchemyShowRepository
from infrastructure.db.repositories.venue import SqlAlchemySeatReader
from infrastructure.messaging.rabbitmq.outbox import SqlAlchemyOutbox


class SqlAlchemyUnitOfWork:
    screenings_repo: ScreeningRepository
    shows_repo: ShowRepository
    seats: SeatReader
    outbox: OutBox

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.screenings_repo = SqlAlchemyScreeningRepository(self._session)
        self.shows_repo = SqlAlchemyShowRepository(self._session)
        self.seats = SqlAlchemySeatReader(self._session)
        self.outbox = SqlAlchemyOutbox(self._session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self._session.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
