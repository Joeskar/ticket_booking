from typing import Protocol
from collections.abc import Sequence

from domain.events.base import DomainEvent


class OutBox(Protocol):
    async def put(self, events: Sequence[DomainEvent]):
        ...