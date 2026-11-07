from domain.entities.screening import ScreeningEntity
from domain.entities.show import ShowEntity
from domain.shared.ids import HallId, ScreeningId, ShowId
from domain.value_objects import AgeRating, Currency, Duration, Money, Period
from infrastructure.db.models import Screening, Show


def show_to_row(entity: ShowEntity) -> Show:
    return Show(
        id=entity.id,
        title=entity.title,
        description=entity.description,
        duration_min=entity.duration.minutes,
        status=entity.status,
        age_rating=int(entity.age_rating),
        poster_url=entity.poster_url,
    )


def show_to_entity(row: Show) -> ShowEntity:
    return ShowEntity(
        id=ShowId(row.id),
        title=row.title,
        description=row.description,
        duration=Duration(minutes=row.duration_min),
        status=row.status,
        age_rating=AgeRating(row.age_rating),
        poster_url=row.poster_url,
    )


def screening_to_row(entity: ScreeningEntity) -> Screening:
    return Screening(
        id=entity.id,
        hall_id=entity.hall_id,
        show_id=entity.show_id,
        status=entity.status,
        starts_at=entity.period.start,
        ends_at=entity.period.end,
        price_amount=entity.money.value,
        price_currency=entity.money.currency.value,
    )


def screening_to_entity(row: Screening) -> ScreeningEntity:
    return ScreeningEntity(
        id=ScreeningId(row.id),
        hall_id=HallId(row.hall_id),
        show_id=ShowId(row.show_id),
        status=row.status,
        period=Period(start=row.starts_at, end=row.ends_at),
        money=Money(value=row.price_amount, currency=Currency(row.price_currency)),
    )
