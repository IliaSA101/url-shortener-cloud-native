from contextlib import asynccontextmanager
from fastapi import FastAPI
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