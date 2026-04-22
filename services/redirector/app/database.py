import logging
import asyncpg
import redis.asyncio as redis
from app.config import settings  # <--- Импортируем наши настройки

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pg_pool = None
redis_client = None

async def connect_db():
    global pg_pool, redis_client
    try:
        # Берем URL прямо из типизированного объекта settings!
        pg_pool = await asyncpg.create_pool(dsn=settings.postgres_url, min_size=5, max_size=20)
        logger.info("✅ Подключение к PostgreSQL установлено")

        redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        await redis_client.ping()
        logger.info("✅ Подключение к Redis установлено")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базам: {e}")
        raise e

async def disconnect_db():
    global pg_pool, redis_client
    if pg_pool:
        await pg_pool.close()
    if redis_client:
        await redis_client.close()