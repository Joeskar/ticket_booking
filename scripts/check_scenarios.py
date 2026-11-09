#!/usr/bin/env python3
"""Проверка основных сценариев ticket_booking на поднятом стенде.

Запуск из корня репозитория:

    HOLD_TTL_SECONDS=10 docker compose -f deploy/docker-compose.yml up -d --wait --build
    python3 scripts/check_scenarios.py            # основные сценарии
    python3 scripts/check_scenarios.py --chaos    # плюс остановка сервисов посреди процесса

"""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

ROOT = Path(__file__).resolve().parent.parent
CATALOG = os.getenv("CATALOG_URL", "http://localhost:8001/api/catalog/v1")
BOOKING = os.getenv("BOOKING_URL", "http://localhost:8002/api/booking/v1")
PAYMENT = os.getenv("PAYMENT_URL", "http://localhost:8003/api/payment/v1")
RABBITMQ_API = os.getenv("RABBITMQ_API_URL", "http://localhost:15672/api")
RABBITMQ_AUTH = os.getenv("RABBITMQ_AUTH", "guest:guest")
COMPOSE_FILE = os.getenv("COMPOSE_FILE_PATH", str(ROOT / "deploy" / "docker-compose.yml"))

GOOD_CARD = "4242424242424242"
DECLINED_CARD = "4000000000000002"  # заглушка провайдера отклоняет карты, оканчивающиеся на 0002
PARALLEL = 20
MAX_TTL_FOR_EXPIRY_CHECKS = 60

