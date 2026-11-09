# ticket_booking

Бронирование мест на сеансы: три сервиса на FastAPI, общение через RabbitMQ, transactional outbox, идемпотентные консюмеры и dead letter queue.

| Сервис | Отвечает за | Порт | Swagger |
|---|---|---|---|
| catalog | площадки, залы, фильмы, сеансы; публикует сеанс в продажу | 8001 | http://localhost:8001/api/catalog/v1/docs |
| booking | места сеанса и брони: держит место, подтверждает, освобождает | 8002 | http://localhost:8002/api/booking/v1/docs |
| payment | платежи и попытки оплаты с `Idempotency-Key` | 8003 | http://localhost:8003/api/payment/v1/docs |

## Запуск

Нужны Docker с Compose v2 и, для скрипта проверки, Python 3.8+.

```bash
docker compose -f deploy/docker-compose.yml up -d --wait --build
```

Бронь держится 5 минут (`HOLD_TTL_SECONDS=300`). Чтобы проверить истечение брони, не дожидаясь 5 минут, поднимите стенд с коротким сроком:

```bash
HOLD_TTL_SECONDS=10 docker compose -f deploy/docker-compose.yml up -d --wait --build
```

Миграции применяются автоматически: API-контейнер каждого сервиса выполняет `alembic upgrade head` при старте, фоновые процессы стартуют после него.

| Что | Адрес |
|---|---|
| RabbitMQ UI | http://localhost:15672, `guest` / `guest` |
| Postgres | `localhost:5433`, `ticket` / `ticket`, базы `catalog`, `booking`, `payment` |

Остановить: `docker compose -f deploy/docker-compose.yml down` (`down -v` удалит и данные).

## Проверка основных сценариев

### Скрипт

```bash
HOLD_TTL_SECONDS=10 docker compose -f deploy/docker-compose.yml up -d --wait --build
python3 scripts/check_scenarios.py            # основные сценарии
python3 scripts/check_scenarios.py --chaos    # плюс остановка сервисов посреди процесса
```

Скрипт без зависимостей: сам создаёт зал 5×8, фильм и сеанс, ходит только в публичные API, DLQ проверяет через HTTP API RabbitMQ, сервисы останавливает через `docker compose stop/start`. Печатает `PASS`/`FAIL` по каждой проверке, код выхода 1, если что-то не прошло. При TTL больше 60 с сценарии с истечением брони пропускаются (`SKIP`).

| № | Сценарий | Ожидаемый результат |
|---|---|---|
| 1 | 20 одновременных броней одного места | одна 201, девятнадцать 409 |
| 2 | 10 одновременных оплат с одним `Idempotency-Key` | одна попытка, один ответ на всех, бронь `CONFIRMED` |
| 3 | 20 одновременных оплат одной брони с разными ключами | один успех, остальные 409, в базе один `SUCCEEDED` |
| 4 | отказ карты → повтор отказа → другая карта | `FAILED` → тот же `FAILED` → `SUCCEEDED`, бронь `CONFIRMED` |
| 5 | отказ, больше никто не платит | через TTL бронь `EXPIRED`, место свободно, платёж `EXPIRED`, оплата отклоняется |
| 6 | битое сообщение в очередь booking | после 5 повторов лежит в `booking.inbox.dlq`, сервис работает |
| 7 | `--chaos`: остановлен `payment-consumer` | `BookingCreated` дожидается в очереди, оплата проходит после старта |
| 8 | `--chaos`: остановлен `booking-consumer` после оплаты | `PaymentSucceeded` дожидается, бронь подтверждается после старта |
| 9 | `--chaos`: `payment-relay` лежит дольше TTL, место свободно | бронь истекла, после старта relay снова `CONFIRMED` |
| 10 | `--chaos`: то же, но место успели занять | первая бронь `LATE_PAID` (деньги к возврату), место не продано дважды |

### Вручную

Через Swagger или curl. Тестовые карты: `4242424242424242` проходит, карта на `0002` (например `4000000000000002`) отклоняется, `delay_seconds` имитирует медленного провайдера.

Сервисы общаются асинхронно, поэтому между шагами нужно дождаться события. Сразу после первого запуска стенда первое событие может идти до 5–6 с: консюмер ещё объявляет свою очередь, а relay держит событие в outbox и повторяет отправку.

