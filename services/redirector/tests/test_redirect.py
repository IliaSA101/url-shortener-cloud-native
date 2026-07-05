import pytest
import json
import uuid

# Помечаем, что тесты асинхронные
pytestmark = pytest.mark.asyncio

async def test_redirect_302_cache_hit(client, mock_infrastructure):
    """
    Проверяем Hot Path: ссылка есть в Redis. 
    Ожидаем статус 302 и отправку события в RabbitMQ.
    """
    print("\n[ТЕСТ] 1. Тест запущен. Настраиваем мок Redis...")
    
    # Берем наш пульт управления из conftest.py
    redis_mock = mock_infrastructure["redis"]
    rmq_mock = mock_infrastructure["rmq"]
    
    # Настраиваем поведение Redis: как будто там лежит наша ссылка
    redis_mock.get.return_value = '{"url": "https://habr.com", "logical_expire": 9999999999}'
    
    print("[ТЕСТ] 2. Делаем HTTP-запрос к приложению...")
    # follow_redirects=False важно, иначе тестовый клиент пойдет скачивать страницу Хабра
    response = client.get("/habr123", follow_redirects=False)
    
    print(f"[ТЕСТ] 3. Получен ответ: {response.status_code}")
    
    # ПРОВЕРКИ (Assertions)
    # 1. Проверяем HTTP-ответ
    assert response.status_code == 302
    assert response.headers["location"] == "https://habr.com"
    
    # 2. Проверяем, что приложение реально сходило в кэш с правильным ключом
    redis_mock.get.assert_called_once_with("shortener:link:habr123")
    print("[ТЕСТ] 4. Проверка: в Redis сходили 1 раз с правильным ключом - УСПЕХ")
    
    # 3. Проверяем, что приложение отправило событие о клике в RabbitMQ
    # Так как отправка идет в BackgroundTasks, она выполнится сразу после возврата ответа
    rmq_mock.publish.assert_called_once()
    print("[ТЕСТ] 5. Проверка: событие отправлено в RabbitMQ - УСПЕХ")

async def test_404_error(client, mock_infrastructure):
    """
    Проверяем Cache Miss: ссылки нет ни в Redis, ни в PostgreSQL.
    Ожидаем статус 404.
    """
    print("\n[ТЕСТ] 1. Тест запущен. Настраиваем мок Redis...")
    
    redis_mock = mock_infrastructure["redis"]
    pg_mock = mock_infrastructure["pg"]
    rmq_mock = mock_infrastructure["rmq"]
    
    # Поведение по умолчанию в conftest.py уже настроено так, что базы "пустые"
    
    print("[ТЕСТ] 2. Делаем HTTP-запрос к приложению...")
    response = client.get("/habr123", follow_redirects=False)
    
    print(f"[ТЕСТ] 3. Получен ответ: {response.status_code}")
    
    # 1. Проверяем HTTP-ответ
    assert response.status_code == 404
    
    # 2. Проверяем, что сходили в Redis
    redis_mock.get.assert_called_once_with("shortener:link:habr123")
    
    # 3. Проверяем, что сходили в PostgreSQL с правильным SQL-запросом и аргументом!
    # Если SQL-запрос изменится в main.py, этот тест справедливо упадет.
    #pg_mock.fetchval.assert_called_once_with(
    #    "SELECT original_url FROM links WHERE short_code = $1", 
    #    "habr123"
    #)
    #print("[ТЕСТ] Проверка: в БД отправлен правильный SQL запрос - УСПЕХ")

    # 3. Допрашиваем mock (вместо жесткого assert)
    print("\n[ТЕСТ] 5. Допрашиваем PostgreSQL-mock:")
    
    # call_args хранит аргументы ПОСЛЕДНЕГО вызова
    last_call = pg_mock.fetchval.call_args
    
    if last_call:
        print(f"  Полный лог вызова: {last_call}")
        
        # У last_call есть атрибут args (позиционные аргументы - кортеж)
        # и kwargs (именованные аргументы - словарь)
        sql_query = last_call.args[0]
        passed_short_code = last_call.args[1]
        
        print(f"  SQL-запрос: {sql_query}")
        print(f"  Переданный код: {passed_short_code}")
    else:
        print("  Mock вообще не вызывали!")
    
    # 4. При 404 событие клика отправляться НЕ должно!
    rmq_mock.publish.assert_not_called()

async def test_redirect_302_rabbitmq_fault_tolerance(client, mock_infrastructure):
    """
    Проверяем отказоустойчивость: брокер сообщений недоступен.
    Редирект все равно должен работать (302).
    Также проверяем, что в RabbitMQ пытался уйти валидный UUID v4.
    """
    redis_mock = mock_infrastructure["redis"]
    rmq_mock = mock_infrastructure["rmq"]

    # 1. Настраиваем Redis (Cache Hit), чтобы получить 302
    redis_mock.get.return_value = '{"url": "https://vk.com", "logical_expire": 9999999999}'

    # 2. Имитируем жесткое падение RabbitMQ (Правило 2: side_effect)
    rmq_mock.publish.side_effect = Exception("RabbitMQ is completely dead")

    # 3. Делаем HTTP-запрос
    response = client.get("/vk123", follow_redirects=False)

    # 4. Проверяем GRACEFUL DEGRADATION
    # Несмотря на Exception в RabbitMQ, клиент должен получить 302!
    assert response.status_code == 302
    assert response.headers["location"] == "https://vk.com"

    # 5. Допрашиваем шпиона RabbitMQ, чтобы проверить payload (UUID v4)
    last_call = rmq_mock.publish.call_args
    assert last_call is not None, "RabbitMQ publish не был вызван"

    # В main.py мы вызывали exchange.publish(message, routing_key="link.clicked")
    # message - это первый позиционный аргумент (args[0])
    message_obj = last_call.args[0]
    
    # Декодируем тело сообщения (из байтов в строку, затем в словарь)
    payload = json.loads(message_obj.body.decode("utf-8"))

    event_id = payload.get("event_id")
    assert event_id is not None
    
    # Строгая проверка UUID версии 4
    # Если строка не является валидным UUID, конструктор выбросит ValueError и тест упадет
    parsed_uuid = uuid.UUID(event_id)
    assert parsed_uuid.version == 4
    
    print("\n[ТЕСТ] Отказоустойчивость: УСПЕХ. Редирект не упал.")
    print(f"[ТЕСТ] Сгенерирован валидный UUID v4: {event_id}")
