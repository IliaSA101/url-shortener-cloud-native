from contextlib import asynccontextmanager
import json
import time
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse
from app.database import connect_db, disconnect_db
import app.database as db # Импортируем модуль, чтобы иметь доступ к db.pg_pool и db.redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код до yield выполняется перед тем, как сервер начнет принимать запросы
    await connect_db()
    yield
    # Код после yield выполняется при выключении сервера (например, по Ctrl+C)
    await disconnect_db()

app = FastAPI(title="Redirector Service", lifespan=lifespan)

@app.get("/health")
async def health_check():
    # Заодно проверим, живы ли коннекты на самом деле
    try:
        # Берем одно соединение из пула и делаем простейший запрос
        async with db.pg_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Пингуем Redis
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
        # Физический TTL = 7 дней (604800 сек). 
        # Логический TTL = 7 дней минус 5 минут (300 сек).
        logical_expire = time.time() + 604800 - 300
        
        cache_data = {
            "url": original_url,
            "logical_expire": logical_expire
        }
        # Пишем в Redis как JSON
        await db.redis_client.setex(redis_key, 604800, json.dumps(cache_data))
        
    return original_url

async def refresh_cache_task(short_code: str, redis_key: str):
    """Фоновая задача для обновления кэша (Early Expiration)."""
    lock_key = f"shortener:lock:{short_code}"
    
    # Пытаемся взять блокировку (Mutex) на 10 секунд
    # nx=True (SET IF NOT EXISTS) - ядро паттерна блокировки в Redis
    is_locked = await db.redis_client.set(lock_key, "1", nx=True, ex=10)
    
    if not is_locked:
        # Кто-то другой (соседний воркер) уже обновляет этот кэш. Просто уходим.
        return
        
    try:
        await _fetch_and_cache(short_code, redis_key)
    finally:
        # Гарантированно снимаем блокировку, даже если БД упала с ошибкой
        await db.redis_client.delete(lock_key)

@app.get("/{short_code}")
async def redirect_to_original(short_code: str, background_tasks: BackgroundTasks):
    """
    Hot Path с защитой от Cache Stampede (Mutex) и фоновым прогревом (Early Expiration).
    """
    redis_key = f"shortener:link:{short_code}"
    cached_data_str = await db.redis_client.get(redis_key)
    
    # СЦЕНАРИЙ 1: Ссылка есть в кэше
    if cached_data_str:
        try:
            cached_data = json.loads(cached_data_str)
            original_url = cached_data["url"]
            logical_expire = cached_data["logical_expire"]
        except json.JSONDecodeError:
            # TODO (Техдолг): Убрать поддержку сырых строк после обновления Laravel Gateway + отсутсвия старых ссылок в КЭШе.
            # Backward compatibility: если в кэше лежит обычная строка (старый формат от Laravel).
            original_url = cached_data_str
            logical_expire = time.time() + 604800 - 300
            
            # Сразу "лечим" кэш, перезаписывая его в новом формате в фоне
            migrated_data = {"url": original_url, "logical_expire": logical_expire}
            background_tasks.add_task(db.redis_client.setex, redis_key, 604800, json.dumps(migrated_data))

        # Если время перевалило за "логический" срок годности
        if time.time() > logical_expire:
            background_tasks.add_task(refresh_cache_task, short_code, redis_key)
            
        return RedirectResponse(url=original_url, status_code=302)
        
    # СЦЕНАРИЙ 2: Cache Miss (полное отсутствие данных)
    # Защита от "Громящего стада" (Cache Stampede)
    lock_key = f"shortener:lock:{short_code}"
    
    # Делаем несколько попыток подождать, если кто-то уже пошел в БД
    for _ in range(10): # Максимум 10 итераций по 50мс = 500мс ожидания
        is_locked = await db.redis_client.set(lock_key, "1", nx=True, ex=10)
        
        if is_locked:
            break # Мы захватили блокировку, идем в БД сами
            
        # Блокировка занята. Спим 50мс и проверяем, не обновился ли кэш соседом
        await asyncio.sleep(0.05)
        cached_data_str = await db.redis_client.get(redis_key)
        if cached_data_str:
            cached_data = json.loads(cached_data_str)
            return RedirectResponse(url=cached_data["url"], status_code=302)
            
    # Если мы вышли из цикла и у нас есть is_locked, значит БД наша
    if is_locked:
        try:
            original_url = await _fetch_and_cache(short_code, redis_key)
            if not original_url:
                raise HTTPException(status_code=404, detail="Link not found")
                
            return RedirectResponse(url=original_url, status_code=302)
        finally:
            await db.redis_client.delete(lock_key)
    else:
        # Не смогли захватить блокировку за 500мс (БД перегружена)
        # Возвращаем 503, чтобы не положить базу окончательно
        raise HTTPException(status_code=503, detail="Service Unavailable (DB Overload)")