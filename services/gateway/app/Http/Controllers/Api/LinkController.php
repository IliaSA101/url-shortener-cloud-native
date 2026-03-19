<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Link;
use Illuminate\Http\Request;
use Illuminate\Support\Str;
use Illuminate\Support\Facades\Redis;

class LinkController extends Controller
{
    public function store(Request $request)
    {
        // 1. Валидация
        $request->validate([
            'original_url' => 'required|url|max:2048'
        ]);

        $originalUrl = $request->input('original_url');

        // 2. Генерация уникального кода (6 символов: a-z, A-Z, 0-9)
        // В Highload вероятность коллизии растет, поэтому используем цикл
        do {
            $shortCode = Str::random(6);
        } while (Link::where('short_code', $shortCode)->exists());

        // 3. Сохранение в PostgreSQL
        $link = Link::create([
            'short_code' => $shortCode,
            'original_url' => $originalUrl,
            // 'user_id' => ... (добавим, когда прикрутим Sanctum)
        ]);

        // 4. ПРОГРЕВ КЭША: Сохраняем напрямую в Redis
        // Ключ: link:{short_code}, Значение: оригинальный URL
        // Время жизни: 7 дней (604800 секунд) - опционально, чтобы не засорять память
        Redis::setex("link:{$shortCode}", 604800, $originalUrl);

        // 5. Возвращаем успешный ответ
        return response()->json([
            'short_code' => $shortCode,
            'short_url' => url('/' . $shortCode),
            'original_url' => $originalUrl,
        ], 201);
    }
}