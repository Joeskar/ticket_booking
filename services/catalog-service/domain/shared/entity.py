from dataclasses import dataclass, field

from domain.events.base import DomainEvent


@dataclass(eq=False, kw_only=True)
class AggregateRootEntity:
    _events: list[DomainEvent] = field(
        default_factory=list, init=False, repr=False, compare=False
    )

    def _add_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events, self._events = self._events, []
        return events
