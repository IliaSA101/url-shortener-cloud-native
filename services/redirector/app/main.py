# services/redirector/app/main.py

import json
import time
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import RedirectResponse

from app.database import connect_db, disconnect_db
import app.database as db

# Инициализируем логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код до yield выполняется перед тем, как сервер начнет принимать запросы
    await connect_db()
    yield
    # Код после yield выполняется при выключении сервера
    await disconnect_db()

app = FastAPI(title="Redirector Service", lifespan=lifespan)

@app.get("/health")
async def health_check():
    try:
        async with db.pg_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        await db.redis_client.ping()
        return {"status": "ok", "postgres": "connected", "redis": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

async def _fetch_and_cache(short_code: str, redis_key: str) -> str | None:
    """Вспомогательная функция: сходить в БД и обновить кэш."""
    async with db.pg_pool.acquire() as conn:
        query = "SELECT original_url FROM links WHERE short_code = $1"
        original_url = await conn.fetchval(query, short_code)
        
    if original_url:
        logical_expire = time.time() + 604800 - 300
        cache_data = {
            "url": original_url,
            "logical_expire": logical_expire
        }
        await db.redis_client.setex(redis_key, 604800, json.dumps(cache_data))
        
    return original_url

async def refresh_cache_task(short_code: str, redis_key: str):
    """Фоновая задача для обновления кэша (Early Expiration)."""
    lock_key = f"shortener:lock:{short_code}"
    is_locked = await db.redis_client.set(lock_key, "1", nx=True, ex=10)
    
    if not is_locked:
        return
        
    try:
        await _fetch_and_cache(short_code, redis_key)
    finally:
        await db.redis_client.delete(lock_key)

async def publish_click_event(short_code: str, request: Request):
    """Фоновая задача отправки события в RabbitMQ."""
    if not db.rabbitmq_exchange:
        logger.error("RabbitMQ Exchange не инициализирован, событие потеряно.")
        return

    event_id = str(uuid.uuid4())
    ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "")

    payload = {
        "event_id": event_id,
        "short_code": short_code,
        "clicked_at": datetime.now(timezone.utc).isoformat(),
        "ip": ip,
        "user_agent": request.headers.get("user-agent", ""),
        "referer": request.headers.get("referer", "")
    }

    message = aio_pika.Message(
        body=json.dumps(payload).encode("utf-8"),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        message_id=event_id,
    )

    try:
        await db.rabbitmq_exchange.publish(
            message,
            routing_key="link.clicked"
        )
        logger.info(f"Событие {event_id} для {short_code} отправлено в RabbitMQ")
    except Exception as e:
        logger.error(f"Ошибка публикации события {event_id} в RabbitMQ: {e}")

@app.get("/{short_code}")
async def redirect_to_original(short_code: str, request: Request, background_tasks: BackgroundTasks):
    """Hot Path с защитой от Cache Stampede и фоновым прогревом."""
    redis_key = f"shortener:link:{short_code}"
    cached_data_str = await db.redis_client.get(redis_key)
    
    original_url = None
    
    # СЦЕНАРИЙ 1: Ссылка есть в кэше
    if cached_data_str:
        try:
            cached_data = json.loads(cached_data_str)
            original_url = cached_data["url"]
            logical_expire = cached_data["logical_expire"]
        except json.JSONDecodeError:
            # Backward compatibility (старый формат от Laravel)
            original_url = cached_data_str
            logical_expire = time.time() + 604800 - 300
            migrated_data = {"url": original_url, "logical_expire": logical_expire}
            background_tasks.add_task(db.redis_client.setex, redis_key, 604800, json.dumps(migrated_data))

        # Если время перевалило за "логический" срок годности
        if time.time() > logical_expire:
            background_tasks.add_task(refresh_cache_task, short_code, redis_key)
            
    # СЦЕНАРИЙ 2: Cache Miss (полное отсутствие данных)
    else:
        lock_key = f"shortener:lock:{short_code}"
        is_locked = False
        
        for _ in range(10): # Ждем максимум 500мс
            is_locked = await db.redis_client.set(lock_key, "1", nx=True, ex=10)
            if is_locked:
                break
                
            await asyncio.sleep(0.05)
            cached_data_str = await db.redis_client.get(redis_key)
            if cached_data_str:
                try:
                    cached_data = json.loads(cached_data_str)
                    original_url = cached_data["url"]
                except json.JSONDecodeError:
                    original_url = cached_data_str
                break
                
        # Если мы вышли из цикла и БД наша
        if is_locked:
            try:
                original_url = await _fetch_and_cache(short_code, redis_key)
            finally:
                await db.redis_client.delete(lock_key)
        elif not original_url:
            raise HTTPException(status_code=503, detail="Service Unavailable (DB Overload)")

    # Финальная проверка: если URL так и не найден (в БД его нет)
    if not original_url:
        raise HTTPException(status_code=404, detail="Link not found")

    # ЕДИНАЯ ТОЧКА ВЫХОДА
    background_tasks.add_task(publish_click_event, short_code, request)
    return RedirectResponse(url=original_url, status_code=302)