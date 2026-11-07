"""Доставляет события из таблицы outbox в RabbitMQ.

Гарантия: at-least-once. Если процесс упадёт после подтверждения брокера, но до
commit, событие уйдёт повторно с тем же message_id, поэтому потребитель обязан
отбрасывать дубли по message_id.

Запуск: python -m infrastructure.messaging.rabbitmq.relay
"""
import asyncio
import contextlib
import json
import logging
import signal
from datetime import datetime, timezone

import aio_pika
from aio_pika.abc import AbstractExchange
from aio_pika.exceptions import DeliveryError
from sqlalchemy import select

from core.config import settings
from infrastructure.db.models import OutBox
from infrastructure.db.session import async_session, engine

log = logging.getLogger("catalog.relay")

EXCHANGE_NAME = "catalog.events"
BATCH_SIZE = 50
POLL_INTERVAL_SECONDS = 1.0
RETRY_DELAY_SECONDS = 5.0
PUBLISH_TIMEOUT_SECONDS = 5.0


def _to_message(row: OutBox) -> aio_pika.Message:
    return aio_pika.Message(
        body=json.dumps(row.payload).encode(),
        message_id=str(row.message_id),
        type=row.event_type,
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )


async def publish_batch(exchange: AbstractExchange) -> int:
    """Публикует пачку событий и возвращает, сколько из них подтвердил брокер."""
    async with async_session() as session:
        # SKIP LOCKED: другая копия relay возьмёт следующие строки, а не будет ждать эти.
        rows = await session.scalars(
            select(OutBox)
            .where(OutBox.published_at.is_(None))
            .order_by(OutBox.created_at)
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )

        published = 0
        try:
            for row in rows.all():
                # mandatory + on_return_raises: событие без очереди даст DeliveryError
                # и останется в outbox, а не пропадёт молча.
                await exchange.publish(
                    _to_message(row),
                    routing_key=row.event_type,
                    mandatory=True,
                    timeout=PUBLISH_TIMEOUT_SECONDS,
                )
                row.published_at = datetime.now(timezone.utc)
                published += 1
        finally:
            # Подтверждённое брокером фиксируем и при сбое на середине пачки,
            # иначе эти строки ушли бы повторно.
            await session.commit()

        return published


async def _sleep(stop: asyncio.Event, seconds: float) -> None:
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(stop.wait(), seconds)


async def _publish_until_stopped(stop: asyncio.Event) -> None:
    connection = await aio_pika.connect(str(settings.broker.broker_url))
    async with connection:
        channel = await connection.channel(publisher_confirms=True, on_return_raises=True)
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True
        )
        log.info("connected, exchange=%s", EXCHANGE_NAME)

        while not stop.is_set():
            published = await publish_batch(exchange)
            if published:
                log.info("published=%d", published)
            if published < BATCH_SIZE:
                await _sleep(stop, POLL_INTERVAL_SECONDS)


async def run(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await _publish_until_stopped(stop)
        except DeliveryError:
            log.warning("no queue is bound for an event, it stays in the outbox")
        except Exception:
            log.exception("relay failed, retrying in %s s", RETRY_DELAY_SECONDS)
        await _sleep(stop, RETRY_DELAY_SECONDS)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # По SIGTERM дописываем текущую пачку и выходим, а не обрываемся на её середине.
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)

    try:
        await run(stop)
    finally:
        await engine.dispose()
    log.info("stopped")


if __name__ == "__main__":
    asyncio.run(main())
