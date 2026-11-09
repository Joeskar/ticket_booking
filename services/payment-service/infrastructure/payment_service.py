"""
Это файл имитаций реально сервиса платежки, если номер карты будет оканчиваться на 0002, то платежка будет отклонена
delay_seconds сколько секунд, столько секунд будет слип для имитаций задержки
"""
import asyncio
from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

DECLINED_CARD_SUFFIX = "0002"


@dataclass(frozen=True)
class ChargeResult:
    approved: bool
    provider_ref: str | None = None
    failure_reason: str | None = None

# думал между charge и deduct, charge корректней
async def charge(*, amount: Decimal, currency: str, card_number: str, delay_seconds: float) -> ChargeResult:
    if delay_seconds:
        await asyncio.sleep(delay_seconds)
    if card_number.endswith(DECLINED_CARD_SUFFIX):
        return ChargeResult(approved=False, failure_reason="card_declined")
    return ChargeResult(approved=True, provider_ref=f"fake_{uuid4().hex[:16]}")