```bash
C=http://localhost:8001/api/catalog/v1; B=http://localhost:8002/api/booking/v1; P=http://localhost:8003/api/payment/v1
id() { python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])'; }
post() { curl -s -X POST "$1" -H 'Content-Type: application/json' -d "${2:-}"; }

VENUE=$(post $C/venues '{"name":"Cinema","city":"Almaty","address":"Abay 1"}' | id)
HALL=$(post $C/halls "{\"venue_id\":\"$VENUE\",\"name\":\"Hall 1\",\"rows\":3,\"seats_per_row\":4}" | id)
SHOW=$(post $C/shows '{"title":"Dune","duration_minutes":155,"age_rating":12}' | id)
post $C/shows/$SHOW/publish
SCREENING=$(post $C/screenings "{\"show_id\":\"$SHOW\",\"hall_id\":\"$HALL\",\"starts_at\":\"2030-01-01T19:00:00+05:00\",\"price_amount\":\"2500.00\",\"price_currency\":\"KZT\"}" | id)
post $C/screenings/$SCREENING/publish

until curl -sf $B/screenings/$SCREENING/seats > /dev/null; do sleep 1; done   # ждём, пока места доедут до booking
SEAT=$(curl -s $B/screenings/$SCREENING/seats | python3 -c 'import json,sys; print(json.load(sys.stdin)[0]["seat_id"])')
BOOKING=$(post $B/bookings "{\"screening_id\":\"$SCREENING\",\"seat_id\":\"$SEAT\"}" | id)   # бронь HELD
until curl -sf $P/payments/$BOOKING > /dev/null; do sleep 1; done             # ждём, пока payment получит BookingCreated
curl -s -X POST $P/payments/$BOOKING/pay -H 'Content-Type: application/json' \
     -H 'Idempotency-Key: attempt-1' -d '{"card_number":"4242424242424242"}'   # попытка SUCCEEDED
until curl -s $B/bookings/$BOOKING | grep -q CONFIRMED; do sleep 1; done      # ждём PaymentSucceeded
curl -s $B/bookings/$BOOKING                                 # status = CONFIRMED
curl -s $P/payments/$BOOKING                                 # платёж и все попытки
```

## Архитектура

События между сервисами:

```
catalog  ──ScreeningPublished──►  booking
booking  ──BookingCreated──────►  payment
payment  ──PaymentSucceeded────►  booking
booking  ──BookingExpired──────►  payment
```

Путь события внутри сервисов:

```
отправитель:  API или таймер ──(одна транзакция с изменениями)──► таблица outbox ──► relay ──► exchange <сервис>.events
получатель:   очередь <сервис>.inbox ──► consumer ──(одна транзакция с отметкой message_id)──► своя база ──► ack
```

| Процесс | Что делает |
|---|---|
| `catalog`, `booking`, `payment` | HTTP API; бизнес-изменение и событие для других сервисов пишутся в одной транзакции (событие в таблицу `outbox`) |
| `*-relay` | раз в секунду забирает неотправленные строки `outbox` и публикует их в RabbitMQ с подтверждением брокера |
| `booking-consumer`, `payment-consumer` | читают свою очередь, обрабатывают событие в одной транзакции с отметкой `message_id`, подтверждают сообщение после commit |
| `booking-expirer` | раз в секунду переводит просроченные брони в `EXPIRED` и кладёт `BookingExpired` в `outbox` |

Один сервер Postgres, у каждого сервиса своя база (`catalog`, `booking`, `payment`); в чужую базу сервис не ходит, всё нужное получает событиями.

### События

Exchange на каждый сервис (`direct`, durable), routing key = имя события, `message_id` = `event_id`.

| Событие | Откуда → куда | Зачем |
|---|---|---|
| `ScreeningPublished` | catalog → booking | снимок сеанса: цена и все места зала; booking заводит места сеанса |
| `BookingCreated` | booking → payment | payment заводит платёж: сумма, валюта, срок брони `expires_at` |
| `PaymentSucceeded` | payment → booking | бронь оплачена: booking подтверждает её |
| `BookingExpired` | booking → payment | срок брони вышел без оплаты: payment больше не принимает оплату |

Очереди `booking.inbox` и `payment.inbox` — quorum с `x-delivery-limit: 5` и dead letter exchange (`booking.dlx`, `payment.dlx`). Сообщение, которое не обработалось ни с первой попытки, ни за 5 повторов, попадает в `booking.inbox.dlq` / `payment.inbox.dlq`.

### Жизнь брони

```
HELD ──PaymentSucceeded──► CONFIRMED
 │                            ▲
 │ срок вышел (таймер)        │ PaymentSucceeded, место ещё свободно
 ▼                            │
EXPIRED ──────────────────────┘
 │
 └──PaymentSucceeded, место уже занято──► LATE_PAID (деньги нужно вернуть)
```

#### Ключевые решения

Если оплата не прошла, место освобождается, и система не остаётся в неконсистентном состоянии. По этой части в тз я решил сделать так, что даю 5 минут на оплату, и вот если за 5 минут оплата не пройдет, то место освобождается. Так как так работают реальные сервисы. 

### Блокировки

