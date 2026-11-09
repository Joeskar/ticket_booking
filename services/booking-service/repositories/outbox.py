from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models import OutBox


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def put(
        self,
        *,
        message_id: UUID,
        event_type: str,
        aggregate_type: str,
        aggregate_id: UUID,
        payload: dict[str, Any],
    ) -> None:
        self._session.add(OutBox(
            message_id=message_id,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
        ))
