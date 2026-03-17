# Используем официальный образ PHP-FPM
FROM php:8.5-fpm

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpng-dev \
    libonig-dev \
    libxml2-dev \
    zip \
    unzip \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Устанавливаем PHP-расширения для Laravel и PostgreSQL
RUN docker-php-ext-install pdo_pgsql mbstring exif pcntl bcmath gd

# Устанавливаем и включаем расширение для Redis
RUN pecl install redis && docker-php-ext-enable redis

# Копируем Composer из официального образа
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /var/www/html

# Даем права доступа (опционально для локальной разработки)
RUN chown -R www-data:www-data /var/www/html
