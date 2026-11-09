from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models import ProcessedMessage


class ProcessedMessageRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def try_mark(self, message_id: UUID, event_type: str) -> bool:
        # если приходит true, то message в первый раз приходит, если false, значит обработали
        inserted = await self._session.scalar(
            insert(ProcessedMessage)
            .values(message_id=message_id, event_type=event_type)
            .on_conflict_do_nothing(index_elements=[ProcessedMessage.message_id])
            .returning(ProcessedMessage.message_id)
        )
        return inserted is not None
