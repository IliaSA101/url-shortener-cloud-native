# API Gateway (Laravel)

Этот микросервис отвечает за обработку входящего HTTP-трафика, создание коротких ссылок и маршрутизацию.

## 🛠 Локальная настройка для разработки

### 1. Настройка окружения
Скопируйте файл `.env.example` в `.env` и укажите доступы к базе данных. 
В Docker-окружении хостом выступает имя сервиса `postgres`:

```env
DB_CONNECTION=pgsql
DB_HOST=postgres
DB_PORT=5432
DB_DATABASE=shortener
DB_USERNAME=root
DB_PASSWORD=root
```

### 2. Работа с базой данных (Миграции)
Все artisan-команды необходимо выполнять внутри контейнера `gateway`.

**Создание новых миграций:**
```bash
docker compose exec gateway php artisan make:migration create_links_table
docker compose exec gateway php artisan make:migration create_click_stats_table
```

**Применение миграций:**
```bash
docker compose exec gateway php artisan migrate
```

### 3. Настройка Redis (Кэширование)
Для предотвращения коллизий ключей в Redis (если на сервере запущено несколько проектов), мы жестко переопределяем префикс приложения. 

Добавьте в ваш `.env` файл:
```env
REDIS_PREFIX="shortener:"
```
После изменения конфигурации не забудьте сбросить кэш: `docker compose exec gateway php artisan config:clear`.

---

## 📖 API Reference

### 1. Создание короткой ссылки
Генерирует уникальный короткий код и сразу прогревает кэш в Redis.

* **Эндпоинт:** `POST /api/links`
* **Headers:** `Accept: application/json`

**Request Body:**
```json
{
    "original_url": "https://habr.com/ru/articles/123456/"
}
```

**Response (201 Created):**
```json
{
    "short_code": "jMWRD6",
    "short_url": "http://localhost:8000/jMWRD6",
    "original_url": "https://habr.com/ru/articles/123456/"
}
```

### 2. Использование (Редирект)
* **Эндпоинт:** `GET /{short_code}` (например, `http://localhost:8000/jMWRD6`)
* **Логика:** Сервис использует паттерн Cache-Aside. Сначала выполняется попытка чтения (Hot Path) из Redis. При cache miss (промахе) данные достаются из PostgreSQL, кэш восстанавливается, и выполняется `302 Found` редирект.