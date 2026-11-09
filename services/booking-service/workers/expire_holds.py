import asyncio
import contextlib
import logging
import signal

from infrastructure.db.session import async_session, engine
from services.bookings import expire_due_holds

log = logging.getLogger("booking.expirer")

INTERVAL_SECONDS = 1.0
BATCH_SIZE = 100
RETRY_DELAY_SECONDS = 5.0


async def _sleep(stop: asyncio.Event, seconds: float) -> None:
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(stop.wait(), seconds)


async def run(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            async with async_session() as session:
                expired = await expire_due_holds(session, BATCH_SIZE)
        except Exception:
            log.exception("expire failed, retrying in %s s", RETRY_DELAY_SECONDS)
            await _sleep(stop, RETRY_DELAY_SECONDS)
            continue

        if expired:
            log.info("expired=%d", expired)
        if expired < BATCH_SIZE:
            await _sleep(stop, INTERVAL_SECONDS)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

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
