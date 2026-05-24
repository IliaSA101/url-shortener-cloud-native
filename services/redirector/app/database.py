# services/redirector/app/database.py
import logging
import asyncpg
import redis.asyncio as redis
import aio_pika
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pg_pool = None
redis_client = None
rabbitmq_conn = None
rabbitmq_channel = None
rabbitmq_exchange = None

async def connect_db():
    global pg_pool, redis_client, rabbitmq_conn, rabbitmq_channel, rabbitmq_exchange
    try:
        pg_pool = await asyncpg.create_pool(dsn=settings.postgres_url, min_size=5, max_size=20)
        logger.info("✅ Подключение к PostgreSQL установлено")

        redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        await redis_client.ping()
        logger.info("✅ Подключение к Redis установлено")

        # --- НОВЫЙ БЛОК RABBITMQ ---
        # Используем connect_robust для защиты от сетевых сбоев
        rabbitmq_conn = await aio_pika.connect_robust(settings.rabbitmq_url)
        # Канал (Channel) - это виртуальное соединение внутри TCP-соединения
        rabbitmq_channel = await rabbitmq_conn.channel()
        
        # Декларируем Exchange (Обменник) типа Topic.
        # durable=True означает, что обменник выживет при перезагрузке RabbitMQ.
        rabbitmq_exchange = await rabbitmq_channel.declare_exchange(
            name="links.exchange",
            type=aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        logger.info("✅ Подключение к RabbitMQ установлено (links.exchange готов)")
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базам/брокеру: {e}")
        raise e

async def disconnect_db():
    global pg_pool, redis_client, rabbitmq_conn
    if pg_pool:
        await pg_pool.close()
    if redis_client:
        await redis_client.close()
    if rabbitmq_conn:
        await rabbitmq_conn.close()