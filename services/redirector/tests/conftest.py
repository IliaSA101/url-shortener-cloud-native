# services/redirector/tests/conftest.py

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

# Фикстура, которая переопределяет глобальные объекты базы и брокера
@pytest.fixture(autouse=True)
def mock_infrastructure():
    """
    Эта фикстура автоматически применяется ко всем тестам (autouse=True).
    Она подменяет реальные коннекты на AsyncMock перед каждым тестом,
    чтобы изолировать тесты от реальной инфраструктуры.
    """
    with patch('app.database.pg_pool', new_callable=AsyncMock) as mock_pg, \
         patch('app.database.redis_client', new_callable=AsyncMock) as mock_redis, \
         patch('app.database.rabbitmq_exchange', new_callable=AsyncMock) as mock_rmq:
        
        # Настраиваем дефолтное поведение моков
        
        # 1. По умолчанию кэш пустой (возвращает None)
        mock_redis.get.return_value = None
        # По умолчанию блокировка захватывается успешно
        mock_redis.set.return_value = True
        
        # 2. По умолчанию в БД тоже ничего нет
        # У pg_pool.acquire() хитрая структура, т.к. это асинхронный контекстный менеджер
        mock_conn = AsyncMock()
        mock_conn.fetchval.return_value = None
        mock_pg.acquire.return_value.__aenter__.return_value = mock_conn

        # Возвращаем моки в тесты, чтобы там можно было менять их поведение и проверять вызовы
        yield {
            "pg": mock_conn,
            "redis": mock_redis,
            "rmq": mock_rmq
        }

@pytest.fixture
def client():
    """
    Фикстура клиента FastAPI для выполнения HTTP-запросов.
    Использует TestClient (под капотом использует httpx).
    """
    return TestClient(app)