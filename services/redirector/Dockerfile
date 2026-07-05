# 1. Base stage: общие системные настройки
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 2. Builder stage: устанавливаем prod-зависимости (можно использовать wheels)
FROM base AS builder
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 3. Development stage: для локальной разработки (останавливаемся здесь через docker-compose)
FROM base AS development
# Копируем prod-зависимости
COPY --from=builder /install /usr/local
# Устанавливаем dev-зависимости
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
# Код не копируем, он мапится через volumes в docker-compose
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 4. Production stage: чистый и легкий образ для деплоя в K3s
FROM base AS production
COPY --from=builder /install /usr/local
# Копируем код приложения (в проде volumes нет)
COPY ./app ./app
# Запускаем без --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]