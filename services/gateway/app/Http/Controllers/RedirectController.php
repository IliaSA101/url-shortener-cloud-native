<?php

namespace App\Http\Controllers;

use App\Models\Link;
use Illuminate\Support\Facades\Redis;

class RedirectController extends Controller
{
    public function redirect(string $code)
    {
        // 1. FAST PATH: Пытаемся достать URL из сверхбыстрого Redis
        $url = Redis::get("link:{$code}");

        // 2. FALLBACK: Если в Redis пусто (кэш протух или Redis перезагружался)
        if (!$url) {
            // Ищем в PostgreSQL. Если не найдем — Laravel сам выкинет 404 ошибку
            $link = Link::where('short_code', $code)->firstOrFail();
            $url = $link->original_url;

            // Восстанавливаем кэш в Redis на 7 дней
            Redis::setex("link:{$code}", 604800, $url);
        }

        // 3. TODO: Здесь будет отправка события о клике в RabbitMQ для аналитики
        // (Реализуем в следующей задаче)

        // 4. Выполняем 302 редирект на оригинальный URL
        return redirect()->away($url);
    }
}