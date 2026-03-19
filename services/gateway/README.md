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