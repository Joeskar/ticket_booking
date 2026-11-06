from dataclasses import dataclass

from domain.events.base import DomainEvent
from domain.shared.ids import ScreeningId


@dataclass(frozen=True, kw_only=True)
class ScreeningPublished(DomainEvent):
    screening_id: ScreeningId


@dataclass(frozen=True, kw_only=True)
class ScreeningCancelled(DomainEvent):
    screening_id: ScreeningId