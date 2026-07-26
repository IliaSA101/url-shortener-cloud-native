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
Route::post('/auth/token', [AuthController::class, 'store']);

// Наш эндпоинт для создания ссылок
Route::post('/links', [LinkController::class, 'store']);