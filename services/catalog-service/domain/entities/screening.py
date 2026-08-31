from dataclasses import dataclass

from domain.shared.entity import AggregateRootEntity
from domain.shared.ids import ScreeningId, HallId, ShowId
from domain.value_objects.money import Money


@dataclass
class ScreeningEntity(AggregateRootEntity):
    id: ScreeningId
    hall_id: HallId
    show_id: ShowId
    money: Money
    
    
    def __post_init__(self):
        pass
        