GREEN, RED, YELLOW, BOLD, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[1m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = BOLD = RESET = ""


# ---------------------------------------------------------------- вывод

class Report:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def check(self, ok: bool, text: str, details: Any = "") -> bool:
        if ok:
            self.passed += 1
            print(f"  {GREEN}PASS{RESET} {text}" + (f"  ({details})" if details != "" else ""))
        else:
            self.failed += 1
            print(f"  {RED}FAIL{RESET} {text}" + (f"  ({details})" if details != "" else ""))
        return ok

    def skip(self, text: str, reason: str) -> None:
        self.skipped += 1
        print(f"  {YELLOW}SKIP{RESET} {text}: {reason}")


report = Report()


def scenario(title: str, proves: str, fn: Callable[[], None]) -> None:
    print(f"\n{BOLD}{title}{RESET}\n  что доказывает: {proves}")
    try:
        fn()
    except Exception as error:  # сценарий не должен ронять остальные
        report.check(False, "сценарий упал с исключением", repr(error))


# ---------------------------------------------------------------- HTTP

def http(method: str, url: str, body: Any = None, headers: dict | None = None,
         auth: str | None = None, timeout: float = 60) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    for name, value in (headers or {}).items():
        request.add_header(name, value)
    if auth:
        request.add_header("Authorization", "Basic " + base64.b64encode(auth.encode()).decode())
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read()
    try:
        return status, json.loads(raw) if raw else None
    except ValueError:
        return status, raw.decode(errors="replace")


def wait_until(predicate: Callable[[], Any], timeout: float, interval: float = 0.3) -> Any:
    deadline = time.monotonic() + timeout
    while True:
        value = predicate()
        if value or time.monotonic() >= deadline:
            return value
        time.sleep(interval)


def in_parallel(n: int, fn: Callable[[int], Any]) -> list:
    """Запускает n запросов так, чтобы они стартовали одновременно."""
    barrier = threading.Barrier(n)

    def task(i: int) -> Any:
        barrier.wait()
        return fn(i)

    with ThreadPoolExecutor(n) as pool:
        return list(pool.map(task, range(n)))


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def label(status: int, body: Any) -> str:
    """Короткая подпись ответа для сводки: «200 SUCCEEDED», «409 Booking is already paid»."""
    if isinstance(body, dict):
        detail = body.get("status") or body.get("detail")
        if isinstance(detail, str):
            return f"{status} {detail}"
    return str(status)


# ---------------------------------------------------------------- API сервисов

def book(screening_id: str, seat_id: str) -> tuple[int, Any]:
    return http("POST", f"{BOOKING}/bookings", {"screening_id": screening_id, "seat_id": seat_id})


def booking_status(booking_id: str) -> str | None:
    status, body = http("GET", f"{BOOKING}/bookings/{booking_id}")
    return body.get("status") if status == 200 else None


def seat_state(screening_id: str, seat_id: str) -> str | None:
    status, seats = http("GET", f"{BOOKING}/screenings/{screening_id}/seats")
    if status != 200:
        return None
    return next((s["state"] for s in seats if s["seat_id"] == seat_id), None)


def pay(booking_id: str, key: str, card: str = GOOD_CARD, delay: float = 0) -> tuple[int, Any]:
    return http("POST", f"{PAYMENT}/payments/{booking_id}/pay",
                {"card_number": card, "delay_seconds": delay}, {"Idempotency-Key": key})


def get_payment(booking_id: str) -> dict | None:
    status, body = http("GET", f"{PAYMENT}/payments/{booking_id}")
    return body if status == 200 else None


def wait_payment(booking_id: str) -> dict | None:
    """Платёж появляется, когда payment обработает BookingCreated (обычно за 1–2 с)."""
    return wait_until(lambda: get_payment(booking_id), timeout=20)


def wait_booking(booking_id: str, *statuses: str, timeout: float = 20) -> str | None:
    found = wait_until(lambda: booking_status(booking_id) in statuses, timeout=timeout)
    return booking_status(booking_id) if found else None


def compose(action: str, service: str) -> None:
    result = subprocess.run(["docker", "compose", "-f", COMPOSE_FILE, action, service],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"docker compose {action} {service}: {result.stderr.strip()}")


def rabbit_queue_messages(queue: str) -> int | None:
    vhost = urllib.parse.quote("/", safe="")
    status, body = http("GET", f"{RABBITMQ_API}/queues/{vhost}/{queue}", auth=RABBITMQ_AUTH)
    return body.get("messages", 0) if status == 200 else None


def rabbit_publish(exchange: str, routing_key: str, payload: str, message_type: str) -> bool:
    vhost = urllib.parse.quote("/", safe="")
    status, body = http("POST", f"{RABBITMQ_API}/exchanges/{vhost}/{exchange}/publish", {
        "properties": {"message_id": str(uuid.uuid4()), "type": message_type, "delivery_mode": 2,
                       "content_type": "application/json"},
        "routing_key": routing_key,
        "payload": payload,
        "payload_encoding": "string",
    }, auth=RABBITMQ_AUTH)
    return status == 200 and bool(body.get("routed"))


# ---------------------------------------------------------------- подготовка данных

class Stand:
    """Опубликованный сеанс и выдача свободных мест для сценариев."""

    def __init__(self, screening_id: str, seat_ids: list[str]) -> None:
        self.screening_id = screening_id
        self._seats: Iterator[str] = iter(seat_ids)
        self.ttl: float | None = None

    def next_seat(self) -> str:
        return next(self._seats)

    def new_booking(self, seat_id: str | None = None) -> dict:
        status, body = book(self.screening_id, seat_id or self.next_seat())
        if status != 201:
            raise RuntimeError(f"бронь не создалась: {status} {body}")
        if self.ttl is None:
            self.ttl = (parse_dt(body["expires_at"]) - parse_dt(body["created_at"])).total_seconds()
        return body

    def short_ttl(self) -> bool:
        return self.ttl is not None and self.ttl <= MAX_TTL_FOR_EXPIRY_CHECKS

    def expiry_wait(self) -> float:
        """Сколько ждать истечения брони: TTL плюс запас на таймер и доставку событий."""
        return (self.ttl or 0) + 15

    def ttl_hint(self) -> str:
        ttl = "неизвестен" if self.ttl is None else f"{self.ttl:.0f} с"
        return f"TTL брони {ttl}; подними стенд с HOLD_TTL_SECONDS=10"


def prepare() -> Stand:
    def created(path: str, body: dict) -> str:
        status, response = http("POST", f"{CATALOG}{path}", body)
        if status != 201:
            raise RuntimeError(f"POST {path}: {status} {response}")
        return response["id"]

    def published(path: str) -> None:
        status, response = http("POST", f"{CATALOG}{path}")
        if status != 204:
            raise RuntimeError(f"POST {path}: {status} {response}")

    venue = created("/venues", {"name": "Check cinema", "city": "Almaty", "address": "Abay 1"})
    hall = created("/halls", {"venue_id": venue, "name": "Check hall", "rows": 5, "seats_per_row": 8})
    show = created("/shows", {"title": "Check show", "duration_minutes": 120, "age_rating": 12})
    published(f"/shows/{show}/publish")
    starts_at = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    screening = created("/screenings", {"show_id": show, "hall_id": hall, "starts_at": starts_at,
                                        "price_amount": "2500.00", "price_currency": "KZT"})
    published(f"/screenings/{screening}/publish")

    def seats_in_booking() -> list | None:
        status, seats = http("GET", f"{BOOKING}/screenings/{screening}/seats")
        return seats if status == 200 and len(seats) == 40 else None

    started = time.monotonic()
    seats = wait_until(seats_in_booking, timeout=30)
    if not seats:
        raise RuntimeError("места сеанса не появились в booking за 30 с: работают ли catalog-relay и booking-consumer?")
    print(f"  сеанс {screening}: 40 мест доехали до booking за {time.monotonic() - started:.1f} с "
          f"(catalog → outbox → relay → RabbitMQ → booking-consumer)")
    return Stand(screening, [s["seat_id"] for s in seats])


# ---------------------------------------------------------------- основные сценарии

def parallel_booking(stand: Stand) -> None:
    seat = stand.next_seat()
    results = in_parallel(PARALLEL, lambda i: book(stand.screening_id, seat))
    codes = Counter(status for status, _ in results)
    report.check(codes[201] == 1 and codes[409] == PARALLEL - 1,
                 f"{PARALLEL} одновременных броней одного места: одна 201, остальные 409", dict(codes))
    report.check(seat_state(stand.screening_id, seat) == "HELD", "место держится за победителем (HELD)")
    winner = next(body for status, body in results if status == 201)
    stand.ttl = (parse_dt(winner["expires_at"]) - parse_dt(winner["created_at"])).total_seconds()
    print(f"  TTL брони на стенде: {stand.ttl:.0f} с")


def same_key_payment(stand: Stand) -> None:
    booking = stand.new_booking()
    wait_payment(booking["id"])
    started = time.monotonic()
    results = in_parallel(10, lambda i: pay(booking["id"], "same-key", GOOD_CARD, delay=1.0))
    ids = {body.get("id") for status, body in results if status == 200}
    report.check(all(status == 200 for status, _ in results) and len(ids) == 1,
                 "10 одновременных оплат с одним Idempotency-Key (провайдер думает 1 с): один ответ на всех",
                 f"{len(ids)} id попытки за {time.monotonic() - started:.1f} с")
    payment = get_payment(booking["id"]) or {}
    report.check(len(payment.get("attempts", [])) == 1 and payment.get("status") == "SUCCEEDED",
                 "в платеже ровно одна попытка, списание одно", payment.get("status"))
    report.check(wait_booking(booking["id"], "CONFIRMED") == "CONFIRMED",
                 "PaymentSucceeded дошёл до booking: бронь CONFIRMED")
    report.check(seat_state(stand.screening_id, booking["seat_id"]) == "SOLD", "место продано (SOLD)")


def two_tabs(stand: Stand) -> None:
    booking = stand.new_booking()
    wait_payment(booking["id"])
    results = in_parallel(PARALLEL, lambda i: pay(booking["id"], f"tab-{i}"))
    labels = Counter(label(status, body) for status, body in results)
    succeeded = [body for status, body in results if status == 200]
    report.check(len(succeeded) == 1 and labels.get("409 Booking is already paid") == PARALLEL - 1,
                 f"{PARALLEL} одновременных оплат с разными ключами: один успех, остальные 409", dict(labels))
    payment = get_payment(booking["id"]) or {}
    successes = [a for a in payment.get("attempts", []) if a["status"] == "SUCCEEDED"]
    report.check(len(successes) == 1, "в базе payment ровно одна успешная попытка", len(successes))
    if succeeded:
        status, replay = pay(booking["id"], succeeded[0]["idempotency_key"])
        report.check(status == 200 and replay == succeeded[0],
                     "повтор запроса победителя с тем же ключом возвращает тот же ответ, а не 409")


def declined_then_success(stand: Stand) -> None:
    booking = stand.new_booking()
    wait_payment(booking["id"])
    status, first = pay(booking["id"], "declined", DECLINED_CARD)
    report.check(status == 200 and first.get("status") == "FAILED", "карта отклонена: попытка FAILED",
                 first.get("failure_reason"))
    report.check(pay(booking["id"], "declined", DECLINED_CARD) == (status, first),
                 "повтор с тем же ключом возвращает тот же отказ, провайдер второй раз не вызывается")
    report.check(booking_status(booking["id"]) == "HELD", "неудачная оплата бронь не снимает: можно платить снова")
    status, second = pay(booking["id"], "new-card")
    report.check(status == 200 and second.get("status") == "SUCCEEDED", "новый ключ, другая карта: успех")
    attempts = [a["status"] for a in (get_payment(booking["id"]) or {}).get("attempts", [])]
    report.check(attempts == ["FAILED", "SUCCEEDED"], "история попыток", attempts)
    report.check(wait_booking(booking["id"], "CONFIRMED") == "CONFIRMED", "бронь CONFIRMED")


def expiry_releases_seat(stand: Stand) -> None:
    if not stand.short_ttl():
        report.skip("истечение брони", stand.ttl_hint())
        return
    booking = stand.new_booking()
    seat = booking["seat_id"]
    wait_payment(booking["id"])
    pay(booking["id"], "declined", DECLINED_CARD)
    report.check(seat_state(stand.screening_id, seat) == "HELD", "после отказа место ещё держится")
    final = wait_booking(booking["id"], "EXPIRED", timeout=stand.expiry_wait())
    report.check(final == "EXPIRED", f"за TTL ({stand.ttl:.0f} с) оплаты не было: таймер поставил EXPIRED")
    report.check(seat_state(stand.screening_id, seat) == "FREE", "место освободилось (FREE)")
    expired = wait_until(lambda: (get_payment(booking["id"]) or {}).get("status") == "EXPIRED", timeout=20)
    report.check(bool(expired), "BookingExpired дошёл до payment: платёж EXPIRED")
    status, body = pay(booking["id"], "too-late")
    report.check(status == 409, "оплата после истечения отклоняется", body.get("detail"))
    report.check(book(stand.screening_id, seat)[0] == 201, "освободившееся место можно забронировать снова")


def dead_letter_queue(stand: Stand) -> None:
    before = rabbit_queue_messages("booking.inbox.dlq")
    if before is None:
        report.check(False, "очередь booking.inbox.dlq не найдена: запущен ли booking-consumer?")
        return
    routed = rabbit_publish("catalog.events", "ScreeningPublished", "{}", "ScreeningPublished")
    report.check(routed, "битое ScreeningPublished ({}) опубликовано в catalog.events")
    arrived = wait_until(lambda: (rabbit_queue_messages("booking.inbox.dlq") or 0) > before, timeout=45, interval=1)
    report.check(bool(arrived), "после первой попытки и 5 повторов сообщение лежит в booking.inbox.dlq, очередь не застряла",
                 f"было {before}, стало {rabbit_queue_messages('booking.inbox.dlq')}")
    report.check(stand.new_booking()["status"] == "HELD", "сервис продолжает работать: новая бронь создаётся")


# ---------------------------------------------------------------- --chaos: падения посередине

def payment_consumer_down(stand: Stand) -> None:
    compose("stop", "payment-consumer")
    try:
        booking = stand.new_booking()
        time.sleep(2)
        status, body = pay(booking["id"], "early")
        report.check(status == 409, "payment-consumer лежит, payment ещё не знает о брони: 409 «повторите»",
                     body.get("detail"))
    finally:
        compose("start", "payment-consumer")
    report.check(bool(wait_payment(booking["id"])), "после старта консюмер разобрал очередь: BookingCreated не потерялся")
    status, body = pay(booking["id"], "early")
    report.check(status == 200 and body.get("status") == "SUCCEEDED", "повтор с тем же ключом проходит")
    report.check(wait_booking(booking["id"], "CONFIRMED") == "CONFIRMED", "бронь CONFIRMED")


def booking_consumer_down(stand: Stand) -> None:
    booking = stand.new_booking()
    wait_payment(booking["id"])
    compose("stop", "booking-consumer")
    try:
        status, body = pay(booking["id"], "while-booking-down")
        report.check(status == 200 and body.get("status") == "SUCCEEDED", "оплата прошла, пока booking-consumer лежит")
        time.sleep(3)
        report.check(booking_status(booking["id"]) == "HELD", "booking ещё не знает об оплате: бронь HELD")
    finally:
        compose("start", "booking-consumer")
    report.check(wait_booking(booking["id"], "CONFIRMED") == "CONFIRMED",
                 "после старта PaymentSucceeded дождался в очереди: бронь CONFIRMED")


def late_payment_seat_free(stand: Stand) -> None:
    if not stand.short_ttl():
        report.skip("поздняя оплата", stand.ttl_hint())
        return
    compose("stop", "payment-relay")
    try:
        booking = stand.new_booking()
        wait_payment(booking["id"])
        status, body = pay(booking["id"], "late-free")
        report.check(status == 200 and body.get("status") == "SUCCEEDED",
                     "деньги списаны, но payment-relay лежит: PaymentSucceeded ждёт в outbox")
        report.check(wait_booking(booking["id"], "EXPIRED", timeout=stand.expiry_wait()) == "EXPIRED",
                     "booking не узнал об оплате, таймер истёк бронь")
    finally:
        compose("start", "payment-relay")
    report.check(wait_booking(booking["id"], "CONFIRMED") == "CONFIRMED",
                 "relay поднялся, место всё ещё свободно: бронь снова CONFIRMED, деньги не пропали")
    report.check(seat_state(stand.screening_id, booking["seat_id"]) == "SOLD", "место продано")


def late_payment_seat_taken(stand: Stand) -> None:
    if not stand.short_ttl():
        report.skip("поздняя оплата, место занято", stand.ttl_hint())
        return
    compose("stop", "payment-relay")
    try:
        first = stand.new_booking()
        wait_payment(first["id"])
        pay(first["id"], "late-taken")
        wait_booking(first["id"], "EXPIRED", timeout=stand.expiry_wait())
        status, second = book(stand.screening_id, first["seat_id"])
        report.check(status == 201, "пока PaymentSucceeded не дошёл, место забронировал другой покупатель")
    finally:
        compose("start", "payment-relay")
    report.check(wait_booking(first["id"], "LATE_PAID") == "LATE_PAID",
                 "поздняя оплата первого: LATE_PAID (деньги нужно вернуть), место не продано дважды")
    report.check(booking_status(second["id"]) == "HELD", "бронь второго покупателя не тронута")


# ---------------------------------------------------------------- запуск

def services_reachable() -> bool:
    for name, url in (("catalog", CATALOG), ("booking", BOOKING), ("payment", PAYMENT)):
        try:
            http("GET", f"{url}/openapi", timeout=5)
        except urllib.error.URLError as error:
            print(f"{RED}{name} недоступен по {url}: {error.reason}{RESET}")
            print("Подними стенд: HOLD_TTL_SECONDS=10 docker compose -f deploy/docker-compose.yml up -d --wait --build")
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--chaos", action="store_true", help="останавливать сервисы посреди процесса (docker compose)")
    args = parser.parse_args()

    if not services_reachable():
        return 1

    print(f"{BOLD}Подготовка{RESET}: зал 5×8, фильм и сеанс в catalog")
    stand = prepare()

    scenario("1. Двое бронируют одно место одновременно",
             "FOR UPDATE на строке места + частичный уникальный индекс: место получает один",
             lambda: parallel_booking(stand))
    scenario("2. Повторная и параллельная оплата с одним ключом",
             "Idempotency-Key + блокировка платежа: повтор возвращает первый ответ, деньги списываются один раз",
             lambda: same_key_payment(stand))
    scenario("3. Две вкладки: параллельные оплаты одной брони с разными ключами",
             "блокировка платежа + индекс «один SUCCEEDED на платёж»: второй раз не списать",
             lambda: two_tabs(stand))
    scenario("4. Отказ карты, потом успешная оплата",
             "неудачная попытка не снимает бронь; повтор отказа идемпотентен",
             lambda: declined_then_success(stand))
    scenario("5. Оплата не прошла: место освобождается",
             "таймер истекает бронь, BookingExpired закрывает приём оплаты в payment",
             lambda: expiry_releases_seat(stand))
    scenario("6. Dead letter queue",
             "битое сообщение после лимита попыток уходит в DLQ и не блокирует очередь",
             lambda: dead_letter_queue(stand))

    if args.chaos:
        scenario("7. payment-consumer упал",
                 "BookingCreated ждёт в durable-очереди, после старта обрабатывается",
                 lambda: payment_consumer_down(stand))
        scenario("8. booking-consumer упал после оплаты",
                 "PaymentSucceeded ждёт в очереди, бронь подтверждается после старта",
                 lambda: booking_consumer_down(stand))
        scenario("9. payment-relay лежит дольше TTL, место свободно",
                 "outbox: событие не теряется; поздняя оплата подтверждает бронь, если место свободно",
                 lambda: late_payment_seat_free(stand))
        scenario("10. payment-relay лежит дольше TTL, место заняли",
                 "поздняя оплата не продаёт место второй раз: LATE_PAID, деньги к возврату",
                 lambda: late_payment_seat_taken(stand))
    else:
        print(f"\n{YELLOW}Сценарии с остановкой сервисов не запускались: добавь --chaos{RESET}")

    color = GREEN if report.failed == 0 else RED
    print(f"\n{color}{BOLD}Итого: {report.passed} PASS, {report.failed} FAIL, {report.skipped} SKIP{RESET}")
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
