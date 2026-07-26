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

        // 2. Генерация уникального кода
        do {
            $shortCode = Str::random(6);
        } while (Link::where('short_code', $shortCode)->exists());

        // 3. Определение пользователя через гвард sanctum (опционально)
        // Если токен передан и валиден — получим модель User, иначе — null
        $user = $request->user('sanctum');

        // 4. Сохранение в PostgreSQL
        $link = Link::create([
            'short_code' => $shortCode,
            'original_url' => $originalUrl,
            'user_id' => $user ? $user->id : null, // Записываем ID, если авторизован
        ]);

        // 5. ПРОГРЕВ КЭША: Сохраняем напрямую в Redis
        // В рамках #21 мы причешем этот контракт, пока сохраняем как было
        Redis::setex("link:{$shortCode}", 604800, $originalUrl);

        // 6. Возвращаем успешный ответ
        // Получаем базовый URL редиректора (локально это порт 8001)
        $redirectorBaseUrl = env('REDIRECTOR_URL', url('/'));
        
        return response()->json([
            'short_code' => $shortCode,
            'short_url' => rtrim($redirectorBaseUrl, '/') . '/' . $shortCode,
            'original_url' => $originalUrl,
        ], 201);
    }
}