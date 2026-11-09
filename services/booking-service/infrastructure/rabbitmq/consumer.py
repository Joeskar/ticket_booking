import asyncio
import logging
import signal
from collections.abc import Awaitable, Callable
from uuid import UUID

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractIncomingMessage, AbstractQueue
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from infrastructure.db.session import async_session, engine
from schemas.events import PaymentSucceeded, ScreeningPublished
from services.bookings import apply_payment_succeeded
from services.screenings import apply_screening_published


log = logging.getLogger("booking.consumer")

QUEUE_NAME = "booking.inbox"
DLX_NAME = "booking.dlx"
DLQ_NAME = "booking.inbox.dlq"
DELIVERY_LIMIT = 5
PREFETCH_COUNT = 10
RETRY_DELAY_SECONDS = 1.0

# тут указыаем, что слушаем ивенты ScreeningPublished и PaymentSucceeded
BINDINGS = [
    ("catalog.events", "ScreeningPublished"),
    ("payment.events", "PaymentSucceeded"),
]

Handler = Callable[[AsyncSession, UUID, bytes], Awaitable[None]]


async def _on_screening_published(session: AsyncSession, message_id: UUID, body: bytes) -> None:
    event = ScreeningPublished.model_validate_json(body)
    if await apply_screening_published(session, message_id, event):
        log.info("screening %s saved, seats=%d", event.screening_id, len(event.seats))
    else:
        log.info("duplicate message %s skipped", message_id)


async def _on_payment_succeeded(session: AsyncSession, message_id: UUID, body: bytes) -> None:
    event = PaymentSucceeded.model_validate_json(body)
    result = await apply_payment_succeeded(session, message_id, event)
    if result is None:
        log.info("duplicate message %s skipped", message_id)
    else:
        log.info("booking %s paid, status=%s", event.booking_id, result)


HANDLERS: dict[str, Handler] = {
    "ScreeningPublished": _on_screening_published,
    "PaymentSucceeded": _on_payment_succeeded,
}


async def _dispatch(message: AbstractIncomingMessage) -> None:
    handler = HANDLERS.get(message.type or "")
    if handler is None:
        raise ValueError(f"no handler for event type {message.type!r}")
    if message.message_id is None:
        raise ValueError("message has no message_id")

    async with async_session() as session:
        await handler(session, UUID(message.message_id), message.body)


async def on_message(message: AbstractIncomingMessage) -> None:
    try:
        await _dispatch(message)
    except Exception:
        log.exception("failed: type=%s message_id=%s", message.type, message.message_id)
        await asyncio.sleep(RETRY_DELAY_SECONDS)  # что бы делал retry после 1 с, без этого retry сделаются слишком быстро
        await message.nack(requeue=True)  # после лимита попыток сообщение идут в DLQ
        return
    # делаем ack в последнюю очередь
    await message.ack()


async def declare_topology(channel: AbstractChannel) -> AbstractQueue:
    dlx = await channel.declare_exchange(DLX_NAME, aio_pika.ExchangeType.DIRECT, durable=True)
    dlq = await channel.declare_queue(DLQ_NAME, durable=True)
    await dlq.bind(dlx, routing_key=QUEUE_NAME)

    queue = await channel.declare_queue(
        QUEUE_NAME,
        durable=True,
        arguments={
            "x-queue-type": "quorum",
            "x-delivery-limit": DELIVERY_LIMIT,
            "x-dead-letter-exchange": DLX_NAME,
            "x-dead-letter-routing-key": QUEUE_NAME,
        },
    )
    for exchange_name, routing_key in BINDINGS:
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.DIRECT, durable=True)
        await queue.bind(exchange, routing_key=routing_key)
    return queue


async def consume(stop: asyncio.Event) -> None:
    connection = await aio_pika.connect_robust(str(settings.broker.broker_url))
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=PREFETCH_COUNT)
        queue = await declare_topology(channel)
        await queue.consume(on_message)
        log.info("consuming %s, bindings=%s", QUEUE_NAME, BINDINGS)
        await stop.wait()


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)

    try:
        await consume(stop)
    finally:
        await engine.dispose()
    log.info("stopped")


if __name__ == "__main__":
    asyncio.run(main())
