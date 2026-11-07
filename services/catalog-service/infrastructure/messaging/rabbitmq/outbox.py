from collections.abc import Sequence
from dataclasses import asdict

from pydantic_core import to_jsonable_python
from sqlalchemy.ext.asyncio import AsyncSession

from domain.events.base import DomainEvent
from infrastructure.db.models import OutBox


class SqlAlchemyOutbox:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def put(self, events: Sequence[DomainEvent]) -> None:
        for event in events:
            self._session.add(OutBox(
                message_id=event.event_id,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                event_type=type(event).__name__,
                payload=to_jsonable_python(asdict(event)),
            ))