Решил использовать в POST /bookings SELECT FOR UPDATE для блокировки. Также добавил уникальный индекс по screening_id и seat_id с условием - "WHERE status NOT IN ('EXPIRED', 'LATE_PAID')". Что бы по базе невозможно было сделать 2 активные брони для одного места. Это двойная защита, одна на уровне кода, вторая на уровне ДБ.
в POST /payments/{booking_id}/pay решил использовать idempotency_key, что бы одному ключу приходил один ответ. Также тут тоже решил использовать SELECT FOR UPDATE для блокировки по booking_id. Что бы 2 пареллельная транзация не смогла поменять данные. Также тут есть два ограничения в базе. Первое, уникальность по payment_id и idempotency_key, чтобы на один ключ была только одна попытка. Второе, частичный уникальный индекс по payment_id с условием WHERE status = 'SUCCEEDED', чтобы по одной платёжке был только один успешный платёж, даже если ключи разные.
Также публикация сеанса использует FOR UPDATE. Предположим, что два админа захотят опубликовать один сеанс. Первый нажимает опубликовать, второй тоже но позже и он ждет, и потом когда сеанс успешно опубликуется, то второй получит 409.
Также в каждом relay у меня при селекте сущности OutBox, используется skip_locked=true. Это допустим если будет несколько воркеров, что бы второй воркер не ждал пока другой воркер не разблокирует строку а шел дальше.

### Идемпотентность

Для идомпотентности оплаты решил использовать idempotency-key который должен генерится на стороне клиента. Если условно человек 2 раза отправит запрос на оплату с одним и тем же ключом, то второй запрос вернёт ту же попытку, что и первый, и деньги второй раз не спишутся. А если ключи разные, например оплатил с двух вкладок, то тут уже защищает блокировка платежа по booking_id и индекс на один SUCCEEDED, второй запрос получит 409. Также работает и с отказом, если по этому idempotency-key пришел отказ, то возвращаем тот же отказ.
Также между сервисами обеспечивает message_id. Консюмер делает INSERT ON CONFLICT DO NOTHING в processed_messages, так что повторная отправка по message_id по опредленному event_type ничего не меняет.


### Что будет, если сервис упадёт посреди процесса

Для этого я использовал transactional outbox, идемпотентность. Начнем с того, у меня всегда в одной транзакций атомарно создается сама сущность к примеру bookings и outbox. То есть создаются либо оба либо ничего не создается. Также у меня есть relay, к примеру, я создаю сущность bookings и outbox но не успеваю отправить событие, условно падает сервис. И вот для этого relay найдет строку outbox с published_at = null и отправит ее. Но также возможен кейс, что упадет relay, условно RabbitMQ подтвердил, но упадет но коммита и published_at также останется null. После перезапуска relay опять прочитает эту строку, увидит, что published_at = null и отправит событие с этим же message_id. А в свою очередь так как консюмер идемпотентен от отсеет дубль. Представим теперь такой кейс, что вдруг RabbitMQ ляжет, то у меня будут записываться логи(сюда бы по хорошему надо было добавить метрики, что бы отслеживать, но не успел). Также представим кейс, что консюмер упадет по середине, тут сразу скажу оговорочку, что я сделал ack только после коммита, что бы отдать ack только после успешного коммита. если он упадет до коммита, то ничего страшного, так как ack не уйдет, а RabbitMQ отдаст сообщение снова. если упадет после коммита но не дойдет до ack, то при новой попытке и если все будет ок, то мы отправим в ack. Если условно нам придет какой то некорректный json, то мы будем делать sleep, потом опять попытаемся и если за 5 попыток не получится, то сообщение уйдет в DLQ. Также представим кейс, что упал payment консюмер. Тогда BookingCreated просто ждёт в очереди payment.inbox и никуда не пропадает. Если человек в этот момент попробует оплатить, то получит 409 «retry later», так как payment ещё не знает про бронь. Когда консюмер поднимется, он разберёт очередь, и оплата с тем же ключом пройдёт. если консюмер лежал дольше 5 минут, то в очереди будут сразу BookingCreated и BookingExpired, и BookingExpired может обработаться раньше. Для этого, если платёж не найден, я бросаю исключение, транзакция откатывается вместе с отметкой в processed_messages, делается nack, и через секунду сообщение придёт снова, когда платёж уже создан. Теперь самый сложный кейс, условно человек оплатил, но упал relay микросервиса payments, и PaymentSucceeded завис в outbox. Через 5 минут таймер ставит брони EXPIRED. Когда relay поднимется и событие дойдёт до booking, я проверяю место: если оно свободно, бронь снова CONFIRMED, а если его уже занял другой, ставлю LATE_PAID и пишу в лог, что деньги надо вернуть. Сам возврат к сожалению не успел сделать. Если payment упадёт посреди оплаты до коммита, то не запишется ни попытка, ни событие, потому что всё в одной транзакции. Клиент повторит запрос с тем же idempotency-key, и оплата выполнится заново. С реальным провайдером тут нужна была бы сверка, но у меня заглушка

## Структура

```
deploy/
  docker-compose.yml        весь стенд одной командой
  init-databases.sql        базы catalog, booking, payment
scripts/
  check_scenarios.py        проверка сценариев
services/
  catalog-service/          domain, application, infrastructure, presentation
  booking-service/          routers, schemas, services, repositories, infrastructure (db, rabbitmq), workers
  payment-service/          routers, schemas, services, repositories, infrastructure (db, rabbitmq, заглушка провайдера)
```

## P.S К сожалению, не успел выкатить проект на облако или добавить метрику
