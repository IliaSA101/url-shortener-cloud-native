<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\LinkController;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

// Стандартный тестовый роут Laravel Sanctum
Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');

// Эндпоинт выдачи токена (Login)
// Навешиваем защиту от брутфорса паролей (5 попыток в минуту)
Route::post('/auth/token', [AuthController::class, 'store'])
    ->middleware('throttle:auth-token');

// Наш эндпоинт для создания ссылок
// Защищаем жестким лимитом (10 в минуту на юзера/IP)
Route::post('/links', [LinkController::class, 'store'])
    ->middleware('throttle:link-create');