from datetime import datetime
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    occurred_at: datetime
    event_id: UUID = field(default_factory=uuid4)
    